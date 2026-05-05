#!/usr/bin/env python3
"""
微博热搜趋势采集工具 - Weibo Hot Search Trend Scraper v1.0
=============================================================
特性：
- 自动爬取微博热搜榜（无需登录）
- 支持趋势追踪（对比历史数据）
- 导出 CSV / JSON / Excel
- 关键词预警通知
- 轻量级，单文件，无外部认证依赖

适用：自媒体运营、舆情监控、热点追踪
售价: ¥19.9 / $2.99
作者: George USA (github.com/georusa)
"""

import json
import csv
import os
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import requests
except ImportError:
    print("[!] 请先安装: pip install requests")
    exit(1)

try:
    from openpyxl import Workbook
    HAS_EXCEL = True
except ImportError:
    HAS_EXCEL = False

# ─── 配置 ─────────────────────────────────────────────────
CONFIG = {
    "hot_search_api": "https://weibo.com/ajax/side/hotSearch",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "output_dir": "output",
    "history_file": "history.json",
    "poll_interval": 300,  # 5分钟轮询一次
    "alert_keywords": [],  # 示例: ["股票", "A股", "地震"]
}


@dataclass
class HotItem:
    rank: int
    word: str
    hot_value: int
    category: str = ""
    url: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class WeiboHotScraper:
    """微博热搜采集器"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or CONFIG
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config["user_agent"],
            "Referer": "https://weibo.com/",
        })
        self.output_dir = Path(self.config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)
        self.history_path = self.output_dir / self.config["history_file"]
        self._load_history()

    def _load_history(self):
        if self.history_path.exists():
            with open(self.history_path, "r", encoding="utf-8") as f:
                self.history: List[dict] = json.load(f)
        else:
            self.history = []

    def _save_history(self):
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def fetch(self) -> List[HotItem]:
        """获取当前热搜榜"""
        resp = self.session.get(self.config["hot_search_api"], timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = []
        realtime = data.get("data", {}).get("realtime", [])
        now = datetime.now().isoformat()

        for i, entry in enumerate(realtime, 1):
            word = entry.get("word", "")
            hot = entry.get("raw_hot", entry.get("num", 0))
            category = entry.get("category", "")
            item = HotItem(
                rank=i,
                word=word,
                hot_value=hot,
                category=category,
                timestamp=now,
            )
            items.append(item)

        return items

    def save_json(self, items: List[HotItem]) -> str:
        """保存为 JSON"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"hot_trend_{ts}.json"
        data = [item.to_dict() for item in items]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(path)

    def save_csv(self, items: List[HotItem]) -> str:
        """保存为 CSV"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"hot_trend_{ts}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["rank", "word", "hot_value", "category", "timestamp"])
            writer.writeheader()
            for item in items:
                writer.writerow(item.to_dict())
        return str(path)

    def save_excel(self, items: List[HotItem]) -> Optional[str]:
        """保存为 Excel"""
        if not HAS_EXCEL:
            return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"hot_trend_{ts}.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "热搜榜"
        ws.append(["排名", "关键词", "热度值", "分类", "时间"])
        for item in items:
            ws.append([item.rank, item.word, item.hot_value, item.category, item.timestamp])
        wb.save(str(path))
        return str(path)

    def save_all(self, items: List[HotItem]) -> Dict[str, Optional[str]]:
        """保存所有格式"""
        return {
            "json": self.save_json(items),
            "csv": self.save_csv(items),
            "excel": self.save_excel(items),
        }

    def track_trend(self, hours: int = 24) -> List[dict]:
        """分析趋势变化"""
        cutoff = time.time() - hours * 3600
        recent = [h for h in self.history
                  if datetime.fromisoformat(h["snapshot_time"]).timestamp() > cutoff]

        # 统计出现频率
        word_count = {}
        for snapshot in recent:
            for item in snapshot["items"]:
                word = item["word"]
                if word not in word_count:
                    word_count[word] = {"count": 0, "max_rank": 99, "entries": []}
                word_count[word]["count"] += 1
                word_count[word]["max_rank"] = min(word_count[word]["max_rank"], item["rank"])
                word_count[word]["entries"].append({
                    "rank": item["rank"],
                    "hot_value": item["hot_value"],
                    "time": item["timestamp"],
                })

        trends = []
        for word, data in sorted(word_count.items(),
                                 key=lambda x: x[1]["count"], reverse=True)[:50]:
            trends.append({
                "word": word,
                "appearances": data["count"],
                "best_rank": data["max_rank"],
                "entries": data["entries"][-10:],
            })

        return trends

    def run_once(self):
        """单次采集"""
        items = self.fetch()
        paths = self.save_all(items)

        # 加入历史
        snapshot = {
            "snapshot_time": datetime.now().isoformat(),
            "items": [item.to_dict() for item in items],
        }
        self.history.append(snapshot)
        self._save_history()

        print(f"[✓] 采集完成 | {len(items)} 条热搜")
        for fmt, path in paths.items():
            if path:
                print(f"  → {fmt}: {path}")

        # 关键词预警
        if self.config["alert_keywords"]:
            matched = [i.word for i in items
                       if any(kw in i.word for kw in self.config["alert_keywords"])]
            if matched:
                print(f"\n[!] 预警关键词命中: {', '.join(matched)}")

        return items, paths

    def poll_loop(self, count: int = 0):
        """持续轮询采集"""
        n = 0
        while count == 0 or n < count:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 采集 #{n+1}")
            try:
                self.run_once()
            except Exception as e:
                print(f"[✗] 采集失败: {e}")
            n += 1
            if count == 0 or n < count:
                time.sleep(self.config["poll_interval"])

    def export_trend_report(self, hours: int = 24) -> str:
        """导出趋势报告"""
        trends = self.track_trend(hours)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"trend_report_{ts}.json"
        report = {
            "report_time": datetime.now().isoformat(),
            "analysis_window_hours": hours,
            "total_snapshots": len(self.history),
            "top_trends": trends[:30],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return str(path)


# ─── CLI ─────────────────────────────────────────────────
def cli():
    import argparse
    parser = argparse.ArgumentParser(
        description="微博热搜趋势采集工具 v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --once
  %(prog)s --poll --count 12          # 采集12次（每5分钟）
  %(prog)s --trend --hours 48          # 分析48小时趋势
  %(prog)s --alert "A股,股票,地震"      # 设置预警关键词
        """,
    )
    parser.add_argument("--once", action="store_true", help="单次采集")
    parser.add_argument("--poll", action="store_true", help="持续轮询")
    parser.add_argument("--count", type=int, default=0, help="轮询次数（0=无限）")
    parser.add_argument("--trend", action="store_true", help="导出趋势报告")
    parser.add_argument("--hours", type=int, default=24, help="趋势分析时间窗口（小时）")
    parser.add_argument("--alert", type=str, help="预警关键词（逗号分隔）")
    parser.add_argument("--format", choices=["json", "csv", "excel"], default="json",
                        help="导出格式")
    args = parser.parse_args()

    config = dict(CONFIG)
    if args.alert:
        config["alert_keywords"] = [k.strip() for k in args.alert.split(",")]

    scraper = WeiboHotScraper(config)

    if args.once:
        scraper.run_once()
    elif args.poll:
        scraper.poll_loop(args.count)
    elif args.trend:
        report_path = scraper.export_trend_report(args.hours)
        print(f"[✓] 趋势报告已导出: {report_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
