"""
股票分析系统配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Tushare API 配置（需要注册获取 token）
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 默认股票代码（A股常用）
DEFAULT_STOCK_CODE = "000001.SZ"

# 常用自选股列表
WATCHLIST = [
    "000001.SZ",   # 平安银行
    "000002.SZ",   # 万科A
    "600519.SH",  # 贵州茅台
    "600036.SH",  # 招商银行
    "600900.SH",  # 长江电力
    "601318.SH",  # 中国平安
    "601888.SH",  # 中国中免
    "300750.SZ",  # 宁德时代
    "300059.SZ",  # 东方财富
    "002594.SZ",  # 比亚迪
    "002475.SZ",  # 立讯精密
    "688981.SH",  # 中芯国际
    "002230.SZ",  # 科大讯飞
    "600410.SH",  # 华胜天成
    "002185.SZ",  # 华天科技
]

# 技术分析参数配置
INDICATORS = {
    "MA": {
        "short_period": 5,
        "medium_period": 20,
        "long_period": 60
    },
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    },
    "KDJ": {
        "k_period": 9,
        "d_period": 3,
        "j_period": 3,
        "overbought": 80,
        "oversold": 20
    },
    "BOLL": {
        "period": 20,      # 布林带周期
        "std_dev": 2       # 标准差倍数
    }
}

# 买卖信号策略配置
SIGNAL_CONFIG = {
    "BUY_CONDITIONS": {
        "MA_CROSS_UP": 3,
        "RSI_OVERSOLD": 3,
        "MACD_GOLDEN_CROSS": 3,
        "KDJ_OVERSOLD": 3,
        "BOLL_LOWER": 2    # 触及布林下轨
    },
    "SELL_CONDITIONS": {
        "MA_CROSS_DOWN": 3,
        "RSI_OVERBOUGHT": 3,
        "MACD_DEATH_CROSS": 3,
        "KDJ_OVERBOUGHT": 3,
        "BOLL_UPPER": 2    # 触及布林上轨
    },
    "BUY_THRESHOLD": 3,
    "SELL_THRESHOLD": 3
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": LOG_DIR / "stock_analyzer.log"
}

# 图表配置
CHART_CONFIG = {
    "figsize": (15, 10),
    "dpi": 100,
    "style": "seaborn-v0_8-darkgrid"
}
