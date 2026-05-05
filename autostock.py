#!/usr/bin/env python3
"""
AutoStock - A股自动化分析工具
一键抓取 -> 计算指标 -> 生成报告
"""

import argparse
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False
import base64
from io import BytesIO
import httpx

# ── 股票列表 ──
STOCKS = {
    "600519": "贵州茅台", "000858": "五粮液", "002415": "海康威视",
    "300750": "宁德时代", "000333": "美的集团", "601318": "中国平安",
    "600036": "招商银行", "000002": "万科A",
}

def fetch_data(code):
    """从东方财富获取股票日线"""
    # 转换代码
    if code.endswith(".SZ"):
        secid = f"0.{code.replace('.SZ', '')}"
    elif code.endswith(".SH"):
        secid = f"1.{code.replace('.SH', '')}"
    elif code.startswith("0") or code.startswith("3"):
        secid = f"0.{code}"
    else:
        secid = f"1.{code}"
    
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=101&fqt=1&end=20500101&lmt=200"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    }
    resp = httpx.get(url, headers=headers, timeout=15)
    data = resp.json()
    klines = data.get("data", {}).get("klines", [])
    if not klines:
        return None
    rows = []
    for line in klines:
        parts = line.split(",")
        rows.append({
            "日期": parts[0], "开盘": float(parts[1]), "收盘": float(parts[2]),
            "最高": float(parts[3]), "最低": float(parts[4]),
            "成交量": float(parts[5]), "成交额": float(parts[6]),
        })
    df = pd.DataFrame(rows)
    df["日期"] = pd.to_datetime(df["日期"])
    return df.sort_values("日期").reset_index(drop=True)


def calc_indicators(df):
    """计算技术指标"""
    df = df.copy()
    # MA
    for n in [5, 10, 20, 60]:
        df[f"MA{n}"] = df["收盘"].rolling(n).mean()
    # RSI
    delta = df["收盘"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    # MACD
    ema12 = df["收盘"].ewm(span=12).mean()
    ema26 = df["收盘"].ewm(span=26).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])
    # 信号
    signals = []
    for i in range(1, len(df)):
        if df["MACD"].iloc[i] > 0 and df["MACD"].iloc[i-1] <= 0:
            signals.append(("金叉", df["日期"].iloc[i], df["收盘"].iloc[i]))
        elif df["MACD"].iloc[i] < 0 and df["MACD"].iloc[i-1] >= 0:
            signals.append(("死叉", df["日期"].iloc[i], df["收盘"].iloc[i]))
        if df["RSI"].iloc[i] < 30 and df["RSI"].iloc[i] > df["RSI"].iloc[i-1]:
            signals.append(("RSI超卖反弹", df["日期"].iloc[i], df["收盘"].iloc[i]))
        elif df["RSI"].iloc[i] > 70 and df["RSI"].iloc[i] < df["RSI"].iloc[i-1]:
            signals.append(("RSI超买回落", df["日期"].iloc[i], df["收盘"].iloc[i]))
    return df, signals


def plot_charts(df, name):
    """生成图表"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                              gridspec_kw={'height_ratios': [3, 1, 1]})
    fig.suptitle(f"{name} — 技术分析图表", fontsize=16, fontweight="bold")
    
    # K线 + MA
    ax1 = axes[0]
    colors = ["red" if df["收盘"].iloc[i] >= df["开盘"].iloc[i] else "green"
              for i in range(len(df))]
    ax1.bar(range(len(df)), df["收盘"] - df["开盘"], 
            bottom=df[["开盘", "收盘"]].min(axis=1),
            color=colors, width=0.6, alpha=0.7)
    ax1.vlines(range(len(df)), df["最低"], df["最高"], colors=colors, linewidth=0.5)
    for n, c in [(5, "#FF6B6B"), (10, "#4ECDC4"), (20, "#45B7D1"), (60, "#96CEB4")]:
        if f"MA{n}" in df.columns:
            ax1.plot(range(len(df)), df[f"MA{n}"], c=c, label=f"MA{n}", linewidth=1)
    ax1.set_ylabel("价格")
    ax1.legend(loc="best")
    ax1.grid(alpha=0.3)
    
    # MACD
    ax2 = axes[1]
    ax2.bar(range(len(df)), df["MACD"], color=["red" if v >= 0 else "green" for v in df["MACD"]], alpha=0.5, width=0.6)
    ax2.plot(range(len(df)), df["DIF"], c="blue", label="DIF", linewidth=1)
    ax2.plot(range(len(df)), df["DEA"], c="orange", label="DEA", linewidth=1)
    ax2.axhline(0, c="gray", linewidth=0.5)
    ax2.set_ylabel("MACD")
    ax2.legend(loc="best")
    ax2.grid(alpha=0.3)
    
    # RSI
    ax3 = axes[2]
    ax3.plot(range(len(df)), df["RSI"], c="purple", linewidth=1.5)
    ax3.axhline(70, c="red", linestyle="--", alpha=0.5, label="超买")
    ax3.axhline(30, c="green", linestyle="--", alpha=0.5, label="超卖")
    ax3.set_ylabel("RSI")
    ax3.set_xlabel("交易日")
    ax3.legend(loc="best")
    ax3.grid(alpha=0.3)
    ax3.set_ylim(0, 100)
    
    # X轴日期
    n = len(df)
    tick_positions = list(range(0, n, max(1, n // 8)))
    tick_labels = [df["日期"].iloc[i].strftime("%m-%d") for i in tick_positions]
    ax3.set_xticks(tick_positions)
    ax3.set_xticklabels(tick_labels, rotation=45)
    
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def generate_report(df, name, signals):
    """生成 HTML 报告"""
    chart_b64 = plot_charts(df, name)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    change_pct = ((latest["收盘"] - prev["收盘"]) / prev["收盘"] * 100)
    trend = "🟢 上涨" if change_pct > 0 else "🔴 下跌"
    
    rsi_val = latest.get("RSI", 50)
    rsi_status = "超买区 ⚠️" if rsi_val >= 70 else ("超卖区 💡" if rsi_val <= 30 else "中性区域")
    
    macd_signal = latest.get("DIF", 0) - latest.get("DEA", 0)
    macd_status = "多头 (DIF > DEA) 🟢" if macd_signal > 0 else "空头 (DIF < DEA) 🔴"
    
    ma_trend = ""
    if "MA5" in df.columns and "MA20" in df.columns:
        ma_trend = "多头排列 📈" if latest["MA5"] > latest["MA20"] else "空头排列 📉"
    
    signals_html = ""
    for sig_type, date, price in signals[-5:]:
        signals_html += f"<tr><td>{sig_type}</td><td>{date.strftime('%Y-%m-%d')}</td><td>{price:.2f}</td></tr>"
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{name} - AutoStock 分析报告</title>
<style>
  body {{ font-family: -apple-system, 'PingFang SC', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  h1 {{ color: #333; border-bottom: 3px solid #4ECDC4; padding-bottom: 10px; }}
  .card {{ background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .price {{ font-size: 28px; font-weight: bold; color: #333; }}
  .change {{ font-size: 16px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
  .metric {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
  .metric-value {{ font-size: 22px; font-weight: bold; }}
  .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #f0f0f0; }}
  .chart {{ width: 100%; }}
  .donate {{ text-align: center; margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; }}
  .donate a {{ color: #0070ba; font-weight: bold; }}
</style></head>
<body>
  <h1>🔍 {name} 技术分析报告</h1>
  <div class="card">
    <div class="grid">
      <div class="metric"><div class="metric-value">{latest['收盘']:.2f}</div><div class="metric-label">最新收盘价</div></div>
      <div class="metric"><div class="metric-value {('red' if change_pct > 0 else 'green')}">{trend} ({change_pct:+.2f}%)</div><div class="metric-label">当日涨跌</div></div>
      <div class="metric"><div class="metric-value">{latest['成交量']:.0f}</div><div class="metric-label">成交量</div></div>
      <div class="metric"><div class="metric-value">¥{latest['成交额']/1e8:.1f}亿</div><div class="metric-label">成交额</div></div>
    </div>
  </div>
  <div class="card">
    <h2>技术指标</h2>
    <div class="grid">
      <div class="metric"><div class="metric-value">{rsi_val:.1f}</div><div class="metric-label">RSI(14) — {rsi_status}</div></div>
      <div class="metric"><div class="metric-value">{latest.get('MA5',0):.2f}</div><div class="metric-label">MA5</div></div>
      <div class="metric"><div class="metric-value">{latest.get('MA20',0):.2f}</div><div class="metric-label">MA20 — {ma_trend}</div></div>
      <div class="metric"><div class="metric-value">{macd_status}</div><div class="metric-label">MACD 趋势</div></div>
    </div>
  </div>
  <div class="card">
    <h2>信号提醒</h2>
    <table><tr><th>类型</th><th>日期</th><th>价格</th></tr>{signals_html or '<tr><td colspan="3">暂无显著信号</td></tr>'}</table>
  </div>
  <div class="card">
    <h2>图表分析</h2>
    <img class="chart" src="data:image/png;base64,{chart_b64}" alt="技术分析图" />
  </div>
  <div class="donate">
    觉得有用？<a href="https://paypal.me/netmstar">☕ 请我喝杯咖啡</a> 支持持续更新！
  </div>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description="AutoStock — A股自动化分析工具")
    parser.add_argument("codes", nargs="*", help="股票代码，如 600519")
    parser.add_argument("--all", action="store_true", help="分析所有内置股票")
    args = parser.parse_args()
    
    codes = args.codes if args.codes else list(STOCKS.keys())
    
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for code in codes:
        name = STOCKS.get(code, f"{code}")
        print(f"📊 正在分析 {name}({code})...")
        
        df = fetch_data(code)
        if df is None or len(df) < 30:
            print(f"  ⚠️ 获取失败或数据不足")
            continue
        
        df, signals = calc_indicators(df)
        report = generate_report(df, name, signals)
        
        outpath = f"output/{code}_{timestamp}.html"
        with open(outpath, "w") as f:
            f.write(report)
        print(f"  ✅ 报告已生成: {outpath}")
    
    print(f"\n✨ 共分析 {len(codes)} 只股票")
    print(f"   打开 output/ 目录查看报告")


if __name__ == "__main__":
    main()
