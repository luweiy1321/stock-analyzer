"""
技术指标基类
"""
from abc import ABC, abstractmethod
import pandas as pd
from utils.logger import setup_logger

logger = setup_logger("indicator")


class BaseIndicator(ABC):
    """技术指标基类"""

    def __init__(self, name: str):
        """
        初始化技术指标

        Args:
            name: 指标名称
        """
        self.name = name

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            添加了技术指标列的 DataFrame
        """
        pass

    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据指标生成交易信号

        Args:
            df: 包含指标数据的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        pass
