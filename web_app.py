"""
股票分析系统 - 网页应用界面
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_source import YFinanceDataSource
from analysis import SignalAnalyzer
from chart import plot_stock_analysis, plot_signal_summary
from config import INDICATORS, SIGNAL_CONFIG

# 页面配置
st.set_page_config(
    page_title="股票技术分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
st.title("📈 股票技术分析与买卖指导系统")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("设置")

    # 股票代码输入
    stock_code = st.text_input(
        "股票代码",
        value="AAPL",
        help="美股：AAPL, TSLA, NVDA 等\nA股：000001.SZ, 600519.SH 等"
    )

    # 日期范围选择
    end_date = st.date_input(
        "结束日期",
        value=datetime.now()
    )

    start_date = st.date_input(
        "开始日期",
        value=end_date - timedelta(days=365)
    )

    # 指标参数调整
    st.subheader("指标参数")
    ma_short = st.number_input("MA短期周期", value=5, min_value=1, max_value=200)
    ma_medium = st.number_input("MA中期周期", value=20, min_value=1, max_value=200)
    ma_long = st.number_input("MA长期周期", value=60, min_value=1, max_value=200)

    rsi_period = st.number_input("RSI周期", value=14, min_value=1, max_value=100)

    macd_fast = st.number_input("MACD快线周期", value=12, min_value=1, max_value=200)
    macd_slow = st.number_input("MACD慢线周期", value=26, min_value=1, max_value=200)
    macd_signal = st.number_input("MACD信号线周期", value=9, min_value=1, max_value=200)

    # 信号阈值
    st.subheader("信号阈值")
    buy_threshold = st.slider("买入信号阈值", 0, 10, 5)
    sell_threshold = st.slider("卖出信号阈值", 0, 10, 5)

    # 分析按钮
    analyze_button = st.button("开始分析", type="primary", use_container_width=True)

# 主内容区
if analyze_button or 'df' not in st.session_state:
    with st.spinner("正在获取数据并分析..."):
        try:
            # 获取数据
            data_source = YFinanceDataSource()

            # 更新指标参数
            INDICATORS["MA"]["short_period"] = ma_short
            INDICATORS["MA"]["medium_period"] = ma_medium
            INDICATORS["MA"]["long_period"] = ma_long
            INDICATORS["RSI"]["period"] = rsi_period
            INDICATORS["MACD"]["fast_period"] = macd_fast
            INDICATORS["MACD"]["slow_period"] = macd_slow
            INDICATORS["MACD"]["signal_period"] = macd_signal
            SIGNAL_CONFIG["BUY_THRESHOLD"] = buy_threshold
            SIGNAL_CONFIG["SELL_THRESHOLD"] = sell_threshold

            # 获取股票数据
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            df = data_source.get_daily_data(stock_code, start_str, end_str)

            if df.empty:
                st.error(f"未获取到股票 {stock_code} 的数据，请检查股票代码是否正确")
            else:
                # 获取股票信息
                stock_info = data_source.get_stock_info(stock_code)
                stock_name = stock_info.get('name', stock_code)

                # 技术分析
                analyzer = SignalAnalyzer()
                df = analyzer.analyze(df)

                # 保存到 session state
                st.session_state['df'] = df
                st.session_state['stock_name'] = stock_name
                st.session_state['stock_code'] = stock_code
                st.session_state['stock_info'] = stock_info

        except Exception as e:
            st.error(f"分析失败: {e}")

# 显示分析结果
if 'df' in st.session_state:
    df = st.session_state['df']
    stock_name = st.session_state['stock_name']
    stock_code = st.session_state['stock_code']
    stock_info = st.session_state['stock_info']

    # 最新数据
    latest = df.iloc[-1]

    # 基本信息
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("股票名称", stock_name)
    with col2:
        st.metric("收盘价", f"{latest['close']:.2f}")
    with col3:
        st.metric("最高价", f"{latest['high']:.2f}")
    with col4:
        st.metric("最低价", f"{latest['low']:.2f}")
    with col5:
        volume = latest.get('vol', latest.get('volume', 0))
        st.metric("成交量", f"{volume:,.0f}")

    st.markdown("---")

    # 技术指标
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 技术指标分析")

        # MA
        st.write("**移动平均线 (MA)**")
        ma_status = "多头排列" if latest['MA_SHORT'] > latest['MA_MEDIUM'] > latest['MA_LONG'] else "空头排列"
        st.info(f"MA5: {latest['MA_SHORT']:.2f} | MA20: {latest['MA_MEDIUM']:.2f} | MA60: {latest['MA_LONG']:.2f}")
        st.caption(f"趋势: {ma_status}")

        # RSI
        st.write("**相对强弱指数 (RSI)**")
        rsi_value = latest['RSI']
        if rsi_value > 70:
            st.warning(f"RSI: {rsi_value:.2f} - 超买")
        elif rsi_value < 30:
            st.success(f"RSI: {rsi_value:.2f} - 超卖")
        else:
            st.info(f"RSI: {rsi_value:.2f}")

        # MACD
        st.write("**MACD**")
        macd_status = "多头" if latest['MACD'] > 0 else "空头"
        st.info(f"MACD: {latest['MACD']:.4f} | Signal: {latest['MACD_SIGNAL']:.4f}")
        st.caption(f"趋势: {macd_status}")

        # KDJ
        st.write("**KDJ**")
        st.info(f"K: {latest['KDJ_K']:.2f} | D: {latest['KDJ_D']:.2f} | J: {latest['KDJ_J']:.2f}")

    with col2:
        st.subheader("🎯 综合评分")

        buy_score = latest.get('BUY_SCORE', 0)
        sell_score = latest.get('SELL_SCORE', 0)
        signal = latest.get('SIGNAL', 'HOLD')

        # 买入评分
        st.write("**买入信号评分**")
        st.progress(buy_score / 10)
        st.caption(f"{buy_score} / {buy_threshold}")

        # 卖出评分
        st.write("**卖出信号评分**")
        st.progress(sell_score / 10)
        st.caption(f"{sell_score} / {sell_threshold}")

        # 操作建议
        st.write("**操作建议**")
        if signal == 'BUY':
            st.success("🟢 强烈建议买入 - 多个买入指标出现")
        elif signal == 'SELL':
            st.error("🔴 强烈建议卖出 - 多个卖出指标出现")
        else:
            st.info("🟡 建议持有 - 当前无明显买卖信号")

    st.markdown("---")

    # 数据表格
    st.subheader("📋 历史数据")
    display_cols = ['trade_date', 'close', 'high', 'low', 'vol',
                   'MA_SHORT', 'MA_MEDIUM', 'MA_LONG', 'RSI', 'MACD', 'SIGNAL']

    # 检查哪些列存在
    available_cols = [col for col in display_cols if col in df.columns or col in ['vol', 'volume']]

    # 处理 vol/volume 列
    df_display = df.copy()
    if 'vol' in df_display.columns:
        df_display = df_display.rename(columns={'vol': '成交量'})
    if 'volume' in df_display.columns and '成交量' not in df_display.columns:
        df_display = df_display = df_display.rename(columns={'volume': '成交量'})

    # 选择要显示的列
    display_map = {
        'trade_date': '日期',
        'close': '收盘价',
        'high': '最高价',
        'low': '最低价',
        'vol': '成交量',
        'MA_SHORT': 'MA5',
        'MA_MEDIUM': 'MA20',
        'MA_LONG': 'MA60',
        'RSI': 'RSI',
        'MACD': 'MACD',
        'SIGNAL': '信号'
    }

    show_cols = []
    for col in ['trade_date', 'close', 'high', 'low', '成交量', 'MA_SHORT', 'MA_MEDIUM', 'MA_LONG', 'RSI', 'SIGNAL']:
        if col in df_display.columns or col == '成交量':
            if col == '成交量':
                if 'vol' in df_display.columns:
                    show_cols.append('vol')
                elif 'volume' in df_display.columns:
                    show_cols.append('volume')
            else:
                show_cols.append(col)

    # 显示最近30条数据
    st.dataframe(df_display[show_cols].tail(30).iloc[::-1], use_container_width=True)

    # 下载按钮
    csv = df_display.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="下载完整数据 (CSV)",
        data=csv,
        file_name=f"{stock_code}_analysis.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # 图表
    st.subheader("📈 技术分析图表")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**价格走势与均线**")

        # 创建图表
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(10, 5))
        dates = pd.to_datetime(df['trade_date'], format='%Y%m%d')

        ax.plot(dates, df['close'], label='收盘价', color='green', linewidth=1.5)
        ax.plot(dates, df['MA_SHORT'], label=f'MA{ma_short}', color='red', linewidth=1, alpha=0.7)
        ax.plot(dates, df['MA_MEDIUM'], label=f'MA{ma_medium}', color='blue', linewidth=1, alpha=0.7)
        ax.plot(dates, df['MA_LONG'], label=f'MA{ma_long}', color='purple', linewidth=1, alpha=0.7)

        # 标记买卖点
        buy_points = df[df['SIGNAL'] == 'BUY']
        sell_points = df[df['SIGNAL'] == 'SELL']

        if not buy_points.empty:
            buy_dates = pd.to_datetime(buy_points['trade_date'], format='%Y%m%d')
            ax.scatter(buy_dates, buy_points['close'], marker='^', color='green', s=100, label='买入', zorder=5)

        if not sell_points.empty:
            sell_dates = pd.to_datetime(sell_points['trade_date'], format='%Y%m%d')
            ax.scatter(sell_dates, sell_points['close'], marker='v', color='red', s=100, label='卖出', zorder=5)

        ax.set_ylabel('价格')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close()

    with col2:
        st.write("**MACD**")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), height_ratios=[2, 1])

        # MACD线
        ax1.plot(dates, df['MACD'], label='MACD', color='blue', linewidth=1)
        ax1.plot(dates, df['MACD_SIGNAL'], label='Signal', color='red', linewidth=1)

        colors = ['green' if x > 0 else 'red' for x in df['MACD_HIST']]
        ax2.bar(dates, df['MACD_HIST'], color=colors, alpha=0.3)

        ax1.set_ylabel('MACD')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax2.set_ylabel('柱状图')
        ax2.grid(True, alpha=0.3)

        for ax in [ax1, ax2]:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # RSI 和 KDJ
    col1, col2 = st.columns(2)

    with col1:
        st.write("**RSI**")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, df['RSI'], label='RSI', color='purple', linewidth=1.5)
        ax.axhline(y=70, color='red', linestyle='--', linewidth=0.8, label='超买线')
        ax.axhline(y=30, color='green', linestyle='--', linewidth=0.8, label='超卖线')
        ax.set_ylim(0, 100)
        ax.set_ylabel('RSI')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.write("**KDJ**")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, df['KDJ_K'], label='K', color='red', linewidth=1)
        ax.plot(dates, df['KDJ_D'], label='D', color='blue', linewidth=1)
        ax.plot(dates, df['KDJ_J'], label='J', color='green', linewidth=1, alpha=0.7)
        ax.axhline(y=80, color='red', linestyle='--', linewidth=0.8)
        ax.axhline(y=20, color='green', linestyle='--', linewidth=0.8)
        ax.set_ylabel('KDJ')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # 风险提示
    st.markdown("---")
    st.warning("⚠️ 风险提示：技术分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
