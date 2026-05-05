#!/usr/bin/env python3
"""
Python 环境检查工具
检查依赖库完整性，自动安装缺失组件

购买完整版: paypal.me/georusa
"""
import os, sys, subprocess, importlib, json

REQUIRED = {
    'pandas': '数据框架',
    'numpy': '数值计算',
    'requests': 'HTTP请求',
    'httpx': '高级HTTP',
    'beautifulsoup4': '网页解析',
    'matplotlib': '数据可视化',
}

def check():
    results = {'ok': [], 'missing': [], 'version': {}}
    for pkg, desc in REQUIRED.items():
        try:
            mod = importlib.import_module(pkg.replace('-', '_').split('.')[0])
            ver = getattr(mod, '__version__', 'OK')
            results['ok'].append(pkg)
            results['version'][pkg] = str(ver)
        except ImportError:
            results['missing'].append(pkg)
    return results

def main():
    print("🔍 Python 环境检查")
    print("=" * 30)
    print(f"Python: {sys.version.split()[0]}")
    
    res = check()
    for pkg in res['ok']:
        print(f"  ✅ {pkg} ({res['version'].get(pkg, 'OK')})")
    for pkg in res['missing']:
        print(f"  ❌ {pkg} - 缺失")
    
    if res['missing']:
        print(f"\n📦 {len(res['missing'])} 个依赖缺失")
        print("自动安装: python3 env_checker.py install")
    else:
        print("\n✅ 环境完整")

    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        for pkg in res['missing']:
            print(f"  安装 {pkg}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
        print("✅ 安装完成!")
    
    print("\n💰 购买完整版工具包: paypal.me/georusa")

if __name__ == "__main__":
    main()
