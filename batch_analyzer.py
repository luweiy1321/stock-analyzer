"""
批量股票分析器 - 自动分类买卖建议
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_source import YFinanceDataSource
from analysis import SignalAnalyzer
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

# 预定义股票池
STOCK_POOL = {
    # A股 - 热门银行
    '000001.SZ': '平安银行',
    '600036.SH': '招商银行',
    '601166.SH': '兴业银行',
    '601318.SH': '中国平安',
    '601398.SH': '工商银行',
    '601939.SH': '建设银行',

    # A股 - 科技
    '300750.SZ': '宁德时代',
    '002475.SZ': '立讯精密',
    '002594.SZ': '比亚迪',
    '600276.SH': '恒瑞医药',

    # A股 - 白马股
    '600519.SH': '贵州茅台',
    '000858.SZ': '五粮液',
    '600887.SH': '伊利股份',
    '002304.SZ': '洋河股份',

    # 美股 - 科技
    'AAPL': '苹果',
    'MSFT': '微软',
    'GOOGL': '谷歌',
    'TSLA': '特斯拉',
    'NVDA': '英伟达',
    'META': 'Meta',
    'AMZN': '亚马逊',

    # 美股 - 其他
    'BABA': '阿里巴巴',
    'JD': '京东',
    'PDD': '拼多多',
}


def analyze_batch(stock_list: Dict[str, str] = None) -> Dict:
    """
    批量分析股票

    Args:
        stock_list: 股票代码到名称的映射

    Returns:
        分类结果
    """
    if stock_list is None:
        stock_list = STOCK_POOL

    data_source = YFinanceDataSource()
    analyzer = SignalAnalyzer()

    # 结果分类
    buy_stocks = []
    sell_stocks = []
    hold_stocks = []
    failed_stocks = []

    # 日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    total = len(stock_list)
    print(f"开始批量分析 {total} 只股票...\n")

    for i, (code, name) in enumerate(stock_list.items(), 1):
        print(f"[{i}/{total}] 分析 {name} ({code})...")

        try:
            # 获取数据
            df = data_source.get_daily_data(code, start_date, end_date)

            if df.empty:
                print(f"  - 跳过：未获取到数据")
                failed_stocks.append({'code': code, 'name': name, 'reason': '无数据'})
                continue

            # 技术分析
            df = analyzer.analyze(df)

            # 获取最新分析结果
            latest = df.iloc[-1]
            signal = latest.get('SIGNAL', 'HOLD')
            buy_score = latest.get('BUY_SCORE', 0)
            sell_score = latest.get('SELL_SCORE', 0)
            price = latest['close']

            stock_info = {
                'code': code,
                'name': name,
                'price': price,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'rsi': latest.get('RSI', 0),
                'ma_trend': '多头' if latest['MA_SHORT'] > latest['MA_MEDIUM'] else '空头',
            }

            # 分类
            if signal == 'BUY':
                buy_stocks.append(stock_info)
                print(f"  -> [买入建议] 买入评分: {buy_score}")
            elif signal == 'SELL':
                sell_stocks.append(stock_info)
                print(f"  -> [卖出建议] 卖出评分: {sell_score}")
            else:
                hold_stocks.append(stock_info)
                print(f"  -> [持有建议] 买入评分: {buy_score}, 卖出评分: {sell_score}")

        except Exception as e:
            print(f"  - 失败: {e}")
            failed_stocks.append({'code': code, 'name': name, 'reason': str(e)})

    return {
        'buy': buy_stocks,
        'sell': sell_stocks,
        'hold': hold_stocks,
        'failed': failed_stocks
    }


def print_report(result: Dict):
    """
    打印分析报告

    Args:
        result: 分析结果
    """
    print("\n" + "=" * 80)
    print("批量股票分析报告")
    print("=" * 80)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 买入建议
    buy_stocks = result['buy']
    print(f"\n【建议买入】({len(buy_stocks)}只)")
    print("-" * 80)
    if buy_stocks:
        for i, stock in enumerate(buy_stocks, 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 买入评分: {stock['buy_score']} | RSI: {stock['rsi']:.2f} | MA趋势: {stock['ma_trend']}")
    else:
        print("暂无")

    # 卖出建议
    sell_stocks = result['sell']
    print(f"\n【建议卖出】({len(sell_stocks)}只)")
    print("-" * 80)
    if sell_stocks:
        for i, stock in enumerate(sell_stocks, 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 卖出评分: {stock['sell_score']} | RSI: {stock['rsi']:.2f} | MA趋势: {stock['ma_trend']}")
    else:
        print("暂无")

    # 持有建议
    hold_stocks = result['hold']
    print(f"\n【建议持有】({len(hold_stocks)}只)")
    print("-" * 80)
    if hold_stocks:
        for i, stock in enumerate(hold_stocks[:10], 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 买入评分: {stock['buy_score']} | 卖出评分: {stock['sell_score']} | RSI: {stock['rsi']:.2f}")
        if len(hold_stocks) > 10:
            print(f"   ... 还有 {len(hold_stocks) - 10} 只")
    else:
        print("暂无")

    # 失败列表
    failed = result['failed']
    if failed:
        print(f"\n【分析失败】({len(failed)}只)")
        print("-" * 80)
        for i, stock in enumerate(failed[:5], 1):
            print(f"{i}. {stock['name']} ({stock['code']}) - {stock['reason']}")
        if len(failed) > 5:
            print(f"   ... 还有 {len(failed) - 5} 只")

    print("\n" + "=" * 80)
    print(f"总计: 成功分析 {len(buy_stocks) + len(sell_stocks) + len(hold_stocks)} 只，失败 {len(failed)} 只")
    print("=" * 80)


def save_report(result: Dict, filename: str = "batch_report.csv"):
    """
    保存报告到 CSV

    Args:
        result: 分析结果
        filename: 文件名
    """
    from config import DATA_DIR

    # 合并所有股票
    all_stocks = []

    for stock in result['buy']:
        all_stocks.append({
            '股票代码': stock['code'],
            '股票名称': stock['name'],
            '建议': '买入',
            '价格': stock['price'],
            '买入评分': stock['buy_score'],
            '卖出评分': 0,
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in result['sell']:
        all_stocks.append({
            '股票代码': stock['code'],
            '股票名称': stock['name'],
            '建议': '卖出',
            '价格': stock['price'],
            '买入评分': 0,
            '卖出评分': stock['sell_score'],
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in result['hold']:
        all_stocks.append({
            '股票代码': stock['code'],
            '股票名称': stock['name'],
            '建议': '持有',
            '价格': stock['price'],
            '买入评分': stock['buy_score'],
            '卖出评分': stock['sell_score'],
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    # 创建 DataFrame 并保存
    df = pd.DataFrame(all_stocks)
    df = df.sort_values(['建议', '买入评分', '卖出评分'], ascending=[True, False, False])
    filepath = DATA_DIR / filename
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"\n报告已保存到: {filepath}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='批量股票分析工具')
    parser.add_argument('--pool', type=str, help='股票池文件')
    parser.add_argument('--save', action='store_true', help='保存报告到 CSV')

    args = parser.parse_args()

    # 分析
    result = analyze_batch()

    # 打印报告
    print_report(result)

    # 保存报告
    if args.save:
        save_report(result)
