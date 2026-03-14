#!/usr/bin/env python3
"""
每日开盘后分析脚本 - 推荐强势股票
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace-finance/stock-analyzer')

from data_source import AKShareDataSource
from analysis import SignalAnalyzer
import pandas as pd

# A股热门股票池
STOCK_POOL = [
    '600519.SH',  # 贵州茅台
    '600036.SH',  # 招商银行
    '601318.SH',  # 中国平安
    '600900.SH',  # 长江电力
    '000001.SZ',  # 平安银行
    '300750.SZ',  # 宁德时代
    '002594.SZ',  # 比亚迪
    '300059.SZ',  # 东方财富
    '601888.SH',  # 中国中免
    '000002.SZ',  # 万科A
    '600016.SH',  # 民生银行
    '600000.SH',  # 浦发银行
    '601166.SH',  # 兴业银行
    '600030.SH',  # 中信证券
    '000858.SZ',  # 五粮液
]

def analyze():
    print("=" * 50)
    print("开盘后股票分析")
    print("=" * 50)
    
    data_source = AKShareDataSource()
    analyzer = SignalAnalyzer()
    
    results = []
    
    for code in STOCK_POOL:
        try:
            # 获取最近60天数据
            df = data_source.get_daily_data(code, start_date='20250101')
            if df is None or len(df) < 20:
                continue
            
            # 分析 - 返回DataFrame
            df_analyzed = analyzer.analyze(df)
            
            # 获取最后一行数据
            latest = df_analyzed.iloc[-1]
            
            results.append({
                'code': code,
                'name': data_source.get_stock_info(code).get('name', code),
                'close': latest['close'],
                'buy_score': int(latest.get('BUY_SCORE', 0)),
                'sell_score': int(latest.get('SELL_SCORE', 0)),
                'signal': latest.get('SIGNAL', 'HOLD'),
                'rsi': latest.get('RSI', 'N/A'),
                'macd_hist': latest.get('MACD_HIST', 0),
            })
        except Exception as e:
            print(f"分析 {code} 失败: {e}")
    
    # 按买入评分排序
    results.sort(key=lambda x: (x['buy_score'], x['close']), reverse=True)
    
    # 打印结果
    print("\n【强力建议买入】TOP 10:")
    print("-" * 60)
    buy_count = 0
    for r in results:
        if r['buy_score'] >= 3 and buy_count < 10:
            print(f"{buy_count+1}. {r['name']} ({r['code']})")
            print(f"   收盘: {r['close']:.2f} | 买入: {r['buy_score']}/3 | 卖出: {r['sell_score']}/3")
            print(f"   信号: {r['signal']} | RSI: {r['rsi']}")
            print()
            buy_count += 1
    
    if buy_count == 0:
        print("今日无强力买入信号，以下为推荐关注：")
        for i, r in enumerate(results[:5], 1):
            print(f"{i}. {r['name']} ({r['code']}) - 收盘: {r['close']:.2f}")
    
    return results[:10]

if __name__ == '__main__':
    analyze()
