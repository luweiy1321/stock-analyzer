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
from data_source import AKShareDataSource
from config import WATCHLIST, DEFAULT_STOCK_CODE, INDICATORS

# 页面配置
st.set_page_config(
    page_title="股票技术分析系统",
    page_icon="📈",
    layout="wide"
)

st.markdown('<p style="font-size:24px;font-weight:bold;color:#ff4b4b;text-align:center;">📈 股票技术分析与买卖指导系统</p>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 股票代码输入
    stock_code = st.text_input("股票代码", value="600519.SH")
    
    # 快速选择自选股
    st.subheader("⭐ 自选股")
    selected_watchlist = st.selectbox("快速选择", [""] + WATCHLIST)
    if selected_watchlist:
        stock_code = selected_watchlist
    
    analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

# 主内容区
if analyze_button or 'df' not in st.session_state:
    with st.spinner("正在获取数据并分析..."):
        try:
            ds = AKShareDataSource()
            df = ds.get_daily_data(stock_code, "2025-01-01", datetime.now().strftime("%Y-%m-%d"))
            
            if df is None or df.empty:
                st.error(f"❌ 无法获取 {stock_code} 的数据")
                st.stop()
            
            st.session_state.df = df
            st.session_state.stock_code = stock_code
            
            # 计算MA
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 计算MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # 计算KDJ
            low14 = df['low'].rolling(window=14).min()
            high14 = df['high'].rolling(window=14).max()
            df['k'] = 100 * (df['close'] - low14) / (high14 - low14)
            df['d'] = df['k'].rolling(window=3).mean()
            df['j'] = 3 * df['k'] - 2 * df['d']
            
            # 计算BOLL
            df['boll_mid'] = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['boll_upper'] = df['boll_mid'] + 2 * std
            df['boll_lower'] = df['boll_mid'] - 2 * std
            
            st.session_state.df = df
            
        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
            st.stop()

if 'df' in st.session_state:
    df = st.session_state.df
    stock_code = st.session_state.stock_code
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # 交易信号判断
    buy_score = 0
    sell_score = 0
    
    # MA信号
    ma_signal = "震荡"
    if latest['ma5'] > latest['ma20'] > latest['ma60']:
        ma_signal = "多头"
        buy_score += 2
    elif latest['ma5'] < latest['ma20'] < latest['ma60']:
        ma_signal = "空头"
        sell_score += 2
    
    # RSI信号
    rsi = latest.get('rsi', 50)
    rsi_signal = "正常"
    if rsi > 70:
        rsi_signal = "超买"
        sell_score += 3
    elif rsi < 30:
        rsi_signal = "超卖"
        buy_score += 3
    
    # MACD信号
    macd_signal = "震荡"
    if latest.get('macd', 0) > latest.get('signal', 0) and prev.get('macd', 0) <= prev.get('signal', 0):
        macd_signal = "金叉"
        buy_score += 3
    elif latest.get('macd', 0) < latest.get('signal', 0) and prev.get('macd', 0) >= prev.get('signal', 0):
        macd_signal = "死叉"
        sell_score += 3
    
    # KDJ信号
    k = latest.get('k', 50)
    kdj_signal = "正常"
    if k > 80:
        kdj_signal = "超买"
        sell_score += 2
    elif k < 20:
        kdj_signal = "超卖"
        buy_score += 2
    
    # 综合建议
    if buy_score > sell_score + 2:
        overall = "🟢 买入"
    elif sell_score > buy_score + 2:
        overall = "🔴 卖出"
    else:
        overall = "🟡 持有"
    
    st.subheader("🎯 交易建议")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("当前价", f"{latest.get('close', 0):.2f}")
    with col2:
        st.metric("买入评分", f"{buy_score}/10", delta="🟢 买入" if buy_score > 3 else None)
    with col3:
        st.metric("卖出评分", f"{sell_score}/10", delta="🔴 卖出" if sell_score > 3 else None)
    with col4:
        st.metric("综合建议", overall)
    
    st.subheader("📊 技术指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"MA: {ma_signal}")
    with col2:
        st.info(f"RSI: {rsi:.1f} ({rsi_signal})")
    with col3:
        st.info(f"MACD: {macd_signal}")
    with col4:
        st.info(f"KDJ: {k:.1f} ({kdj_signal})")
    
    st.subheader("📈 布林带")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("上轨", f"{latest.get('boll_upper', 0):.2f}")
    with col2:
        st.metric("中轨", f"{latest.get('boll_mid', 0):.2f}")
    with col3:
        st.metric("下轨", f"{latest.get('boll_lower', 0):.2f}")
    
    # 图表
    st.subheader("📉 K线图")
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        df_show = df.tail(60)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=('K线', '成交量'))
        
        fig.add_trace(go.Candlestick(
            x=df_show.index,
            open=df_show['open'],
            high=df_show['high'],
            low=df_show['low'],
            close=df_show['close'],
            name='K线'
        ), row=1, col=1)
        
        colors = ['green' if df_show['close'].iloc[i] >= df_show['open'].iloc[i] else 'red' for i in range(len(df_show))]
        fig.add_trace(go.Bar(x=df_show.index, y=df_show['volume'], marker_color=colors, name='成交量'), row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=500, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"图表生成失败: {str(e)}")
    
    with st.expander("📋 详细数据"):
        st.dataframe(df.tail(30))

st.markdown("---")
st.caption("⚠️ 风险提示：本系统仅供学习交流，不构成投资建议")
