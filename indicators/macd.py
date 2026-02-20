"""
移动平均收敛发散 (MACD) 指标
"""
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator
from config import INDICATORS
from utils.logger import setup_logger

logger = setup_logger("macd_indicator")


class MACD(BaseIndicator):
    """移动平均收敛发散指标"""

    def __init__(self, fast_period: int = None, slow_period: int = None, signal_period: int = None):
        """
        初始化 MACD 指标

        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
        """
        super().__init__("MACD")
        self.fast_period = fast_period or INDICATORS["MACD"]["fast_period"]
        self.slow_period = slow_period or INDICATORS["MACD"]["slow_period"]
        self.signal_period = signal_period or INDICATORS["MACD"]["signal_period"]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 MACD

        Args:
            df: 包含 close 列的 DataFrame

        Returns:
            添加了 MACD 列的 DataFrame
        """
        df = df.copy()

        # 计算 EMA
        ema_fast = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow_period, adjust=False).mean()

        # 计算 MACD 线
        df['MACD'] = ema_fast - ema_slow

        # 计算 DEA 信号线
        df['MACD_SIGNAL'] = df['MACD'].ewm(span=self.signal_period, adjust=False).mean()

        # 计算 MACD 柱状图
        df['MACD_HIST'] = df['MACD'] - df['MACD_SIGNAL']

        logger.debug(f"MACD 指标计算完成，快/慢/信号: {self.fast_period}/{self.slow_period}/{self.signal_period}")
        return df

    def get_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成 MACD 交易信号

        信号规则：
        - 金叉：MACD 上穿信号线 = 买入信号
        - 死叉：MACD 下穿信号线 = 卖出信号

        Args:
            df: 包含 MACD 列的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        df = df.copy()

        # 确保有 MACD 列
        if 'MACD' not in df.columns or 'MACD_SIGNAL' not in df.columns:
            df = self.calculate(df)

        # 计算差值
        df['MACD_DIFF'] = df['MACD'] - df['MACD_SIGNAL']

        # 金叉：MACD 上穿信号线
        df['MACD_GOLDEN_CROSS'] = (
            (df['MACD_DIFF'] > 0) & (df['MACD_DIFF'].shift(1) <= 0)
        ).astype(int)

        # 死叉：MACD 下穿信号线
        df['MACD_DEATH_CROSS'] = (
            (df['MACD_DIFF'] < 0) & (df['MACD_DIFF'].shift(1) >= 0)
        ).astype(int)

        return df

    def get_analysis_text(self, df: pd.DataFrame, index: int = -1) -> str:
        """
        获取 MACD 分析文本

        Args:
            df: 包含 MACD 列的 DataFrame
            index: 分析的索引位置

        Returns:
            分析文本
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        if pd.isna(row['MACD']) or pd.isna(row['MACD_SIGNAL']):
            return "MACD 数据不足"

        macd = row['MACD']
        signal = row['MACD_SIGNAL']
        hist = row['MACD_HIST']

        trend = "多头" if macd > 0 else "空头"
        momentum = "增强" if hist > 0 else "减弱"

        text = f"""
【MACD 分析】
MACD 线: {macd:.4f}
信号线: {signal:.4f}
柱状图: {hist:.4f}
趋势: {trend}
动能: {momentum}
        """

        if row.get('MACD_GOLDEN_CROSS', 0) == 1:
            text += "\n[出现金叉信号(买入参考)]"
        elif row.get('MACD_DEATH_CROSS', 0) == 1:
            text += "\n[出现死叉信号(卖出参考)]"

        return text.strip()
