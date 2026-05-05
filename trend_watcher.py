#!/usr/bin/env python3
"""
TrendWatcher - GitHub热门项目追踪器
自动采集GitHub Trending，生成热门项目日报
帮助开发者不错过热门开源项目
"""
import os, json, requests, re
from datetime import datetime
from collections import Counter

class TrendWatcher:
    """GitHub热门项目追踪"""
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_trending(self, language="python", since="daily"):
        """抓取GitHub Trending"""
        url = "https://api.gitterapp.com/repositories"
        params = {"since": since, "language": language}
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        
        # 备用API
        try:
            resp = requests.get(
                f"https://gh-trending-api.herokuapp.com/repositories",
                params={"language": language, "since": since},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        
        return []
    
    def fetch_trending_html(self, language="python", since="daily"):
        """直接从GitHub页面解析"""
        url = f"https://github.com/trending/{language}?since={since}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            repos = []
            pattern = r'href="/([^/]+/[^/"]+)"'
            matches = re.findall(pattern, resp.text)
            seen = set()
            for m in matches:
                if m not in seen:
                    seen.add(m)
                    repos.append({"full_name": m})
            return repos[:20]
        except:
            return self.fetch_trending(language, since)
    
    def get_repo_info(self, repo):
        """获取仓库详细信息"""
        if isinstance(repo, dict) and "full_name" in repo:
            return repo
        return {"full_name": repo if isinstance(repo, str) else "unknown/unknown"}
    
    def generate_report(self, languages=None):
        """生成趋势报告"""
        if languages is None:
            languages = ["python", "javascript", "typescript", "go", "rust"]
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub Trending 日报 - TrendWatcher</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0d1117; color:#c9d1d9; padding:20px; max-width:1200px; margin:0 auto; }}
h1 {{ font-size:28px; margin-bottom:5px; color:#fff; }}
.subtitle {{ color:#8b949e; font-size:14px; margin-bottom:20px; }}
.lang-tab {{ display:inline-block; padding:8px 16px; margin:4px; border-radius:20px; background:#21262d; color:#c9d1d9; cursor:pointer; font-size:14px; }}
.lang-tab.active {{ background:#1f6feb; color:#fff; }}
.repo {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-bottom:12px; }}
.repo h3 {{ font-size:16px; margin-bottom:4px; }}
.repo h3 a {{ color:#58a6ff; text-decoration:none; }}
.repo h3 a:hover {{ text-decoration:underline; }}
.repo .desc {{ color:#8b949e; font-size:13px; margin-bottom:8px; }}
.repo .meta {{ display:flex; gap:16px; font-size:12px; color:#8b949e; flex-wrap:wrap; }}
.repo .meta span {{ display:flex; align-items:center; gap:4px; }}
.stars {{ color:#d29922; }}
.lang-dot {{ width:12px; height:12px; border-radius:50%; display:inline-block; }}
.footer {{ text-align:center; margin-top:40px; padding:20px; color:#484f58; font-size:12px; }}
</style>
</head>
<body>

<h1>🔥 GitHub Trending 日报</h1>
<div class="subtitle">{now} | 追踪 {len(languages)} 种语言 | 每日自动更新</div>

<div class="lang-tabs">
"""
        for lang in languages:
            html += f'\n    <span class="lang-tab active">#{lang}</span>'
        
        html += "\n</div>\n\n"
        
        for lang in languages:
            html += f'\n<h2 id="{lang}">#{lang}</h2>\n'
            repos = self.fetch_trending_html(lang, "daily")
            
            for i, repo in enumerate(repos[:10]):
                name = repo.get("full_name", str(repo)) if isinstance(repo, dict) else str(repo)
                desc = repo.get("description", "")[:120] if isinstance(repo, dict) else ""
                stars = repo.get("stars", "★") if isinstance(repo, dict) else "★"
                
                html += f"""
<div class="repo">
    <h3><a href="https://github.com/{name}" target="_blank">#{i+1} {name}</a></h3>
    <div class="desc">{desc or '暂无描述'}</div>
    <div class="meta">
        <span class="stars">⭐ {stars}</span>
        <span>🔤 {lang}</span>
    </div>
</div>
"""
        
        html += """
<div class="footer">
    🦞 TrendWatcher by Claw | 自动生成 | 数据来源: GitHub Trending<br>
    购买完整工具包: PayPal netmstar@gmail.com | 支付宝 pkuzxx@gmail.com
</div>

</body>
</html>"""
        
        fname = f"github_trending_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        fpath = os.path.join(self.output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"✅ Trending报告已生成: {fpath}")
        return fpath


if __name__ == "__main__":
    tw = TrendWatcher()
    output = tw.generate_report()
    print(f"\n📋 包含: Python, JavaScript, TypeScript, Go, Rust")
    print(f"💡 浏览器打开查看: {output}")
