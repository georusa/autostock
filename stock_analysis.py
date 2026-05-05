#!/usr/bin/env python3
"""
CEO A股量化分析工具
基于公开数据源的 A 股行情分析 + 技术指标 + 可视化报告
（只使用合法公开数据，不涉及内幕/隐私/非法数据）

功能:
1. 获取 A 股行情数据（通过免费公开 API）
2. 技术指标计算（MA, RSI, MACD等）
3. 生成可视化分析报告

使用: python stock_analysis.py
输出: output/stock_report.html
"""

import sys
import json
import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# macOS Chinese font
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'STHeiti', 'Songti SC']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = Path(__file__).parent / "output"
STOCKS = {
    '000001.SZ': '平安银行',
    '600519.SH': '贵州茅台',
    '000858.SZ': '五粮液',
    '600036.SH': '招商银行',
    '601318.SH': '中国平安',
    '002415.SZ': '海康威视',
    '000333.SZ': '美的集团',
    '600900.SH': '长江电力',
}


class StockAnalyzer:
    """基于公开数据源的 A 股技术分析"""
    
    @staticmethod
    def fetch_daily(code, name, days=120):
        """
        通过公开 API 获取日线数据
        使用 akashare 替代方案：直接请求东方财富公开接口
        数据源: 东方财富（公开免费数据接口）
        """
        # 转换股票代码格式
        if code.endswith('.SZ'):
            secid = f"0.{code.replace('.SZ', '')}"
        elif code.endswith('.SH'):
            secid = f"1.{code.replace('.SH', '')}"
        else:
            return None
        
        import httpx
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'secid': secid,
            'ut': 'fa5fd1943c7b386f172d6893dbfd32bb',
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日K
            'fqt': '1',    # 前复权
            'end': '20500101',
            'lmt': days,
            '_': int(datetime.datetime.now().timestamp() * 1000),
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
        }
        
        try:
            r = httpx.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                klines = data.get('data', {}).get('klines', [])
                if not klines:
                    return None
                
                rows = []
                for line in klines:
                    parts = line.split(',')
                    rows.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6]),
                        'stock_code': code,
                        'stock_name': name,
                    })
                
                df = pd.DataFrame(rows)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                return df
        except Exception as e:
            print(f"   ⚠ {name}: 请求失败 - {e}")
            return None
        
        return None
    
    @staticmethod
    def compute_indicators(df):
        """计算技术指标"""
        if df is None or len(df) < 20:
            return None
        
        df = df.copy()
        
        # 移动平均线
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA10'] = df['close'].rolling(10).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        
        # RSI (14)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df['RSI14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # 涨跌幅
        df['pct_change'] = df['close'].pct_change() * 100
        
        # 成交量均线
        df['VOL_MA5'] = df['volume'].rolling(5).mean()
        
        return df
    
    @staticmethod
    def plot_chart(df, output_path):
        """生成分析图表"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), 
                                  gridspec_kw={'height_ratios': [3, 1.2, 1.2]})
        
        stock_label = f"{df.iloc[0]['stock_name']} ({df.iloc[0]['stock_code']})"
        latest = df.iloc[-1]
        
        # ---------- 图1: K线 + MA ----------
        ax1 = axes[0]
        
        # 用简化的方式画图（完整的K线图需要 mplfinance）
        ax1.plot(df['date'], df['close'], 'b-', linewidth=1.5, label='收盘价', alpha=0.8)
        ax1.plot(df['date'], df['MA5'], 'orange', linewidth=1, alpha=0.7, label='MA5')
        ax1.plot(df['date'], df['MA10'], 'green', linewidth=1, alpha=0.7, label='MA10')
        ax1.plot(df['date'], df['MA20'], 'red', linewidth=1, alpha=0.7, label='MA20')
        
        # Fill between MA5 and MA20 for trend visualization
        ax1.fill_between(df['date'], df['MA5'], df['MA20'], 
                         where=df['MA5'] >= df['MA20'], 
                         color='green', alpha=0.08, label='上升趋势区间')
        
        # 最新价标注
        last_close = latest['close']
        last_date = latest['date']
        ax1.annotate(f'{last_close:.2f}', 
                    xy=(last_date, last_close),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=12, fontweight='bold', color='blue',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        ax1.set_title(f'{stock_label} - 走势分析', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格')
        ax1.legend(loc='upper left', fontsize=9, ncol=4)
        ax1.grid(alpha=0.2)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # ---------- 图2: MACD ----------
        ax2 = axes[1]
        ax2.bar(df['date'], df['MACD_Hist'], 
                color=['red' if v >= 0 else 'green' for v in df['MACD_Hist']],
                width=0.8, alpha=0.6)
        ax2.plot(df['date'], df['MACD'], 'b-', linewidth=1, label='MACD')
        ax2.plot(df['date'], df['MACD_Signal'], 'r-', linewidth=1, label='Signal')
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
        ax2.set_ylabel('MACD')
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(alpha=0.2)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # ---------- 图3: RSI + 成交量 ----------
        ax3 = axes[2]
        
        # 成交量柱状图
        vol_bars = ax3.bar(df['date'], df['volume'] / 1e8, 
                           alpha=0.3, color='gray', width=0.8)
        ax3.set_ylabel('成交量(亿)', color='gray')
        
        # RSI 双轴
        ax3_rsi = ax3.twinx()
        ax3_rsi.plot(df['date'], df['RSI14'], 'purple', linewidth=1.5, label='RSI14')
        ax3_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
        ax3_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.4, linewidth=0.8)
        ax3_rsi.set_ylim(0, 100)
        ax3_rsi.set_ylabel('RSI', color='purple')
        ax3_rsi.legend(loc='upper right', fontsize=9)
        
        ax3.grid(alpha=0.2)
        ax3.spines['top'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            'path': str(output_path),
            'latest_close': latest['close'],
            'latest_pct': latest.get('pct_change', 0),
            'latest_rsi': latest.get('RSI14', 50),
            'latest_macd': latest.get('MACD', 0),
            'latest_volume': latest['volume'],
            'latest_date': latest['date'].strftime('%Y-%m-%d'),
        }
    
    @staticmethod
    def generate_html(summaries, output_path):
        """生成分析报告"""
        charts = [s['path'] for s in summaries]
        # Count signals
        buy_signals = sum(1 for s in summaries if s.get('latest_rsi', 50) < 30)
        sell_signals = sum(1 for s in summaries if s.get('latest_rsi', 50) > 70)
        normal_count = len(summaries) - buy_signals - sell_signals
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CEO 量化分析报告 - {datetime.date.today()}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f7fa; color: #1a1a2e; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
              color: white; padding: 40px; border-radius: 16px; margin-bottom: 30px;
              text-align: center; }}
    .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
    .header p {{ opacity: 0.8; font-size: 14px; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
    .stat-box {{ background: white; border-radius: 12px; padding: 20px; text-align: center;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .stat-box .value {{ font-size: 28px; font-weight: bold; }}
    .stat-box .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
    .buy .value {{ color: #e74c3c; }}
    .sell .value {{ color: #27ae60; }}
    .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .card h2 {{ font-size: 18px; margin-bottom: 16px; border-left: 4px solid #0f3460; padding-left: 12px; }}
    .stock-row {{ display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #f0f0f5; }}
    .stock-row:last-child {{ border-bottom: none; }}
    .stock-info {{ flex: 1; }}
    .stock-name {{ font-weight: bold; font-size: 16px; }}
    .stock-price {{ font-size: 18px; font-weight: bold; }}
    .stock-pct {{ font-size: 14px; }}
    .up {{ color: #e74c3c; }} .down {{ color: #27ae60; }}
    .rsi-bar {{ height: 6px; border-radius: 3px; margin-top: 4px; }}
    .card img {{ max-width: 100%; border-radius: 8px; }}
    .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px;
              background: #e8f4fd; color: #2b6cb0; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🦞 CEO A股量化分析报告</h1>
        <p>自动生成于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} · 基于公开行情数据</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-box">
            <div class="value">{len(summaries)}</div>
            <div class="label">📊 监测标的</div>
        </div>
        <div class="stat-box buy">
            <div class="value">{buy_signals}</div>
            <div class="label">🔴 RSI超卖(机会)</div>
        </div>
        <div class="stat-box sell">
            <div class="value">{sell_signals}</div>
            <div class="label">🟢 RSI超买(风险)</div>
        </div>
    </div>

    <div class="card">
        <h2>📈 行情总览</h2>
"""
        for s in summaries:
            pct = s.get('latest_pct', 0)
            rsi = s.get('latest_rsi', 50)
            pct_cls = 'up' if pct >= 0 else 'down'
            rsi_color = '#e74c3c' if rsi > 70 else ('#27ae60' if rsi < 30 else '#3498db')
            rsi_signal = '超买⚠️' if rsi > 70 else ('超卖💡' if rsi < 30 else '正常')
            
            html += f"""
        <div class="stock-row">
            <div class="stock-info">
                <div class="stock-name">{Path(s['path']).stem.split('_')[0]}</div>
                <div class="stock-tag"><span class="badge">{s['latest_date']}</span></div>
            </div>
            <div style="text-align:right; margin-right: 24px;">
                <div class="stock-price">{s['latest_close']:.2f}</div>
                <div class="stock-pct {pct_cls}">{pct:+.2f}%</div>
            </div>
            <div style="text-align:center; width: 100px;">
                <div style="font-weight:bold; color:{rsi_color};">RSI {rsi:.1f}</div>
                <div style="font-size:11px; color:#888;">{rsi_signal}</div>
                <div class="rsi-bar" style="width:{rsi}%; background:{rsi_color};"></div>
            </div>
        </div>"""
        
        html += """
    </div>
"""
        
        # 每只股票的分析图表
        for i, s in enumerate(summaries):
            name = Path(s['path']).stem.split('_')[0]
            html += f"""
    <div class="card">
        <h2>📊 {name} 详细分析</h2>
        <img src="../{s['path']}" alt="{name} 分析图" style="width:100%;">
    </div>
"""
        
        html += f"""
    <div class="footer">
        <p>🦞 由 CEO AI Agent 自动生成 · 数据来源：公开行情接口 · 不构成投资建议</p>
        <p>{datetime.datetime.now().year} · 仅供学习参考</p>
    </div>
</div>
</body>
</html>"""
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / output_path).write_text(html, encoding='utf-8')
        return str(OUTPUT_DIR / output_path)


def main():
    print("🦞 CEO A股量化分析系统启动")
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    analyzer = StockAnalyzer()
    summaries = []
    
    for code, name in STOCKS.items():
        print(f"\n📊 分析 {name}({code})...")
        df = analyzer.fetch_daily(code, name)
        if df is not None:
            print(f"   ✓ 获取数据: {len(df)} 条日线")
            df_indicators = analyzer.compute_indicators(df)
            if df_indicators is not None:
                chart_file = OUTPUT_DIR / f"{name}_{code.replace('.', '_')}_chart.png"
                summary = analyzer.plot_chart(df_indicators, chart_file)
                if summary:
                    summaries.append(summary)
                    print(f"   ✓ 图表生成: {summary['latest_close']:.2f} | "
                          f"RSI={summary['latest_rsi']:.1f} | MACD={summary['latest_macd']:.2f}")
                else:
                    print(f"   ✗ 图表生成失败")
            else:
                print(f"   ✗ 指标计算失败")
        else:
            print(f"   ✗ 数据获取失败")
    
    if summaries:
        print(f"\n📝 生成分析报告...")
        report = analyzer.generate_html(summaries, f"stock_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        print(f"   ✓ 报告已生成: {report}")
    
    print(f"\n{'=' * 40}")
    print(f"✅ 分析完成! 成功分析 {len(summaries)}/{len(STOCKS)} 只股票")
    print(f"📂 输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
