"""
股票分析系统 - 主入口
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data_source import TushareDataSource, YFinanceDataSource
from analysis import SignalAnalyzer
from chart import plot_stock_analysis, plot_signal_summary
from config import DEFAULT_STOCK_CODE
from utils.logger import setup_logger

logger = setup_logger("main")


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        [股票技术分析与买卖指导系统]                          ║
║                                                           ║
║        支持指标: MA, RSI, MACD, KDJ                      ║
║        数据来源: Yahoo Finance (免费)                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def analyze_stock(stock_code: str, start_date: str = None, end_date: str = None, use_tushare: bool = False):
    """
    分析单只股票

    Args:
        stock_code: 股票代码，如 'AAPL' (美股) 或 '000001.SZ' (A股)
        start_date: 开始日期
        end_date: 结束日期
        use_tushare: 是否使用 Tushare 数据源（默认使用 Yahoo Finance）
    """
    logger.info(f"开始分析股票: {stock_code}")

    try:
        # 1. 获取数据 - 默认使用 Yahoo Finance
        if use_tushare:
            print("\n[使用 Tushare 数据源...]")
            data_source = TushareDataSource()
            df = data_source.get_daily_data(stock_code, start_date, end_date)
            stock_info = data_source.get_stock_basic(stock_code)
            stock_name = stock_info.get('name', stock_code)
        else:
            print("\n[使用 Yahoo Finance 数据源...]")
            data_source = YFinanceDataSource()
            df = data_source.get_daily_data(stock_code, start_date, end_date)
            stock_info = data_source.get_stock_info(stock_code)
            stock_name = stock_info.get('name', stock_code)

        if df.empty:
            print(f"\n[ERROR] 未获取到股票 {stock_code} 的数据，请检查股票代码是否正确")
            return

        print(f"\n[获取到 {len(df)} 条交易数据]")
        print(f"[日期范围: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}]")

        # 2. 技术分析
        analyzer = SignalAnalyzer()
        df = analyzer.analyze(df)

        # 3. 显示分析报告
        report = analyzer.get_analysis_report(df)
        print(report)

        # 4. 显示最近的买卖信号
        recent_signals = analyzer.get_recent_signals(df, days=10)
        if recent_signals:
            print("\n\n[最近买卖信号]:")
            print("-" * 60)
            for sig in recent_signals:
                signal_text = "[买入]" if sig['signal'] == 'BUY' else "[卖出]"
                print(f"{signal_text} | 日期: {sig['date']} | 价格: {sig['price']:.2f} | "
                      f"买入评分: {sig['buy_score']} | 卖出评分: {sig['sell_score']}")

        # 5. 生成图表
        print("\n[正在生成分析图表...]")
        plot_stock_analysis(df, stock_name=stock_name, save=True)
        plot_signal_summary(df, stock_name=stock_name, save=True)

        # 6. 保存分析结果
        from config import DATA_DIR
        output_file = DATA_DIR / f"{stock_code}_analysis.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n[分析结果已保存到: {output_file}]")

    except Exception as e:
        logger.error(f"分析股票时出错: {e}")
        print(f"\n[ERROR] 分析失败: {e}")


def show_help():
    """显示帮助信息"""
    help_text = """
╔═══════════════════════════════════════════════════════════╗
║                       使用说明                             ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  1. 运行分析 (默认使用 Yahoo Finance):                    ║
║     python main.py <股票代码>                            ║
║                                                           ║
║     示例 - 美股 (推荐):                                   ║
║     python main.py AAPL          (苹果)                   ║
║     python main.py TSLA          (特斯拉)                 ║
║     python main.py NVDA          (英伟达)                 ║
║     python main.py MSFT          (微软)                   ║
║     python main.py GOOGL         (谷歌)                   ║
║                                                           ║
║     示例 - A股:                                           ║
║     python main.py 000001.SZ      (平安银行)             ║
║     python main.py 600519.SH      (贵州茅台)             ║
║                                                           ║
║  2. 使用 Tushare 数据源 (需要 token):                    ║
║     python main.py <股票代码> --tushare                   ║
║                                                           ║
║  3. 指定日期范围:                                         ║
║     python main.py AAPL 2024-01-01 2024-12-31           ║
║                                                           ║
║  4. 交互模式:                                             ║
║     python main.py                                        ║
║                                                           ║
║  股票代码格式:                                            ║
║  - 美股: 直接输入代码 (AAPL, TSLA, MSFT 等)             ║
║  - 深交所: 000xxx.SZ, 300xxx.SZ                         ║
║  - 上交所: 600xxx.SH, 688xxx.SH                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(help_text)


def interactive_mode():
    """交互模式"""
    print("\n[进入交互模式 (输入 'q' 退出)]")
    print("-" * 60)

    analyzer = SignalAnalyzer()

    while True:
        try:
            stock_code = input("\n请输入股票代码 (如 AAPL, TSLA, 000001.SZ): ").strip()

            if not stock_code:
                continue

            if stock_code.lower() in ['q', 'quit', 'exit']:
                print("\n[再见！]")
                break

            # 询问使用哪个数据源
            use_tushare = False
            choice = input("使用哪个数据源? [1] Yahoo Finance (免费) [2] Tushare (需token) [默认:1]: ").strip()
            if choice == '2':
                use_tushare = True

            print(f"\n[正在分析 {stock_code}...]")
            analyze_stock(stock_code, use_tushare=use_tushare)

        except KeyboardInterrupt:
            print("\n\n[再见！]")
            break
        except Exception as e:
            print(f"[错误: {e}]")


def main():
    """主函数"""
    print_banner()

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_help()
            return

        # 检查是否使用 Tushare 数据源
        use_tushare = '--tushare' in sys.argv

        # 分析指定股票
        stock_code = sys.argv[1]
        start_date = None
        end_date = None

        # 跳过 --tushare 参数，获取日期参数
        for i, arg in enumerate(sys.argv[2:], start=2):
            if arg == '--tushare':
                continue
            if start_date is None:
                start_date = arg
            elif end_date is None:
                end_date = arg

        analyze_stock(stock_code, start_date, end_date, use_tushare)
    else:
        # 交互模式
        show_help()
        interactive_mode()


if __name__ == "__main__":
    main()
