"""
AKShare 数据源（免费，支持 A 股）
"""
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Optional
from config import DATA_DIR
from utils.logger import setup_logger

logger = setup_logger("akshare_source")


class AKShareDataSource:
    """AKShare 数据源"""

    def __init__(self):
        """初始化 AKShare 数据源"""
        logger.info("AKShare 数据源初始化成功（免费，支持A股）")

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取 A 股全部股票列表

        Returns:
            股票列表 DataFrame
        """
        try:
            # 获取 A 股实时行情数据
            df = ak.stock_zh_a_spot_em()

            # 转换为标准格式
            result = pd.DataFrame({
                'code': df['代码'],
                'name': df['名称'],
                'price': df['最新价'],
                'change': df['涨跌幅'],
                'volume': df['成交量'],
                'market': df['market']
            })

            logger.info(f"获取到 {len(result)} 只股票")
            return result

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    def get_daily_data(self, symbol: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            symbol: 股票代码，如 'sh600519' 或 'sz000001'
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'

        Returns:
            日线数据 DataFrame
        """
        try:
            # AKShare 格式: sh600519 或 sz000001
            ak_symbol = self._convert_symbol(symbol)
            logger.info(f"正在获取 {symbol} ({ak_symbol}) 的数据...")

            # 默认获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            # 获取 A 股历史数据
            df = ak.stock_zh_a_hist(symbol=ak_symbol, period="daily",
                                    start_date=start_date, end_date=end_date, adjust="qfq")

            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return df

            # 转换为标准格式
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']].copy()
            df.columns = ['trade_date', 'open', 'high', 'low', 'close', 'volume']

            # 确保有必要的列
            df['date'] = pd.to_datetime(df['trade_date'], format='%Y-%m-%d')

            logger.info(f"获取 {symbol} 日线数据成功，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 日线数据失败: {e}")
            raise

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码格式为 AKShare 格式

        Args:
            symbol: 原始代码，如 '600519.SH' 或 '000001.SZ'

        Returns:
            AKShare 格式代码，如 'sh600519' 或 'sz000001'
        """
        symbol = symbol.upper()

        if '.SH' in symbol:
            return symbol.replace('.SH', 'sh').replace('6000', '600')
        elif '.SZ' in symbol:
            return symbol.replace('.SZ', 'sz')
        elif symbol.startswith('60'):
            return 'sh' + symbol
        elif symbol.startswith('00') or symbol.startswith('30'):
            return 'sz' + symbol
        else:
            return symbol

    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票信息

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            ak_symbol = self._convert_symbol(symbol)
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == ak_symbol]

            if not stock_data.empty:
                return {
                    'name': stock_data['名称'].iloc[0],
                    'symbol': symbol,
                    'price': stock_data['最新价'].iloc[0],
                    'market': stock_data['market'].iloc[0],
                }
            else:
                return {'name': symbol, 'symbol': symbol}

        except Exception as e:
            logger.error(f"获取 {symbol} 信息失败: {e}")
            return {'name': symbol, 'symbol': symbol}
