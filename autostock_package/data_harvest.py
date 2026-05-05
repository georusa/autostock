#!/usr/bin/env python3
"""
DataHarvest - 通用数据采集与处理工具包
支持网页内容提取、文件处理、格式转换、批量处理
"""
import os, sys, json, csv, re
from pathlib import Path
from datetime import datetime
import argparse
import httpx
from bs4 import BeautifulSoup

class DataHarvester:
    """通用数据采集器"""
    
    @staticmethod
    def fetch_url(url, output=None):
        """获取网页内容并提取正文"""
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        r.encoding = r.charset_encoding or 'utf-8'
        
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        
        result = {
            'url': str(r.url),
            'status': r.status_code,
            'title': soup.title.string if soup.title else '',
            'text_length': len(text),
            'text': text[:50000],
        }
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存到 {output}")
        
        return result
    
    @staticmethod
    def extract_links(url, output=None):
        """提取页面所有链接"""
        headers = {"User-Agent": "Mozilla/5.0"}
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if href.startswith('http') or href.startswith('/'):
                links.append({'text': text[:100], 'href': href})
        
        result = {'source': url, 'total': len(links), 'links': links}
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result
    
    @staticmethod
    def csv_to_json(input_file, output=None):
        """CSV 转 JSON"""
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    
    @staticmethod
    def batch_fetch(urls, output_dir="output"):
        """批量获取多个URL"""
        os.makedirs(output_dir, exist_ok=True)
        results = []
        for i, url in enumerate(urls):
            try:
                result = DataHarvester.fetch_url(url)
                results.append(result)
                print(f"  [{i+1}/{len(urls)}] {url[:50]}... OK")
            except Exception as e:
                print(f"  [{i+1}/{len(urls)}] {url[:50]}... 失败: {e}")
        
        summary = {"total": len(results), "success": sum(1 for r in results if r), "results": results}
        outpath = os.path.join(output_dir, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ 批量采集完成，结果保存到 {outpath}")
        return results
    
    @staticmethod
    def extract_tables(url, output=None):
        """从网页提取表格数据"""
        headers = {"User-Agent": "Mozilla/5.0"}
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tables = []
        for i, table in enumerate(soup.find_all('table')):
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for cell in tr.find_all(['td', 'th']):
                    cells.append(cell.get_text(strip=True))
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({'table_index': i, 'rows': len(rows), 'columns': len(rows[0]) if rows else 0, 'data': rows})
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(tables, f, ensure_ascii=False, indent=2)
        return tables


def main():
    parser = argparse.ArgumentParser(description="DataHarvest - 通用数据采集与处理工具")
    sub = parser.add_subparsers(dest="command")
    
    # fetch
    f = sub.add_parser("fetch", help="获取网页内容")
    f.add_argument("url", help="目标URL")
    f.add_argument("-o", "--output", help="输出文件路径")
    
    # links
    l = sub.add_parser("links", help="提取页面链接")
    l.add_argument("url", help="目标URL")
    l.add_argument("-o", "--output", help="输出文件路径")
    
    # tables
    t = sub.add_parser("tables", help="提取表格")
    t.add_argument("url", help="目标URL")
    t.add_argument("-o", "--output", help="输出文件路径")
    
    # csv2json
    c = sub.add_parser("csv2json", help="CSV转JSON")
    c.add_argument("input", help="输入的CSV文件")
    c.add_argument("-o", "--output", help="输出JSON文件路径")
    
    # batch
    b = sub.add_parser("batch", help="批量采集")
    b.add_argument("file", help="包含URL列表的文件(每行一个)")
    b.add_argument("-o", "--output", help="输出目录")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        DataHarvester.fetch_url(args.url, args.output)
    elif args.command == "links":
        DataHarvester.extract_links(args.url, args.output)
    elif args.command == "tables":
        DataHarvester.extract_tables(args.url, args.output)
    elif args.command == "csv2json":
        DataHarvester.csv_to_json(args.input, args.output)
    elif args.command == "batch":
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        DataHarvester.batch_fetch(urls, args.output or "output")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
