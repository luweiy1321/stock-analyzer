"""
Tushare 数据源模块
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from config import TUSHARE_TOKEN, DATA_DIR
from utils.logger import setup_logger

logger = setup_logger("data_source")


class TushareDataSource:
    """Tushare 数据源"""

    def __init__(self, token: Optional[str] = None):
        """
        初始化 Tushare 数据源

        Args:
            token: Tushare API token，如果不提供则从配置读取
        """
        self.token = token or TUSHARE_TOKEN
        if not self.token:
            raise ValueError("请先设置 TUSHARE_TOKEN，注册地址: https://tushare.pro/")

        ts.set_token(self.token)
        self.pro = ts.pro_api()
        logger.info("Tushare 数据源初始化成功")

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            股票列表 DataFrame
        """
        try:
            df = self.pro.stock_basic(exchange='', list_status='L',
                                     fields='ts_code,symbol,name,area,industry,list_date')
            logger.info(f"获取股票列表成功，共 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    def get_daily_data(self, ts_code: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            ts_code: 股票代码，如 '000001.SZ'
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'

        Returns:
            日线数据 DataFrame
        """
        try:
            # 默认获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df.empty:
                logger.warning(f"未获取到股票 {ts_code} 的数据")
                return df

            # 按日期排序
            df = df.sort_values('trade_date').reset_index(drop=True)
            logger.info(f"获取 {ts_code} 日线数据成功，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {ts_code} 日线数据失败: {e}")
            raise

    def get_stock_basic(self, ts_code: str) -> dict:
        """
        获取股票基本信息

        Args:
            ts_code: 股票代码

        Returns:
            股票基本信息字典
        """
        try:
            df = self.pro.stock_basic(ts_code=ts_code)
            if not df.empty:
                return df.iloc[0].to_dict()
            return {}
        except Exception as e:
            logger.error(f"获取 {ts_code} 基本信息失败: {e}")
            return {}

    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """
        保存数据到 CSV 文件

        Args:
            df: 要保存的数据
            filename: 文件名
        """
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到 {filepath}")

    def load_from_csv(self, filename: str) -> pd.DataFrame:
        """
        从 CSV 文件加载数据

        Args:
            filename: 文件名

        Returns:
            数据 DataFrame
        """
        filepath = DATA_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            logger.info(f"从 {filepath} 加载数据成功")
            return df
        logger.warning(f"文件 {filepath} 不存在")
        return pd.DataFrame()
