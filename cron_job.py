#!/usr/bin/env python3
"""
定时任务入口 - 检查是否为A股交易日
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace-finance/stock-analyzer')

# 判断今天是否是交易日（排除周末）
def is_trading_day():
    today = datetime.now()
    weekday = today.weekday()
    
    # 周六(5)或周日(6)不交易
    if weekday >= 5:
        return False
    
    return True

if __name__ == '__main__':
    task = sys.argv[1] if len(sys.argv) > 1 else ''
    
    if task == 'morning':
        # 开盘后分析
        if is_trading_day():
            os.chdir('/root/.openclaw/workspace-finance/stock-analyzer')
            os.system('python3 daily_analysis.py >> /tmp/daily_analysis.log 2>&1')
    elif task == 'evening':
        # 收盘后更新
        if is_trading_day():
            os.chdir('/root/.openclaw/workspace-finance/stock-analyzer')
            os.system('python3 update_data.py >> /tmp/update_data.log 2>&1')
