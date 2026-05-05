#!/usr/bin/env python3
"""
Excel 自动处理工具套件
批量处理 Excel 文件 - 合并、清洗、转换、生成报表

功能:
  merge     - 合并多个 Excel
  clean     - 清洗数据 (去重/填充/格式化)
  stats     - 生成统计报表
  convert   - 格式转换
  split     - 按条件拆分

定价: ¥39.9 / $4.99 (完整版)
     ¥19.9 / $2.99 (基础版，当前版本)

购买: paypal.me/georusa
"""
import os, sys, csv, json
from datetime import datetime

def merge_files(files, output="merged_output.xlsx"):
    """合并多个 CSV/Excel 文件"""
    if not files:
        print("❌ 请指定要合并的文件")
        return
    try:
        import pandas as pd
        dfs = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.csv',):
                df = pd.read_csv(f)
            elif ext in ('.xls', '.xlsx'):
                df = pd.read_excel(f)
            else:
                continue
            df['_source'] = os.path.basename(f)
            dfs.append(df)
            print(f"  + {f}: {len(df)} 行")
        
        result = pd.concat(dfs, ignore_index=True)
        result.to_excel(output, index=False)
        print(f"✅ 合并完成: {len(result)} 行 → {output}")
    except ImportError:
        print("❌ 需要 pandas: pip3 install pandas openpyxl")

def clean_file(input_file, output=None):
    """清洗数据"""
    if not output:
        name, ext = os.path.splitext(input_file)
        output = f"{name}_cleaned{ext}"
    try:
        import pandas as pd
        ext = os.path.splitext(input_file)[1].lower()
        df = pd.read_excel(input_file) if ext in ('.xls','.xlsx') else pd.read_csv(input_file)
        
        before = len(df)
        df = df.drop_duplicates()
        df = df.dropna(how='all')
        print(f"  去重: {before} → {len(df)} 行")
        
        df.to_excel(output, index=False)
        print(f"✅ 清洗完成 → {output}")
    except ImportError:
        print("❌ 需要 pandas")

def generate_stats(input_file, output="stats_report.xlsx"):
    """生成统计数据"""
    try:
        import pandas as pd
        ext = os.path.splitext(input_file)[1].lower()
        df = pd.read_excel(input_file) if ext in ('.xls','.xlsx') else pd.read_csv(input_file)
        
        stats = df.describe()
        stats.to_excel(output)
        print(f"✅ 统计报表 → {output}")
        print(f"  列数: {len(df.columns)}")
        print(f"  行数: {len(df)}")
    except ImportError:
        print("❌ 需要 pandas")

def main():
    print("📊 Excel 自动处理工具")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 excel_auto.py merge file1.xlsx file2.xlsx")
        print("  python3 excel_auto.py clean messy_data.xlsx")
        print("  python3 excel_auto.py stats sales_data.xlsx")
        print()
        print("💰 完整版: paypal.me/georusa")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "merge":
        files = sys.argv[2:]
        merge_files(files)
    elif cmd == "clean":
        if len(sys.argv) < 3:
            print("❌ 请指定文件")
            sys.exit(1)
        clean_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "stats":
        if len(sys.argv) < 3:
            print("❌ 请指定文件")
            sys.exit(1)
        generate_stats(sys.argv[2])
    elif cmd == "install":
        print("安装依赖: pandas, openpyxl")
        print("  pip3 install pandas openpyxl")
    else:
        print(f"❌ 未知命令: {cmd}")
        print("💡 完整版含更多功能: paypal.me/georusa")

if __name__ == "__main__":
    main()
