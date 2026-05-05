#!/usr/bin/env python3
"""
StockDashboard - 实时A股行情仪表盘生成器
一键生成带所有数据的HTML仪表盘
比同花顺/东方财富客户端更轻量、更定制化
"""
import os, json, requests, hashlib, math
from datetime import datetime
import numpy as np

class StockDashboard:
    """A股仪表盘生成器"""
    
    EASTMONEY_URL = "https://push2.eastmoney.com/api/qt/stock/get"
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_realtime_quote(self, stock_code):
        """获取实时行情"""
        sec_code = f"1.{stock_code}" if stock_code.startswith("6") else f"0.{stock_code}"
        params = {
            "secid": f"0.{stock_code}" if not stock_code.startswith("6") else f"1.{stock_code}",
            "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f59,f60,f116,f117,f162,f167,f168,f169,f170,f171",
        }
        try:
            resp = requests.get(self.EASTMONEY_URL, params=params, timeout=5).json()
            d = resp.get("data", {})
            return {
                "name": f"股票{stock_code}",
                "code": stock_code,
                "price": d.get("f43", 0) / 100,
                "high": d.get("f44", 0) / 100,
                "low": d.get("f45", 0) / 100,
                "open": d.get("f46", 0) / 100,
                "volume": d.get("f47", 0),
                "amount": d.get("f48", 0),
                "change_pct": round(d.get("f170", 0) / 100, 2) if d.get("f170") else 0,
            }
        except:
            return None
    
    def get_kline_data(self, stock_code, days=60):
        """获取K线数据用于生成图表"""
        market = "1" if stock_code.startswith("6") else "0"
        params = {
            "secid": f"{market}.{stock_code}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # 日K
            "fqt": "1",    # 前复权
            "beg": "0",
            "end": "20500101",
            "lmt": days,
        }
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            klines = data.get("data", {}).get("klines", [])
            return klines
        except:
            return []
    
    def generate_dashboard(self, stock_codes):
        """生成HTML仪表盘"""
        quotes = []
        for code in stock_codes:
            q = self.get_realtime_quote(code)
            if q:
                quotes.append(q)
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 构建仪表盘
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股实时仪表盘 - AutoStock</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0f0f1a; color:#e0e0e0; padding:20px; }}
.header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }}
.header h1 {{ font-size:24px; color:#fff; }}
.header .time {{ color:#888; font-size:14px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; margin-bottom:20px; }}
.card {{ background:#1a1a2e; border-radius:12px; padding:20px; border:1px solid #2a2a4a; }}
.card h3 {{ font-size:14px; color:#888; margin-bottom:8px; }}
.price {{ font-size:32px; font-weight:700; margin:8px 0; }}
.price.up {{ color:#00c853; }}
.price.down {{ color:#ff1744; }}
.change {{ font-size:14px; }}
.change.up {{ color:#00c853; }}
.change.down {{ color:#ff1744; }}
.detail {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; font-size:12px; color:#888; }}
.detail span {{ display:flex; justify-content:space-between; }}
.detail span b {{ color:#ccc; }}
.chart-card {{ background:#1a1a2e; border-radius:12px; padding:20px; border:1px solid #2a2a4a; margin-bottom:20px; }}
.actions {{ display:flex; gap:10px; margin-top:20px; }}
.btn {{ padding:10px 20px; border-radius:8px; border:none; cursor:pointer; font-size:14px; }}
.btn-primary {{ background:#4a6cf7; color:#fff; }}
.btn-secondary {{ background:#2a2a4a; color:#888; }}
.footer {{ text-align:center; margin-top:30px; padding:20px; color:#555; font-size:12px; }}
</style>
</head>
<body>

<div class="header">
    <h1>📊 A股实时仪表盘</h1>
    <div class="time">更新: {now}</div>
</div>

<div class="grid">
"""
        for q in quotes:
            up = q.get("change_pct", 0) >= 0
            cls = "up" if up else "down"
            html += f"""
    <div class="card">
        <h3>{q['code']}</h3>
        <div class="price {cls}">¥{q['price']:.2f}</div>
        <div class="change {cls}">{'+' if up else ''}{q['change_pct']:.2f}%</div>
        <div class="detail">
            <span>开盘 <b>¥{q['open']:.2f}</b></span>
            <span>最高 <b>¥{q['high']:.2f}</b></span>
            <span>最低 <b>¥{q['low']:.2f}</b></span>
            <span>成交量 <b>{q.get('volume',0):,}</b></span>
        </div>
    </div>
"""
        
        html += """
</div>

<div class="actions">
    <button class="btn btn-primary" onclick="location.reload()">🔄 刷新</button>
</div>

<div class="footer">
    🦞 AutoStock by Claw — 数据来源：东方财富 | 仅供学习参考<br>
    购买完整版工具：PayPal netmstar@gmail.com | 支付宝 pkuzxx@gmail.com
</div>

</body>
</html>"""
        
        fname = f"dashboard_{datetime.now().strftime('%H%M%S')}.html"
        fpath = os.path.join(self.output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"✅ 仪表盘已生成: {fpath}")
        return fpath


if __name__ == "__main__":
    import sys
    d = StockDashboard()
    
    # 默认监控8只热门A股
    stocks = ["600519","000858","300750","601318","000333",
              "002594","600036","000858","002415","600276"]
    
    if len(sys.argv) > 1:
        stocks = sys.argv[1:]
    
    output = d.generate_dashboard(stocks)
    print(f"\n📊 仪表盘包含 {len(stocks)} 只股票")
    print(f"💡 浏览器打开查看: {output}")
