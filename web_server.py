#!/usr/bin/env python3
"""
AutoStock Web Server - 在线 A 股分析服务
启动后可在浏览器中直接使用
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, render_template_string, request, jsonify
from autostock import fetch_data, calc_indicators, generate_report

app = Flask(__name__)
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>AutoStock - A股分析工具</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, 'PingFang SC', sans-serif; background: #f0f2f5; min-height: 100vh; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }
.header h1 { font-size: 32px; margin-bottom: 8px; }
.header p { opacity: 0.9; font-size: 14px; }
.container { max-width: 700px; margin: 0 auto; padding: 20px; }
.card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.stocks { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; margin: 16px 0; }
.stock-btn { padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; text-align: center; transition: all .2s; background: white; font-size: 13px; }
.stock-btn:hover { border-color: #667eea; background: #f8f9ff; }
.stock-btn.selected { border-color: #667eea; background: #667eea; color: white; }
.input-group { display: flex; gap: 8px; margin: 16px 0; }
.input-group input { flex: 1; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; }
.input-group button { padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; font-weight: 600; transition: background .2s; }
.input-group button:hover { background: #5a6fd6; }
.loading { display: none; text-align: center; padding: 40px; }
.loading .spinner { width: 40px; height: 40px; border: 4px solid #e0e0e0; border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.result { display: none; }
iframe { width: 100%; min-height: 1000px; border: none; }
.footer { text-align: center; padding: 20px; color: #888; font-size: 13px; }
.footer a { color: #667eea; text-decoration: none; }
</style></head>
<body>
<div class="header">
  <h1>📊 AutoStock</h1>
  <p>输入股票代码，一键生成 A 股技术分析报告</p>
</div>
<div class="container">
  <div class="card">
    <h3>热门股票</h3>
    <div class="stocks" id="hotStocks">
      <button class="stock-btn" data-code="600519.SH">贵州茅台</button>
      <button class="stock-btn" data-code="000858.SZ">五粮液</button>
      <button class="stock-btn" data-code="300750.SZ">宁德时代</button>
      <button class="stock-btn" data-code="002415.SZ">海康威视</button>
      <button class="stock-btn" data-code="000333.SZ">美的集团</button>
      <button class="stock-btn" data-code="601318.SH">中国平安</button>
      <button class="stock-btn" data-code="600036.SH">招商银行</button>
      <button class="stock-btn" data-code="000002.SZ">万科A</button>
    </div>
    <div class="input-group">
      <input type="text" id="stockCode" placeholder="输入股票代码，如 600519 或 600519.SH" />
      <button onclick="analyze()">分析</button>
    </div>
  </div>
  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p>正在获取数据并生成分析报告...</p>
  </div>
  <div class="result" id="result">
    <div class="card">
      <iframe id="reportFrame"></iframe>
    </div>
  </div>
  <div class="footer">
    觉得有用？<a href="https://paypal.me/netmstar" target="_blank">☕ 请我喝杯咖啡</a> 支持持续更新！
  </div>
</div>
<script>
function selectStock(el) {
  document.querySelectorAll('.stock-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('stockCode').value = el.dataset.code;
}
document.querySelectorAll('.stock-btn').forEach(b => b.addEventListener('click', () => selectStock(b)));
function analyze() {
  const code = document.getElementById('stockCode').value.trim();
  if(!code) { alert('请输入股票代码'); return; }
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result').style.display = 'none';
  fetch('/analyze', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({code}) })
    .then(r => r.json())
    .then(data => {
      document.getElementById('loading').style.display = 'none';
      if(data.error) { alert(data.error); return; }
      document.getElementById('reportFrame').src = '/report/' + data.report_id;
      document.getElementById('result').style.display = 'block';
      document.getElementById('reportFrame').onload = function() {
        this.style.height = this.contentWindow.document.body.scrollHeight + 'px';
      };
    })
    .catch(e => { document.getElementById('loading').style.display = 'none'; alert('分析失败: ' + e); });
}
</script>
</body></html>"""

reports_cache = {}
report_counter = 0

@app.route('/')
def index():
    landing = os.path.join(os.path.dirname(__file__), 'templates', 'product_landing.html')
    html = open(landing).read()
    return html

@app.route('/products')
def products():
    return '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>AutoStock 产品目录</title>
<style>
body{font-family:-apple-system, 'PingFang SC', sans-serif;background:#0f0f23;color:#e0e0e0;padding:40px;max-width:800px;margin:auto}
h1{color:#667eea;border-bottom:1px solid #333;padding-bottom:12px}
.card{background:#1a1a3e;border:1px solid #2a2a5e;border-radius:12px;padding:20px;margin:16px 0}
h2{color:#00d2ff;margin:0 0 8px 0}
.price{color:#667eea;font-weight:bold;display:inline-block;padding:4px 12px;border:1px solid #667eea;border-radius:4px;font-size:14px;margin:8px 0}
.desc{color:#999;font-size:14px}
.link{color:#667eea;text-decoration:none;display:inline-block;margin-top:8px}
.footer{text-align:center;color:#555;margin-top:40px;padding-top:20px;border-top:1px solid #333}
</style></head><body>
<h1>🛒 AutoStock 产品目录</h1>
<div class="card">
<h2>📊 A股自动化分析工具</h2>
<div class="price">开源版: 免费</div>
<div class="desc">输入股票代码，自动获取数据、计算技术指标、生成HTML报告。支持MA/RSI/MACD。</div>
<a class="link" href="/analyze">👉 在线使用</a>
</div>
<div class="card">
<h2>💎 A股完整版</h2>
<div class="price">¥49.9</div>
<div class="desc">开源版全部功能 + 自定义均线 + 资金流向 + 行业对比 + 自动交易信号 + 永久更新</div>
<a class="link" href="https://paypal.me/netmstar/49.9">💰 购买</a>
</div>
<div class="card">
<h2>🔄 数据采集工具包</h2>
<div class="price">¥29.9</div>
<div class="desc">Web内容提取、CSV转JSON、表格提取、批量采集、格式转换。即装即用。</div>
<a class="link" href="https://paypal.me/netmstar/29.9">💰 购买</a>
</div>
<div class="card">
<h2>🤝 定制开发</h2>
<div class="price">$100起</div>
<div class="desc">根据您的具体需求开发自动化脚本、数据分析工具、量化模型。</div>
<a class="link" href="https://paypal.me/netmstar/100">💰 咨询</a>
</div>
<div class="footer">
<p>© 2026 AutoStock · Made with 🦞</p>
<p>PayPal: netmstar@gmail.com · 支付宝: pkuzxx@gmail.com</p>
</div>
</body></html>'''

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'GET':
        return render_template_string(INDEX_TEMPLATE)
    # POST
    global report_counter
    code = request.json.get('code', '').strip()
    if not code:
        return jsonify({'error': '请输入股票代码'})
    
    # 补全格式
    sec_code = code
    if '.' not in code:
        if code.startswith('6') or code.startswith('9'):
            sec_code = code + '.SH'
        else:
            sec_code = code + '.SZ'
    
    # 获取名称
    from autostock import STOCKS
    name = STOCKS.get(sec_code, sec_code)
    
    df = fetch_data(code)
    if df is None or len(df) < 20:
        return jsonify({'error': f'获取 {code} 数据失败，请检查代码是否正确'})
    
    df, signals = calc_indicators(df)
    report = generate_report(df, name, signals)
    
    report_counter += 1
    rid = f"r{report_counter}"
    reports_cache[rid] = report
    
    return jsonify({'report_id': rid})

@app.route('/report/<rid>')
def report(rid):
    if rid in reports_cache:
        return reports_cache[rid]
    return '<h1>报告不存在或已过期</h1>', 404


@app.route('/us')
def us_stock_page():
    """美股分析页面"""
    return '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>US Stock Analyzer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a1a;color:#e0e0e0;padding:20px}
.container{max-width:600px;margin:40px auto;text-align:center}
h1{font-size:32px;margin-bottom:8px}
p{color:#888;margin-bottom:20px}
.symbols{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:16px 0}
.sym-btn{padding:8px 16px;background:#1a1a3e;border:1px solid #2a2a5a;border-radius:8px;color:#e0e0e0;cursor:pointer}
.sym-btn:hover{border-color:#4a6cf7}
.input-group{display:flex;gap:8px;margin:16px 0}
.input-group input{flex:1;padding:12px;border:2px solid #2a2a5a;border-radius:8px;background:#1a1a3e;color:#fff;font-size:15px}
.input-group button{padding:12px 24px;background:#4a6cf7;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600}
.report-link{display:block;padding:12px;background:#1a1a3e;border:1px solid #2a2a5a;border-radius:8px;margin:8px 0;color:#4a6cf7;text-decoration:none}
.msg{color:#ffa726;margin:12px 0}
.footer{margin-top:40px;color:#555;font-size:12px}
</style></head>
<body>
<div class="container">
<h1>🇺🇸 US Stock Analyzer</h1>
<p>Real-time technical analysis for US stocks</p>
<div class="symbols" id="hotSymbols">
<button class="sym-btn" onclick="analyze('AAPL')">AAPL</button>
<button class="sym-btn" onclick="analyze('TSLA')">TSLA</button>
<button class="sym-btn" onclick="analyze('NVDA')">NVDA</button>
<button class="sym-btn" onclick="analyze('MSFT')">MSFT</button>
<button class="sym-btn" onclick="analyze('AMZN')">AMZN</button>
<button class="sym-btn" onclick="analyze('META')">META</button>
<button class="sym-btn" onclick="analyze('GOOGL')">GOOGL</button>
<button class="sym-btn" onclick="analyze('SPY')">SPY</button>
</div>
<div class="input-group">
<input type="text" id="usSymbol" placeholder="Enter symbol (AAPL, TSLA...)" />
<button onclick="analyze(document.getElementById('usSymbol').value)">Analyze</button>
</div>
<div id="usResult"></div>
<p class="msg">💡 Reports are saved in output/ folder</p>
<div class="footer">
<p>🦞 USStockAnalyzer by Claw | $19.99</p>
<p>PayPal: netmstar@gmail.com</p>
</div>
</div>
<script>
function analyze(sym){
if(!sym)return;
document.getElementById('usResult').innerHTML='<p>⏳ Generating report for '+sym+'...</p>';
fetch('/us/analyze/'+sym.toUpperCase())
.then(r=>r.json())
.then(d=>{
if(d.error) document.getElementById('usResult').innerHTML='<p>❌ '+d.error+'</p>';
else document.getElementById('usResult').innerHTML='<a class="report-link" href="/read/'+d.file+'" target="_blank">📊 '+d.symbol+' - $'+d.price+' ('+d.change+'%)</a>';
})
.catch(e=>document.getElementById('usResult').innerHTML='<p>❌ Error: '+e+'</p>');
}
</script>
</body>
</html>'''


@app.route('/us/analyze/<symbol>')
def us_analyze(symbol):
    """美股分析"""
    import subprocess,json
    try:
        result = subprocess.run(
            [sys.executable, "us_stock_analyzer.py", symbol.upper()],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        reports = sorted([f for f in os.listdir(output_dir) if f.startswith(f"us_report_{symbol.upper()}_")])
        if reports:
            # Extract price from log
            for line in result.stdout.split('\n'):
                if symbol.upper() in line and '$' in line:
                    parts = line.split('$')
                    if len(parts) > 1:
                        price_str = parts[1].split(')')[0]
                        change_str = parts[1].split(')')[1].strip() if ')' in parts[1] else ''
                        return jsonify({"symbol": symbol.upper(), "file": reports[-1], "price": price_str, "change": change_str})
            return jsonify({"symbol": symbol.upper(), "file": reports[-1], "price": "?", "change": "?"})
        return jsonify({"error": "Report generation failed"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/live')
def live():
    """实时A股行情仪表盘"""
    import subprocess
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    # 尝试运行生成器
    subprocess.run(
        [sys.executable, "stock_dashboard.py", "600519", "000858", "300750", "601318", "000333", "002594"],
        capture_output=True, timeout=15,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    dashes = sorted([f for f in os.listdir(output_dir) if f.startswith("dashboard_")])
    if dashes:
        return send_from_directory(output_dir, dashes[-1])
    return "<h2>仪表盘生成中，请稍后刷新</h2>", 202


@app.route('/demo/trending')
def demo_trending():
    """GitHub Trending演示"""
    import subprocess
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    subprocess.run(
        [sys.executable, "trend_watcher.py"],
        capture_output=True, timeout=15,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    trends = sorted([f for f in os.listdir(output_dir) if f.startswith("github_trending_")])
    if trends:
        return send_from_directory(output_dir, trends[-1])
    return "<h2>生成中...</h2>", 202


@app.route('/reports')
def report_list():
    """所有生成报告列表"""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    files = sorted(os.listdir(output_dir), reverse=True)[:20]
    html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>所有报告</title><style>body{font-family:system-ui;padding:20px;background:#f0f2f5}li{padding:8px;margin:4px;background:white;border-radius:8px;list-style:none}a{color:#667eea;text-decoration:none}</style></head><body>'
    html += '<h1>📊 所有报告</h1><ul>'
    for f in files:
        html += f'<li><a href="/read/{f}" target="_blank">{f}</a></li>'
    html += '</ul></body></html>'
    return html


@app.route('/read/<fname>')
def read_file(fname):
    """读取输出文件"""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    # 安全过滤
    fname = os.path.basename(fname)
    path = os.path.join(output_dir, fname)
    if os.path.exists(path) and os.path.isfile(path):
        # 检测是否为图片
        ext = os.path.splitext(fname)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            return send_from_directory(output_dir, fname)
        # HTML直接显示
        with open(path, encoding='utf-8') as f:
            content = f.read()
        return content
    return f'<h2>文件不存在: {fname}</h2>', 404


if __name__ == '__main__':
    from flask import send_from_directory
    port = int(os.environ.get('PORT', 8888))
    print(f"🚀 AutoStock Web 服务启动: http://localhost:{port}")
    print(f"   🇨🇳 A股分析 ⏎ /analyze")
    print(f"   🇺🇸 美股分析 ⏎ /us")
    print(f"   📊 仪表盘 ⏎ /live")
    print(f"   🔥 GitHub热门 ⏎ /demo/trending")
    print(f"   📋 所有报告 ⏎ /reports")
    print(f"   📦 产品目录 ⏎ /products")
    app.run(host='0.0.0.0', port=port, debug=True)
