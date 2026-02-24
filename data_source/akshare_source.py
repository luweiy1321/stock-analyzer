"""
AKShare 数据源（免费，实时 A 股数据）
"""
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Optional
from config import DATA_DIR
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AKShareDataSource:
    """AKShare 数据源 - 专门针对 A 股的实时数据"""

    def __init__(self):
        """初始化 AKShare 数据源"""
        logger.info("AKShare 数据源初始化成功（免费，A 股实时数据）")

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码以匹配 AKShare 格式

        Args:
            symbol: 原始股票代码 (如 '000001.SZ', '600519.SH')

        Returns:
            AKShare 格式代码 (如 'sz000001', 'sh600519')
        """
        # AKShare 格式：
        # - 深交所：sz + 6位代码 (如 sz000001)
        # - 上交所：sh + 6位代码 (如 sh600519)

        if '.SZ' in symbol:
            code = symbol.replace('.SZ', '').replace('.', '')
            return f"sz{code}"
        elif '.SH' in symbol:
            code = symbol.replace('.SH', '').replace('.', '')
            return f"sh{code}"
        else:
            # 如果没有后缀，尝试自动判断
            code = symbol.replace('.', '')
            if code.startswith('6'):
                return f"sh{code}"
            else:
                return f"sz{code}"

    def _convert_symbol_back(self, ak_symbol: str) -> str:
        """
        将 AKShare 格式转换回标准格式

        Args:
            ak_symbol: AKShare 格式代码 (如 'sz000001', 'sh600519')

        Returns:
            标准格式代码 (如 '000001.SZ', '600519.SH')
        """
        if ak_symbol.startswith('sz'):
            code = ak_symbol[2:]
            return f"{code}.SZ"
        elif ak_symbol.startswith('sh'):
            code = ak_symbol[2:]
            return f"{code}.SH"
        return ak_symbol

    def get_daily_data(self, symbol: str, start_date: str = None,
                      end_date: str = None, adjust: str = 'qfq') -> pd.DataFrame:
        """
        获取日线数据（支持前后复权）

        Args:
            symbol: 股票代码，如 '000001.SZ' (A股)
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            adjust: 复权类型 'qfq'-前复权, 'hfq'-后复权, ''-不复权

        Returns:
            日线数据 DataFrame
        """
        try:
            # 转换股票代码格式
            ak_symbol = self._convert_symbol(symbol)

            # 默认获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            else:
                end_date = end_date.replace('-', '')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            else:
                start_date = start_date.replace('-', '')

            logger.info(f"正在获取 {symbol} 的数据 ({start_date} ~ {end_date})...")

            # 使用 AKShare 获取股票数据
            try:
                # 尝试使用 stock_zh_a_hist 方法（推荐）
                df = ak.stock_zh_a_hist(
                    symbol=ak_symbol[2:],  # 去掉 sh/sz 前缀
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
            except Exception as e:
                # 如果失败，尝试旧版接口
                logger.warning(f"新接口失败，尝试旧接口: {e}")
                df = ak.stock_zh_a_daily(
                    symbol=ak_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )

            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return df

            # 转换为标准格式
            # AKShare 返回的列名可能是中文，需要转换
            column_map = {
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover',
            }

            # 检查是否有英文列名（新版接口）
            if 'date' in df.columns or 'Date' in df.columns:
                df.columns = df.columns.str.lower()
                column_map = {
                    'date': 'date',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume',
                }

            df = df.rename(columns=column_map)

            # 确保日期是 datetime 格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            # 保留必要的列
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            existing_cols = [col for col in required_cols if col in df.columns]
            df = df[existing_cols]

            # 转换日期格式
            df['trade_date'] = df['date'].dt.strftime('%Y%m%d')

            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)

            logger.info(f"获取 {symbol} 日线数据成功，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 日线数据失败: {e}")
            raise

    def get_intraday_data(self, symbol: str) -> pd.DataFrame:
        """
        获取分时数据（当天实时）

        Args:
            symbol: 股票代码，如 '000001.SZ'

        Returns:
            分时数据 DataFrame
        """
        try:
            ak_symbol = self._convert_symbol(symbol)
            code = ak_symbol[2:]  # 去掉 sh/sz 前缀
            logger.info(f"正在获取 {symbol} 的分时数据...")

            # 获取分时数据
            df = ak.stock_zh_a_hist_min_em(symbol=code, period='1', adjust='')

            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的分时数据")
                return df

            # 转换列名
            column_map = {
                '时间': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '时间': 'datetime',
            }

            # 检查是否有英文列名（新版接口）
            if 'datetime' in df.columns or 'DateTime' in df.columns:
                df.columns = df.columns.str.lower()

            df = df.rename(columns=column_map)

            # 确保日期是 datetime 格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'datetime' in df.columns:
                df['date'] = pd.to_datetime(df['datetime'])

            # 保留必要的列
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            existing_cols = [col for col in required_cols if col in df.columns]
            df = df[existing_cols]

            # 转换日期格式
            df['trade_date'] = df['date'].dt.strftime('%Y%m%d')

            # 按时间排序
            df = df.sort_values('date').reset_index(drop=True)

            logger.info(f"获取 {symbol} 分时数据成功，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 分时数据失败: {e}")
            return pd.DataFrame()

    def get_realtime_data(self, symbol: str) -> pd.DataFrame:
        """
        获取实时行情数据

        Args:
            symbol: 股票代码，如 '000001.SZ'

        Returns:
            实时数据 DataFrame
        """
        try:
            ak_symbol = self._convert_symbol(symbol)
            logger.info(f"正在获取 {symbol} 的实时数据...")

            # 获取实时行情
            df = ak.stock_zh_a_spot_em()

            # 筛选目标股票
            stock_df = df[df['代码'] == ak_symbol[2:]]  # 去掉 sh/sz 前缀

            if stock_df.empty:
                logger.warning(f"未获取到股票 {symbol} 的实时数据")
                return stock_df

            # 转换列名
            column_map = {
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'prev_close',
                '换手率': 'turnover',
                '市盈率-动态': 'pe_ttm',
            }

            stock_df = stock_df.rename(columns=column_map)

            logger.info(f"获取 {symbol} 实时数据成功")
            return stock_df

        except Exception as e:
            logger.error(f"获取 {symbol} 实时数据失败: {e}")
            return pd.DataFrame()

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
            code = ak_symbol[2:]  # 去掉 sh/sz 前缀

            # 获取股票基本信息
            info_df = ak.stock_individual_info_em(symbol=code)

            if info_df.empty:
                return {'name': symbol, 'symbol': symbol}

            # 转换为字典
            info_dict = {}
            for _, row in info_df.iterrows():
                if len(row) >= 2:
                    key = str(row.iloc[0]).strip()
                    value = str(row.iloc[1]).strip()
                    info_dict[key] = value

            return {
                'name': info_dict.get('股票简称', symbol),
                'symbol': symbol,
                'industry': info_dict.get('行业', ''),
                'market_cap': info_dict.get('总市值', 0),
            }
        except Exception as e:
            logger.error(f"获取 {symbol} 信息失败: {e}")
            return {'name': symbol, 'symbol': symbol}

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取 A 股所有股票列表

        Returns:
            股票列表 DataFrame
        """
        try:
            logger.info("正在获取 A 股股票列表...")
            df = ak.stock_zh_a_spot_em()
            logger.info(f"获取 A 股股票列表成功，共 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取 A 股股票列表失败: {e}")
            return pd.DataFrame()

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
    '000001.SZ': {'name': '平安银行', 'exchange': 'SZSE'},
    '000002.SZ': {'name': '万科A', 'exchange': 'SZSE'},
    '600519.SH': {'name': '贵州茅台', 'exchange': 'SSE'},
    '600036.SH': {'name': '招商银行', 'exchange': 'SSE'},
    '300750.SZ': {'name': '宁德时代', 'exchange': 'SZSE'},
}
