#!/usr/bin/env python3
"""
每日收盘后更新网站数据
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace-finance/stock-analyzer')

import subprocess
import os

os.chdir('/root/.openclaw/workspace-finance/stock-analyzer')

# 批量分析热门股票
STOCKS = "600519.SH 600036.SH 601318.SH 600900.SH 000001.SZ 300750.SZ 002594.SZ 300059.SZ 601888.SH 000002.SZ"

print("=" * 50)
print("收盘后更新网站数据")
print("=" * 50)

# 运行批量分析
print("\n运行批量分析...")
result = subprocess.run(
    f"python3 batch_analyzer.py {STOCKS}",
    shell=True,
    capture_output=True,
    text=True,
    timeout=300
)

if result.returncode == 0:
    print("✅ 数据更新完成")
else:
    print(f"❌ 更新失败: {result.stderr}")

print("\n完成!")
