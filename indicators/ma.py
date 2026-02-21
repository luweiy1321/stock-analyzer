"""
移动平均线 (MA) 指标
"""
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator
from config import INDICATORS
from utils.logger import setup_logger

logger = setup_logger("ma_indicator")


class MovingAverage(BaseIndicator):
    """移动平均线指标"""

    def __init__(self, short_period: int = None, medium_period: int = None, long_period: int = None):
        """
        初始化 MA 指标

        Args:
            short_period: 短期均线周期
            medium_period: 中期均线周期
            long_period: 长期均线周期
        """
        super().__init__("MA")
        self.short_period = short_period or INDICATORS["MA"]["short_period"]
        self.medium_period = medium_period or INDICATORS["MA"]["medium_period"]
        self.long_period = long_period or INDICATORS["MA"]["long_period"]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线

        Args:
            df: 包含 close 列的 DataFrame

        Returns:
            添加了 MA 列的 DataFrame
        """
        df = df.copy()

        df['MA_SHORT'] = df['close'].rolling(window=self.short_period).mean()
        df['MA_MEDIUM'] = df['close'].rolling(window=self.medium_period).mean()
        df['MA_LONG'] = df['close'].rolling(window=self.long_period).mean()

        logger.debug(f"MA 指标计算完成，短/中/长期均线: {self.short_period}/{self.medium_period}/{self.long_period}")
        return df

    def get_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成 MA 交易信号

        信号规则：
        - 金叉：短期均线上穿中期均线 = 买入信号
        - 死叉：短期均线下穿中期均线 = 卖出信号

        Args:
            df: 包含 MA 列的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        df = df.copy()

        # 确保有 MA 列
        if 'MA_SHORT' not in df.columns or 'MA_MEDIUM' not in df.columns:
            df = self.calculate(df)

        # 计算金叉和死叉
        df['MA_DIFF'] = df['MA_SHORT'] - df['MA_MEDIUM']

        # 金叉：短期均线上穿中期均线
        df['MA_GOLDEN_CROSS'] = (
            (df['MA_DIFF'] > 0) & (df['MA_DIFF'].shift(1) <= 0)
        ).astype(int)

        # 死叉：短期均线下穿中期均线
        df['MA_DEATH_CROSS'] = (
            (df['MA_DIFF'] < 0) & (df['MA_DIFF'].shift(1) >= 0)
        ).astype(int)

        return df

    def get_analysis_text(self, df: pd.DataFrame, index: int = -1) -> str:
        """
        获取 MA 分析文本

        Args:
            df: 包含 MA 列的 DataFrame
            index: 分析的索引位置

        Returns:
            分析文本
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        if pd.isna(row['MA_SHORT']) or pd.isna(row['MA_MEDIUM']):
            return "MA 数据不足"

        price = row['close']
        ma_short = row['MA_SHORT']
        ma_medium = row['MA_MEDIUM']
        ma_long = row['MA_LONG']

        trend = "多头排列" if ma_short > ma_medium > ma_long else "空头排列"
        position = "上方" if price > ma_short else "下方"

        text = f"""
【MA 均线分析】
当前价格: {price:.2f}
短期均线({self.short_period}): {ma_short:.2f}
中期均线({self.medium_period}): {ma_medium:.2f}
长期均线({self.long_period}): {ma_long:.2f}
均线趋势: {trend}
价格位置: {price:.2f} 位于短期均线{position}
        """

        if row.get('MA_GOLDEN_CROSS', 0) == 1:
            text += "\n[出现金叉信号(买入参考)]"
        elif row.get('MA_DEATH_CROSS', 0) == 1:
            text += "\n[出现死叉信号(卖出参考)]"

        return text.strip()
