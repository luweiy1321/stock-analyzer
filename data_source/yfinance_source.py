"""
Yahoo Finance 数据源（免费，不需要 token）
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
from config import DATA_DIR
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YFinanceDataSource:
    """Yahoo Finance 数据源"""

    def __init__(self):
        """初始化 Yahoo Finance 数据源"""
        logger.info("Yahoo Finance 数据源初始化成功（无需 token）")

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码以匹配 Yahoo Finance 格式

        Args:
            symbol: 原始股票代码

        Returns:
            转换后的股票代码
        """
        # Yahoo Finance 格式：
        # - 上交所：.SS (如 600519.SS)
        # - 深交所：.SZ (如 000001.SZ)
        # - 美股：直接代码 (如 AAPL)

        if '.SH' in symbol:
            # 将 .SH 转换为 .SS
            return symbol.replace('.SH', '.SS')
        return symbol

    def get_daily_data(self, symbol: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            symbol: 股票代码，如 '000001.SZ' (A股) 或 'AAPL' (美股)
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'

        Returns:
            日线数据 DataFrame
        """
        try:
            # 转换股票代码格式
            yf_symbol = self._convert_symbol(symbol)

            # 默认获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            logger.info(f"正在获取 {symbol} 的数据 ({start_date} ~ {end_date})...")

            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return df

            # 转换为标准格式
            df = df.reset_index()
            df.columns = df.columns.str.lower()

            # 重命名列以匹配系统格式
            column_map = {
                'adj close': 'adj_close',
            }
            df = df.rename(columns=column_map)

            # 保留必要的列
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]

            # 转换日期格式
            df['trade_date'] = df['date'].dt.strftime('%Y%m%d')

            logger.info(f"获取 {symbol} 日线数据成功，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 日线数据失败: {e}")
            raise

    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票信息

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            # 转换股票代码格式
            yf_symbol = self._convert_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            return {
                'name': info.get('longName', symbol),
                'symbol': symbol,
                'industry': info.get('industry', ''),
                'sector': info.get('sector', ''),
                'market_cap': info.get('marketCap', 0),
            }
        except Exception as e:
            logger.error(f"获取 {symbol} 信息失败: {e}")
            return {'name': symbol, 'symbol': symbol}

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


# 预定义的一些热门股票代码
STOCK_SYMBOLS = {
    # A股（通过 Yahoo Finance）
    '000001.SZ': {'name': '平安银行', 'exchange': 'SZSE'},
    '000002.SZ': {'name': '万科A', 'exchange': 'SZSE'},
    '600519.SH': {'name': '贵州茅台', 'exchange': 'SSE'},
    '600036.SH': {'name': '招商银行', 'exchange': 'SSE'},
    '300750.SZ': {'name': '宁德时代', 'exchange': 'SZSE'},

    # 美股
    'AAPL': {'name': 'Apple Inc.', 'exchange': 'NASDAQ'},
    'MSFT': {'name': 'Microsoft Corporation', 'exchange': 'NASDAQ'},
    'GOOGL': {'name': 'Alphabet Inc.', 'exchange': 'NASDAQ'},
    'TSLA': {'name': 'Tesla, Inc.', 'exchange': 'NASDAQ'},
    'NVDA': {'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
}
