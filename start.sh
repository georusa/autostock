#!/bin/bash
# AutoStock - 一键启动 A 股分析服务
echo "🚀 AutoStock Web 服务"
echo "===================="
echo ""
echo "在浏览器打开: http://localhost:8888"
echo "输入股票代码即可生成分析报告"
echo ""
echo "热门股票: 600519(茅台) 000858(五粮液) 002415(海康威视)"
echo "          300750(宁德时代) 000333(美的) 601318(平安)"
echo ""
echo "按 Ctrl+C 停止服务"
echo "===================="
echo ""

cd "$(dirname "$0")"
python3 web_server.py
