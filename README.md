# Autostock - AI-Powered A-Stock Analysis Toolkit

智能A股量化分析工具集，支持自动数据采集、技术指标分析、趋势识别与可视化报告生成。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

## Features

- **Real-time Data**: Fetch A-share market data (沪深两市) from multiple data sources automatically
- **Technical Analysis**: MACD, RSI, KDJ, Bollinger Bands, moving averages, and more
- **Trend Recognition**: Identify buy/sell signals based on multi-indicator convergence/divergence
- **Visual Reports**: Generate professional-grade analysis charts and PDF reports
- **Web Dashboard**: Interactive web interface for on-demand analysis
- **Data Harvesting**: Batch download and archive historical data
- **Trend Watching**: Monitor multiple stocks and get alerts on trend changes

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze a single stock
python3 autostock.py --symbol 600519 --days 120

# Or specify stock name
python3 autostock.py --name 贵州茅台 --days 120

# Launch web dashboard
python3 web_server.py --port 8080

# Start the trend watcher
python3 trend_watcher.py --watchlist 600519,000858,300750
```

## Available Tools

| Tool | Description |
|------|-------------|
| `autostock.py` | Core stock analysis engine |
| `stock_analysis.py` | Advanced technical analysis modules |
| `stock_dashboard.py` | Real-time market dashboard |
| `data_harvest.py` | Historical data batch collector |
| `data_report_tool.py` | Automated report generator |
| `trend_watcher.py` | Multi-stock trend monitoring |
| `web_server.py` | Web-based interactive dashboard |

## Sample Reports

Generate professional reports for any A-share stock:

```bash
python3 autostock.py --symbol 600519 --days 120  # 贵州茅台
python3 autostock.py --symbol 000858 --days 120  # 五粮液
python3 autostock.py --symbol 300750 --days 120  # 宁德时代
```

## Support

If this project helps you, consider supporting:

- **PayPal**: `https://paypal.me/netmstar`
- **BTC**: (contact for address)

Questions or custom development? Open an issue or reach out!

## License

MIT
