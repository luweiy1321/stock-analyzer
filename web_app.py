"""
股票分析系统 - 网页应用界面 (优化版)
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_source import YFinanceDataSource, AKShareDataSource
from analysis import SignalAnalyzer
from chart import plot_stock_analysis, plot_signal_summary
from config import INDICATORS, SIGNAL_CONFIG, WATCHLIST, DEFAULT_STOCK_CODE

# 页面配置
st.set_page_config(
    page_title="股票技术分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS - 夜间模式优化
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .main-title { font-size: 2rem; font-weight: bold; color: #ff4b4b; text-align: center; padding: 1rem; }
    .signal-buy { background-color: #28a745; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: bold; }
    .signal-sell { background-color: #dc3545; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: bold; }
    .signal-hold { background-color: #ffc107; color: black; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 股票技术分析与买卖指导系统</p>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 数据源选择
    data_source = st.radio("数据源", ["AKShare (A股)", "YFinance (美股)"], horizontal=True)
    
    # 股票代码输入
    stock_code = st.text_input("股票代码", value=DEFAULT_STOCK_CODE, 
                                help="A股：000001.SZ, 600519.SH\n美股：AAPL, TSLA, NVDA")
    
    # 快速选择自选股
    st.subheader("⭐ 自选股")
    selected_watchlist = st.selectbox("快速选择", [""] + WATCHLIST)
    if selected_watchlist:
        stock_code = selected_watchlist
    
    # 日期范围
    st.subheader("📅 日期范围")
    end_date = st.date_input("结束日期", value=datetime.now())
    start_date = st.date_input("开始日期", value=end_date - timedelta(days=365))
    
    # 指标参数
    st.subheader("📊 指标参数")
    col1, col2 = st.columns(2)
    with col1:
        ma_short = st.number_input("MA短期", value=5, min_value=1, max_value=200)
        rsi_period = st.number_input("RSI周期", value=14, min_value=1, max_value=100)
    with col2:
        ma_medium = st.number_input("MA中期", value=20, min_value=1, max_value=200)
        macd_fast = st.number_input("MACD快线", value=12, min_value=1, max_value=200)
    
    # 信号阈值
    st.subheader("🎯 信号阈值")
    buy_threshold = st.slider("买入阈值", 0, 10, 3)
    sell_threshold = st.slider("卖出阈值", 0, 10, 3)
    
    # 自动刷新
    st.subheader("🔄 自动刷新")
    auto_refresh = st.checkbox("开启自动刷新", value=False)
    if auto_refresh:
        refresh_interval = st.slider("刷新间隔(秒)", 30, 300, 60)
    
    analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

# 主内容区
if analyze_button or 'df' not in st.session_state:
    with st.spinner("正在获取数据并分析..."):
        try:
            if "A股" in data_source:
                data_source_obj = AKShareDataSource()
            else:
                data_source_obj = YFinanceDataSource()
            
            df = data_source_obj.get_daily_data(stock_code, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            
            if df is None or df.empty:
                st.error(f"❌ 无法获取 {stock_code} 的数据，请检查股票代码是否正确")
                st.stop()
            
            st.session_state.df = df
            st.session_state.stock_code = stock_code
            
            from indicators import MAIndicator, RSIIndicator, MACDIndicator, KDJIndicator
            from indicators.boll import BOLLIndicator
            
            ma_indicator = MAIndicator(short_period=ma_short, medium_period=ma_medium)
            df = ma_indicator.calculate(df)
            
            rsi_indicator = RSIIndicator(period=rsi_period)
            df = rsi_indicator.calculate(df)
            
            macd_indicator = MACDIndicator(fast_period=macd_fast)
            df = macd_indicator.calculate(df)
            
            kdj_indicator = KDJIndicator()
            df = kdj_indicator.calculate(df)
            
            boll_indicator = BOLLIndicator()
            df = boll_indicator.calculate(df)
            
            analyzer = SignalAnalyzer(buy_threshold=buy_threshold, sell_threshold=sell_threshold)
            signals = analyzer.analyze(df)
            
            st.session_state.signals = signals
            st.session_state.boll_signals = boll_indicator.get_signals(df)
            
        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
            st.stop()

if 'df' in st.session_state:
    df = st.session_state.df
    stock_code = st.session_state.stock_code
    signals = st.session_state.get('signals', {})
    boll_signals = st.session_state.get('boll_signals', {})
    
    st.subheader("🎯 交易建议")
    
    signal_color = "green" if signals.get("overall_signal") == "BUY" else "red" if signals.get("overall_signal") == "SELL" else "yellow"
    signal_text = "买入" if signals.get("overall_signal") == "BUY" else "卖出" if signals.get("overall_signal") == "SELL" else "持有"
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latest = df.iloc[-1]
        st.metric("当前价格", f"{latest.get('close', 0):.2f}", 
                  f"{latest.get('pct_change', 0):.2f}%")
    with col2:
        buy_score = signals.get("buy_score", 0)
        st.metric("买入评分", f"{buy_score}/10", 
                  delta="🟢 买入" if buy_score >= 3 else None)
    with col3:
        sell_score = signals.get("sell_score", 0)
        st.metric("卖出评分", f"{sell_score}/10",
                  delta="🔴 卖出" if sell_score >= 3 else None)
    with col4:
        trend = signals.get("trend", "未知")
        st.metric("趋势判断", trend)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background-color: #{signal_color}; 
                border-radius: 0.5rem; margin: 1rem 0;">
        <h2>📊 综合建议: {signal_text}</h2>
        <p>{signals.get("summary", "暂无建议")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 技术指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ma_info = signals.get("ma_signal", {})
        st.info(f"MA信号: {ma_info.get('signal', 'N/A')}")
    with col2:
        rsi_info = signals.get("rsi_signal", {})
        st.info(f"RSI: {rsi_info.get('rsi', 0):.1f}")
    with col3:
        macd_info = signals.get("macd_signal", {})
        st.info(f"MACD: {macd_info.get('signal', 'N/A')}")
    with col4:
        kdj_info = signals.get("kdj_signal", {})
        st.info(f"KDJ: {kdj_info.get('signal', 'N/A')}")
    
    if boll_signals:
        st.subheader("📈 布林带")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("上轨", f"{boll_signals.get('upper', 0):.2f}")
        with col2:
            st.metric("中轨", f"{boll_signals.get('mid', 0):.2f}")
        with col3:
            st.metric("下轨", f"{boll_signals.get('lower', 0):.2f}")
        
        if boll_signals.get('signals'):
            for s in boll_signals['signals']:
                if s['severity'] == 'BUY':
                    st.success(f"🟢 {s['message']}")
                elif s['severity'] == 'SELL':
                    st.warning(f"🔴 {s['message']}")
    
    st.subheader("📉 技术分析图表")
    try:
        chart_fig = plot_stock_analysis(df, stock_code)
        st.plotly_chart(chart_fig, use_container_width=True)
    except Exception as e:
        st.error(f"图表生成失败: {str(e)}")
    
    with st.expander("📋 详细数据"):
        st.dataframe(df.tail(30), use_container_width=True)
    
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()

st.markdown("---")
st.caption("⚠️ 风险提示：本系统仅供学习交流，不构成投资建议，投资有风险，入市需谨慎")
