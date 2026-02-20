"""
相对强弱指数 (RSI) 指标
"""
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator
from config import INDICATORS
from utils.logger import setup_logger

logger = setup_logger("rsi_indicator")


class RelativeStrengthIndex(BaseIndicator):
    """相对强弱指数指标"""

    def __init__(self, period: int = None, overbought: int = None, oversold: int = None):
        """
        初始化 RSI 指标

        Args:
            period: RSI 周期
            overbought: 超买阈值
            oversold: 超卖阈值
        """
        super().__init__("RSI")
        self.period = period or INDICATORS["RSI"]["period"]
        self.overbought = overbought or INDICATORS["RSI"]["overbought"]
        self.oversold = oversold or INDICATORS["RSI"]["oversold"]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 RSI

        Args:
            df: 包含 close 列的 DataFrame

        Returns:
            添加了 RSI 列的 DataFrame
        """
        df = df.copy()

        # 计算价格变化
        delta = df['close'].diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()

        # 计算相对强度
        rs = avg_gain / avg_loss

        # 计算 RSI
        df['RSI'] = 100 - (100 / (1 + rs))

        logger.debug(f"RSI 指标计算完成，周期: {self.period}")
        return df

    def get_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成 RSI 交易信号

        信号规则：
        - RSI < 30: 超卖 = 买入信号
        - RSI > 70: 超买 = 卖出信号

        Args:
            df: 包含 RSI 列的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        df = df.copy()

        # 确保有 RSI 列
        if 'RSI' not in df.columns:
            df = self.calculate(df)

        # 超卖信号
        df['RSI_OVERSOLD'] = (df['RSI'] < self.oversold).astype(int)

        # 超买信号
        df['RSI_OVERBOUGHT'] = (df['RSI'] > self.overbought).astype(int)

        return df

    def get_analysis_text(self, df: pd.DataFrame, index: int = -1) -> str:
        """
        获取 RSI 分析文本

        Args:
            df: 包含 RSI 列的 DataFrame
            index: 分析的索引位置

        Returns:
            分析文本
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        if pd.isna(row['RSI']):
            return "RSI 数据不足"

        rsi_value = row['RSI']

        text = f"""
【RSI 分析】
当前 RSI 值: {rsi_value:.2f}
超买阈值: {self.overbought}
超卖阈值: {self.oversold}
        """

        if rsi_value > self.overbought:
            text += f"\n[RSI超买] 价格可能回调(卖出参考)"
        elif rsi_value < self.oversold:
            text += f"\n[RSI超卖] 价格可能反弹(买入参考)"
        elif rsi_value > 50:
            text += f"\n[RSI>50] 多头占优"
        else:
            text += f"\n[RSI<50] 空头占优"

        return text.strip()
