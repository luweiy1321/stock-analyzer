"""
图表可视化模块
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import pandas as pd
from datetime import datetime
from config import CHART_CONFIG, DATA_DIR
from utils.logger import setup_logger

logger = setup_logger("chart")


def plot_stock_analysis(df: pd.DataFrame, stock_name: str = "", save: bool = True):
    """
    绘制股票技术分析图表

    Args:
        df: 包含 OHLCV 和指标的 DataFrame
        stock_name: 股票名称
        save: 是否保存图表
    """
    plt.style.use(CHART_CONFIG['style'])

    # 创建图表
    fig = plt.figure(figsize=CHART_CONFIG['figsize'], dpi=CHART_CONFIG['dpi'])
    gs = GridSpec(4, 2, figure=fig, hspace=0.3, wspace=0.2)

    # 日期转换
    df['trade_date_dt'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    dates = mdates.date2num(df['trade_date_dt'])

    # ==================== 主图：价格和均线 ====================
    ax1 = fig.add_subplot(gs[0:2, :])

    # 绘制 K 线（简化为折线）
    ax1.plot(dates, df['close'], label='收盘价', color='#2ecc71', linewidth=1.5)

    # 绘制均线
    if 'MA_SHORT' in df.columns:
        ax1.plot(dates, df['MA_SHORT'], label=f'MA{df["MA_SHORT"].iloc[0]:.0f}',
                color='#e74c3c', linewidth=1, alpha=0.7)
    if 'MA_MEDIUM' in df.columns:
        ax1.plot(dates, df['MA_MEDIUM'], label=f'MA{df["MA_MEDIUM"].iloc[0]:.0f}',
                color='#3498db', linewidth=1, alpha=0.7)
    if 'MA_LONG' in df.columns:
        ax1.plot(dates, df['MA_LONG'], label=f'MA{df["MA_LONG"].iloc[0]:.0f}',
                color='#9b59b6', linewidth=1, alpha=0.7)

    # 标记买卖点
    buy_points = df[df['SIGNAL'] == 'BUY']
    sell_points = df[df['SIGNAL'] == 'SELL']

    if not buy_points.empty:
        buy_dates = mdates.date2num(pd.to_datetime(buy_points['trade_date'], format='%Y%m%d'))
        ax1.scatter(buy_dates, buy_points['close'], marker='^', color='green',
                   s=100, label='买入', zorder=5)

    if not sell_points.empty:
        sell_dates = mdates.date2num(pd.to_datetime(sell_points['trade_date'], format='%Y%m%d'))
        ax1.scatter(sell_dates, sell_points['close'], marker='v', color='red',
                   s=100, label='卖出', zorder=5)

    ax1.set_title(f'{stock_name} 股票技术分析图', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格', fontsize=10)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # ==================== MACD ====================
    ax2 = fig.add_subplot(gs[2, :])

    if 'MACD' in df.columns:
        ax2.plot(dates, df['MACD'], label='MACD', color='#3498db', linewidth=1)
        ax2.plot(dates, df['MACD_SIGNAL'], label='SIGNAL', color='#e74c3c', linewidth=1)

        # 柱状图
        colors = ['green' if x > 0 else 'red' for x in df['MACD_HIST']]
        ax2.bar(dates, df['MACD_HIST'], color=colors, alpha=0.3, label='柱状图')

        ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        ax2.set_ylabel('MACD', fontsize=10)
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)

    # ==================== RSI ====================
    ax3 = fig.add_subplot(gs[3, 0])

    if 'RSI' in df.columns:
        ax3.plot(dates, df['RSI'], label='RSI', color='#9b59b6', linewidth=1)
        ax3.axhline(y=70, color='red', linestyle='--', linewidth=0.8, label='超买线')
        ax3.axhline(y=30, color='green', linestyle='--', linewidth=0.8, label='超卖线')
        ax3.set_ylim(0, 100)
        ax3.set_ylabel('RSI', fontsize=10)
        ax3.legend(loc='upper left', fontsize=8)
        ax3.grid(True, alpha=0.3)

    # ==================== KDJ ====================
    ax4 = fig.add_subplot(gs[3, 1])

    if 'KDJ_K' in df.columns:
        ax4.plot(dates, df['KDJ_K'], label='K', color='#e74c3c', linewidth=1)
        ax4.plot(dates, df['KDJ_D'], label='D', color='#3498db', linewidth=1)
        ax4.plot(dates, df['KDJ_J'], label='J', color='#27ae60', linewidth=1, alpha=0.7)
        ax4.axhline(y=80, color='red', linestyle='--', linewidth=0.8)
        ax4.axhline(y=20, color='green', linestyle='--', linewidth=0.8)
        ax4.set_ylabel('KDJ', fontsize=10)
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3)

    # 统一设置 x 轴日期格式
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=8)

    plt.tight_layout()

    # 保存图表
    if save:
        filename = f"{DATA_DIR}/analysis_chart.png"
        plt.savefig(filename, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        logger.info(f"图表已保存到 {filename}")

    return fig


def plot_signal_summary(df: pd.DataFrame, stock_name: str = "", save: bool = True):
    """
    绘制信号汇总图表

    Args:
        df: 包含信号的 DataFrame
        stock_name: 股票名称
        save: 是否保存图表
    """
    plt.style.use(CHART_CONFIG['style'])
    fig, axes = plt.subplots(2, 1, figsize=(CHART_CONFIG['figsize'][0], 8))

    # 日期转换
    df['trade_date_dt'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    dates = mdates.date2num(df['trade_date_dt'])

    # ==================== 买入评分 ====================
    axes[0].plot(dates, df['BUY_SCORE'], label='买入评分', color='green', linewidth=1.5)
    axes[0].axhline(y=5, color='green', linestyle='--', linewidth=0.8, label='买入阈值')
    axes[0].fill_between(dates, 0, df['BUY_SCORE'], alpha=0.3, color='green')
    axes[0].set_ylabel('评分', fontsize=10)
    axes[0].set_title(f'{stock_name} 买卖信号评分', fontsize=12)
    axes[0].legend(loc='upper left', fontsize=9)
    axes[0].grid(True, alpha=0.3)

    # ==================== 卖出评分 ====================
    axes[1].plot(dates, df['SELL_SCORE'], label='卖出评分', color='red', linewidth=1.5)
    axes[1].axhline(y=5, color='red', linestyle='--', linewidth=0.8, label='卖出阈值')
    axes[1].fill_between(dates, 0, df['SELL_SCORE'], alpha=0.3, color='red')
    axes[1].set_ylabel('评分', fontsize=10)
    axes[1].legend(loc='upper left', fontsize=9)
    axes[1].grid(True, alpha=0.3)

    # 统一设置 x 轴日期格式
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=8)

    plt.tight_layout()

    # 保存图表
    if save:
        filename = f"{DATA_DIR}/signal_summary.png"
        plt.savefig(filename, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        logger.info(f"信号图表已保存到 {filename}")

    return fig
