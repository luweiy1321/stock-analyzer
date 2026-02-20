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
# 注册地址: https://tushare.pro/
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 默认股票代码（示例：平安银行）
DEFAULT_STOCK_CODE = "000001.SZ"

# 技术分析参数配置
INDICATORS = {
    "MA": {
        "short_period": 5,   # 短期均线
        "medium_period": 20,  # 中期均线
        "long_period": 60    # 长期均线
    },
    "RSI": {
        "period": 14,        # RSI周期
        "overbought": 70,    # 超买阈值
        "oversold": 35       # 超卖阈值 - 调整为35，更容易触发
    },
    "MACD": {
        "fast_period": 12,   # 快线周期
        "slow_period": 26,   # 慢线周期
        "signal_period": 9   # 信号线周期
    },
    "KDJ": {
        "k_period": 9,       # K线周期
        "d_period": 3,       # D线周期
        "j_period": 3,       # J线周期
        "overbought": 80,    # 超买阈值
        "oversold": 25        # 超卖阈值 - 调整为25，更容易触发
    }
}

# 买卖信号策略配置
SIGNAL_CONFIG = {
    # 买入信号权重
    "BUY_CONDITIONS": {
        "MA_CROSS_UP": 3,      # 均线金叉
        "RSI_OVERSOLD": 3,     # RSI超卖
        "MACD_GOLDEN_CROSS": 3, # MACD金叉
        "KDJ_OVERSOLD": 3      # KDJ超卖
    },
    # 卖出信号权重
    "SELL_CONDITIONS": {
        "MA_CROSS_DOWN": 3,    # 均线死叉
        "RSI_OVERBOUGHT": 3,   # RSI超买
        "MACD_DEATH_CROSS": 3, # MACD死叉
        "KDJ_OVERBOUGHT": 3    # KDJ超买
    },
    # 信号阈值 - 降低到3分，更容易触发
    "BUY_THRESHOLD": 3,   # 买入信号总分阈值
    "SELL_THRESHOLD": 3   # 卖出信号总分阈值
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": LOG_DIR / "stock_analyzer.log"
}

# 图表配置
CHART_CONFIG = {
    "figsize": (15, 10),
    "dpi": 100,
    "style": "seaborn-v0_8-darkgrid"
}
