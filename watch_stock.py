#!/usr/bin/env python3
"""
实时盯盘脚本 - 每30分钟检查一次
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace-finance/stock-analyzer')

from data_source import AKShareDataSource
from analysis import SignalAnalyzer

# 盯盘股票列表
WATCH_STOCKS = [
    '002185.SZ',  # 华天科技
    '002413.SZ',  # 雷科防务
    '600410.SH',  # 华胜天成
    '603666.SH',  # 亿嘉和
]

SIGNAL_FILE = '/tmp/watch_signals.json'

def get_previous_signals():
    """获取之前的信号"""
    if os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_signals(signals):
    """保存当前信号"""
    with open(SIGNAL_FILE, 'w') as f:
        json.dump(signals, f)

def watch():
    print(f"\n{'='*50}")
    print(f"🕐 {datetime.now().strftime('%H:%M:%S')} 实时盯盘")
    print(f"{'='*50}")
    
    data_source = AKShareDataSource()
    analyzer = SignalAnalyzer()
    
    previous_signals = get_previous_signals()
    current_signals = {}
    alerts = []
    
    for code in WATCH_STOCKS:
        try:
            # 获取最近5天数据
            df = data_source.get_daily_data(code, start_date='20250301')
            if df is None or len(df) < 5:
                continue
            
            df_analyzed = analyzer.analyze(df)
            latest = df_analyzed.iloc[-1]
            
            name = data_source.get_stock_info(code).get('name', code)
            close = latest['close']
            buy_score = int(latest.get('BUY_SCORE', 0))
            sell_score = int(latest.get('SELL_SCORE', 0))
            signal = latest.get('SIGNAL', 'HOLD')
            
            current_signals[code] = {
                'name': name,
                'close': close,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'signal': signal
            }
            
            # 检查是否有新信号
            prev = previous_signals.get(code, {})
            prev_signal = prev.get('signal', 'HOLD')
            
            if signal != prev_signal and prev_signal != 'HOLD':
                alerts.append(f"⚠️ {name} ({code}) 信号变化: {prev_signal} → {signal}")
            elif signal == 'BUY' and buy_score >= 3:
                alerts.append(f"🟢 买入信号: {name} ({code}) - 收盘 {close:.2f}")
            elif signal == 'SELL' and sell_score >= 3:
                alerts.append(f"🔴 卖出信号: {name} ({code}) - 收盘 {close:.2f}")
            
            # 打印当前状态
            emoji = '🟢' if signal == 'BUY' else ('🔴' if signal == 'SELL' else '⚪')
            print(f"{emoji} {name}: {close:.2f} | 买入:{buy_score} 卖出:{sell_score} | {signal}")
            
        except Exception as e:
            print(f"❌ {code} 分析失败: {e}")
    
    # 保存当前信号
    save_signals(current_signals)
    
    # 输出提醒
    if alerts:
        print("\n📢 信号变化:")
        for alert in alerts:
            print(alert)
    else:
        print("\n✅ 无新信号")
    
    return alerts

if __name__ == '__main__':
    watch()
