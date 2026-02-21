"""
信号分析器
"""
import pandas as pd
from typing import Dict, List, Optional
from indicators import MovingAverage, RelativeStrengthIndex, MACD, KDJ
from config import SIGNAL_CONFIG
from utils.logger import setup_logger

logger = setup_logger("signal_analyzer")


class SignalAnalyzer:
    """买卖信号分析器"""

    def __init__(self):
        """初始化信号分析器"""
        self.ma = MovingAverage()
        self.rsi = RelativeStrengthIndex()
        self.macd = MACD()
        self.kdj = KDJ()
        self.indicators = [self.ma, self.rsi, self.macd, self.kdj]

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        分析股票数据，计算所有指标并生成信号

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            添加了所有指标和信号的 DataFrame
        """
        logger.info("开始分析股票数据...")

        df = df.copy()

        # 计算所有指标
        for indicator in self.indicators:
            df = indicator.calculate(df)
            df = indicator.get_signal(df)

        # 综合评分
        df['BUY_SCORE'] = 0
        df['SELL_SCORE'] = 0

        # 买入条件评分
        buy_conditions = SIGNAL_CONFIG['BUY_CONDITIONS']
        df['BUY_SCORE'] += df.get('MA_GOLDEN_CROSS', 0) * buy_conditions['MA_CROSS_UP']
        df['BUY_SCORE'] += df.get('RSI_OVERSOLD', 0) * buy_conditions['RSI_OVERSOLD']
        df['BUY_SCORE'] += df.get('MACD_GOLDEN_CROSS', 0) * buy_conditions['MACD_GOLDEN_CROSS']
        df['BUY_SCORE'] += df.get('KDJ_OVERSOLD', 0) * buy_conditions['KDJ_OVERSOLD']

        # 卖出条件评分
        sell_conditions = SIGNAL_CONFIG['SELL_CONDITIONS']
        df['SELL_SCORE'] += df.get('MA_DEATH_CROSS', 0) * sell_conditions['MA_CROSS_DOWN']
        df['SELL_SCORE'] += df.get('RSI_OVERBOUGHT', 0) * sell_conditions['RSI_OVERBOUGHT']
        df['SELL_SCORE'] += df.get('MACD_DEATH_CROSS', 0) * sell_conditions['MACD_DEATH_CROSS']
        df['SELL_SCORE'] += df.get('KDJ_OVERBOUGHT', 0) * sell_conditions['KDJ_OVERBOUGHT']

        # 生成最终信号
        df['SIGNAL'] = 'HOLD'  # 持有

        buy_threshold = SIGNAL_CONFIG['BUY_THRESHOLD']
        sell_threshold = SIGNAL_CONFIG['SELL_THRESHOLD']

        df.loc[df['BUY_SCORE'] >= buy_threshold, 'SIGNAL'] = 'BUY'
        df.loc[df['SELL_SCORE'] >= sell_threshold, 'SIGNAL'] = 'SELL'

        logger.info("分析完成")
        return df

    def get_analysis_report(self, df: pd.DataFrame, index: int = -1) -> str:
        """
        获取分析报告

        Args:
            df: 包含指标和信号的 DataFrame
            index: 分析的索引位置

        Returns:
            分析报告文本
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        # 基本信息
        price = row['close']
        high = row['high']
        low = row['low']
        volume = row.get('vol', row.get('volume', 0))
        date = row.get('trade_date', '')

        report = f"""
╔════════════════════════════════════════════════════╗
║           股票技术分析报告                          ║
╠════════════════════════════════════════════════════╣
║  交易日期: {date}
║  收盘价: {price:.2f}
║  最高价: {high:.2f}
║  最低价: {low:.2f}
║  成交量: {volume:,.0f}
╚════════════════════════════════════════════════════╝

"""

        # 各指标分析
        report += self.ma.get_analysis_text(df, index) + "\n\n"
        report += self.rsi.get_analysis_text(df, index) + "\n\n"
        report += self.macd.get_analysis_text(df, index) + "\n\n"
        report += self.kdj.get_analysis_text(df, index) + "\n\n"

        # 综合评分
        buy_score = row.get('BUY_SCORE', 0)
        sell_score = row.get('SELL_SCORE', 0)
        signal = row.get('SIGNAL', 'HOLD')

        report += f"""
╔════════════════════════════════════════════════════╗
║           综合评分与操作建议                        ║
╠════════════════════════════════════════════════════╣
║  买入信号评分: {buy_score} / {SIGNAL_CONFIG['BUY_THRESHOLD']}
║  卖出信号评分: {sell_score} / {SIGNAL_CONFIG['SELL_THRESHOLD']}
╚════════════════════════════════════════════════════╝
"""

        # 最终建议
        if signal == 'BUY':
            report += "\n[强烈建议买入] 多个买入指标出现，关注！"
        elif signal == 'SELL':
            report += "\n[强烈建议卖出] 多个卖出指标出现，注意风险！"
        else:
            report += "\n[建议持有] 当前无明显买卖信号，继续观察"

        report += "\n\n[风险提示] 技术分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"

        return report

    def get_recent_signals(self, df: pd.DataFrame, days: int = 5) -> List[Dict]:
        """
        获取最近的买卖信号

        Args:
            df: 包含信号的 DataFrame
            days: 查看最近多少天的信号

        Returns:
            信号列表
        """
        recent = df.tail(days).copy()

        signals = []
        for idx, row in recent.iterrows():
            if row['SIGNAL'] in ['BUY', 'SELL']:
                signals.append({
                    'date': row.get('trade_date', ''),
                    'signal': row['SIGNAL'],
                    'price': row['close'],
                    'buy_score': row.get('BUY_SCORE', 0),
                    'sell_score': row.get('SELL_SCORE', 0)
                })

        return signals
