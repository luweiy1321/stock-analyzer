"""
批量股票分析器 - 支持全部A股，使用 AKShare 数据源
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_source import AKShareDataSource
from analysis import SignalAnalyzer
import pandas as pd
from typing import List, Dict, Optional


def get_all_stocks(market: Optional[str] = None) -> Dict[str, str]:
    """
    获取全部 A 股列表

    Args:
        market: 市场筛选，'沪A', '深A', None(全部)

    Returns:
        股票代码到名称的映射
    """
    data_source = AKShareDataSource()
    df = data_source.get_stock_list()

    stock_dict = {}

    for _, row in df.iterrows():
        code = row['code']
        name = row['name']
        stock_dict[code] = name

    if market:
        # 按市场筛选
        market_map = {
            '沪A': '沪A主板',
            '深A': '深A主板',
            '创业板': '创业板',
        }
        if market in market_map:
            df_filtered = df[df['market'].str.contains(market_map[market])]
            stock_dict = {row['code']: row['name'] for _, row in df_filtered.iterrows()}

    return stock_dict


def analyze_batch_stocks(stock_list: Dict[str, str] = None, limit: Optional[int] = None) -> Dict:
    """
    批量分析股票（使用 AKShare）

    Args:
        stock_list: 股票代码到名称的映射，None 表示获取全部
        limit: 限制分析数量，None 表示全部

    Returns:
        分类结果
    """
    if stock_list is None:
        stock_list = get_all_stocks()

    # 限制数量
    if limit and len(stock_list) > limit:
        # 取前 limit 只股票
        stock_list = dict(list(stock_list.items())[:limit])

    data_source = AKShareDataSource()
    analyzer = SignalAnalyzer()

    # 结果分类
    buy_stocks = []
    sell_stocks = []
    hold_stocks = []
    failed_stocks = []

    total = len(stock_list)
    print(f"开始批量分析 {total} 只股票...\\n")

    for i, (code, name) in enumerate(stock_list.items(), 1):
        print(f"[{i}/{total}] 分析 {name} ({code})...", end=' ')

        try:
            # 获取数据
            df = data_source.get_daily_data(code)

            if df.empty:
                print("跳过：未获取到数据")
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
                print(f"-> [买入建议] 买入评分: {buy_score}")
            elif signal == 'SELL':
                sell_stocks.append(stock_info)
                print(f"-> [卖出建议] 卖出评分: {sell_score}")
            else:
                hold_stocks.append(stock_info)
                print(f"-> [持有建议] 买入评分: {buy_score}, 卖出评分: {sell_score}")

        except Exception as e:
            print(f"-> 失败: {e}")
            failed_stocks.append({'code': code, 'name': name, 'reason': str(e)})

    return {
        'buy': buy_stocks,
        'sell': sell_stocks,
        'hold': hold_stocks,
        'failed': failed_stocks
    }


def print_report(result: Dict, show_all: bool = False):
    """
    打印分析报告

    Args:
        result: 分析结果
        show_all: 是否显示全部持有股票
    """
    print("\\n" + "=" * 80)
    print("批量股票分析报告")
    print("=" * 80)
    print(f"分析时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 建议买入
    buy_stocks = result['buy']
    print(f"\\n【建议买入】({len(buy_stocks)}只)")
    print("-" * 80)
    if buy_stocks:
        for i, stock in enumerate(buy_stocks, 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 买入评分: {stock['buy_score']} | RSI: {stock['rsi']:.2f} | MA趋势: {stock['ma_trend']}")
    else:
        print("暂无")

    # 建议卖出
    sell_stocks = result['sell']
    print(f"\\n【建议卖出】({len(sell_stocks)}只)")
    print("-" * 80)
    if sell_stocks:
        for i, stock in enumerate(sell_stocks, 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 卖出评分: {stock['sell_score']} | RSI: {stock['rsi']:.2f} | MA趋势: {stock['ma_trend']}")
    else:
        print("暂无")

    # 建议持有
    hold_stocks = result['hold']
    print(f"\\n【建议持有】({len(hold_stocks)}只)")
    print("-" * 80)

    display_count = len(hold_stocks) if show_all else min(20, len(hold_stocks))

    if hold_stocks:
        for i, stock in enumerate(hold_stocks[:display_count], 1):
            print(f"{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: {stock['price']:.2f} | 买入评分: {stock['buy_score']} | 卖出评分: {stock['sell_score']} | RSI: {stock['rsi']:.2f}")
        if len(hold_stocks) > display_count:
            print(f"   ... 还有 {len(hold_stocks) - display_count} 只")
    else:
        print("暂无")

    # 失败列表
    failed = result['failed']
    if failed:
        print(f"\\n【分析失败】({len(failed)}只)")
        print("-" * 80)
        display_failed = failed[:10] if len(failed) > 10 else failed
        for i, stock in enumerate(display_failed, 1):
            print(f"{i}. {stock['name']} ({stock['code']}) - {stock['reason']}")
        if len(failed) > 10:
            print(f"   ... 还有 {len(failed) - 10} 只")

    print("\\n" + "=" * 80)
    print(f"总计: 成功分析 {len(buy_stocks) + len(sell_stocks) + len(hold_stocks)} 只，失败 {len(failed)} 只")
    print("=" * 80)


def save_report(result: Dict, filename: str = "all_a_stocks.csv"):
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
            '代码': stock['code'],
            '名称': stock['name'],
            '建议': '买入',
            '价格': stock['price'],
            '买入评分': stock['buy_score'],
            '卖出评分': 0,
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in result['sell']:
        all_stocks.append({
            '代码': stock['code'],
            '名称': stock['name'],
            '建议': '卖出',
            '价格': stock['price'],
            '买入评分': 0,
            '卖出评分': stock['sell_score'],
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in result['hold']:
        all_stocks.append({
            '代码': stock['code'],
            '名称': stock['name'],
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
    print(f"\\n报告已保存到: {filepath}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='全部A股票批量分析工具')
    parser.add_argument('--limit', type=int, default=50, help='限制分析数量（默认50只）')
    parser.add_argument('--market', type=str, help='市场筛选：沪A、深A')
    parser.add_argument('--all', action='store_true', help='分析全部股票（可能很慢）')
    parser.add_argument('--show-all', action='store_true', help='显示全部持有股票')
    parser.add_argument('--save', action='store_true', help='保存报告到 CSV')

    args = parser.parse_args()

    # 获取股票列表
    if args.market:
        stock_list = get_all_stocks(market=args.market)
    elif args.all:
        stock_list = get_all_stocks()
    else:
        # 默认分析前 50 只
        stock_list = get_all_stocks()
        stock_list = dict(list(stock_list.items())[:args.limit])

    # 分析
    result = analyze_batch_stocks(stock_list, limit=None if args.all else args.limit)

    # 打印报告
    print_report(result, show_all=args.show_all)

    # 保存报告
    if args.save:
        save_report(result, f"all_a_stocks_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
