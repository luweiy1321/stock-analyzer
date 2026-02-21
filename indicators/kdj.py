"""
随机指标 (KDJ)
"""
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator
from config import INDICATORS
from utils.logger import setup_logger

logger = setup_logger("kdj_indicator")


class KDJ(BaseIndicator):
    """随机指标 KDJ"""

    def __init__(self, k_period: int = None, d_period: int = None, j_period: int = None):
        """
        初始化 KDJ 指标

        Args:
            k_period: K 线周期
            d_period: D 线周期
            j_period: J 线周期
        """
        super().__init__("KDJ")
        self.k_period = k_period or INDICATORS["KDJ"]["k_period"]
        self.d_period = d_period or INDICATORS["KDJ"]["d_period"]
        self.j_period = j_period or INDICATORS["KDJ"]["j_period"]
        self.overbought = INDICATORS["KDJ"].get("overbought", 80)
        self.oversold = INDICATORS["KDJ"].get("oversold", 20)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 KDJ

        Args:
            df: 包含 high、low、close 列的 DataFrame

        Returns:
            添加了 KDJ 列的 DataFrame
        """
        df = df.copy()

        # 计算最高价和最低价
        high = df['high'].rolling(window=self.k_period).max()
        low = df['low'].rolling(window=self.k_period).min()

        # 计算 RSV
        rsv = (df['close'] - low) / (high - low) * 100

        # 计算 K、D、J
        df['KDJ_K'] = rsv.ewm(com=2, adjust=False).mean()
        df['KDJ_D'] = df['KDJ_K'].ewm(com=2, adjust=False).mean()
        df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']

        logger.debug(f"KDJ 指标计算完成，K/D/J 周期: {self.k_period}/{self.d_period}/{self.j_period}")
        return df

    def get_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成 KDJ 交易信号

        信号规则：
        - K < oversold: 超卖 = 买入信号
        - K > overbought: 超买 = 卖出信号

        Args:
            df: 包含 KDJ 列的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        df = df.copy()

        # 确保有 KDJ 列
        if 'KDJ_K' not in df.columns:
            df = self.calculate(df)

        # 超卖信号
        df['KDJ_OVERSOLD'] = (df['KDJ_K'] < self.oversold).astype(int)

        # 超买信号
        df['KDJ_OVERBOUGHT'] = (df['KDJ_K'] > self.overbought).astype(int)

        # KD 金叉
        df['KDJ_KD_GOLDEN_CROSS'] = (
            (df['KDJ_K'] > df['KDJ_D']) & (df['KDJ_K'].shift(1) <= df['KDJ_D'].shift(1))
        ).astype(int)

        # KD 死叉
        df['KDJ_KD_DEATH_CROSS'] = (
            (df['KDJ_K'] < df['KDJ_D']) & (df['KDJ_K'].shift(1) >= df['KDJ_D'].shift(1))
        ).astype(int)

        return df

    def get_analysis_text(self, df: pd.DataFrame, index: int = -1) -> str:
        """
        获取 KDJ 分析文本

        Args:
            df: 包含 KDJ 列的 DataFrame
            index: 分析的索引位置

        Returns:
            分析文本
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        if pd.isna(row['KDJ_K']) or pd.isna(row['KDJ_D']):
            return "KDJ 数据不足"

        k = row['KDJ_K']
        d = row['KDJ_D']
        j = row['KDJ_J']

        text = f"""
【KDJ 分析】
K 值: {k:.2f}
D 值: {d:.2f}
J 值: {j:.2f}
        """

        if k > self.overbought:
            text += f"\n[K值超买] 价格可能回调(卖出参考)"
        elif k < self.oversold:
            text += f"\n[K值超卖] 价格可能反弹(买入参考)"

        if row.get('KDJ_KD_GOLDEN_CROSS', 0) == 1:
            text += "\n[K线上穿D线(金叉)]"
        elif row.get('KDJ_KD_DEATH_CROSS', 0) == 1:
            text += "\n[K线下穿D线(死叉)]"

        return text.strip()
