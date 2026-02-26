"""
股票分析系统 - 网页应用界面
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from datetime import timedelta

from data_source import AKShareDataSource

# 自选股文件路径
WATCHLIST_FILE = Path(__file__).parent / "data"
WATCHLIST_FILE.mkdir(parents=True, exist_ok=True)

# 默认自选股
DEFAULT_WATCHLIST = ["000001", "600519", "600036", "600900", "601318", "300750", "300059", "600410", "002185", "002009"]

# 股票代码自动加后缀
STOCK_MARKET_MAP = {
    "600000": "SH", "600036": "SH", "600519": "SH", "600900": "SH", "600410": "SH", "601318": "SH", "601888": "SH", "600016": "SH", "600030": "SH", "600031": "SH", "600887": "SH", "688981": "SH", "688111": "SH", "688036": "SH", "688008": "SH", "688005": "SH", "688399": "SH", "688001": "SH", "688169": "SH", "688328": "SH", "688027": "SH", "688066": "SH", "000001": "SZ", "000002": "SZ", "000063": "SZ", "000333": "SZ", "000651": "SZ", "000858": "SZ", "000725": "SZ", "300750": "SZ", "300059": "SZ", "300015": "SZ", "300033": "SZ", "300122": "SZ", "300124": "SZ", "300347": "SZ", "300308": "SZ", "300364": "SZ", "300251": "SZ", "300666": "SZ", "002594": "SZ", "002475": "SZ", "002185": "SZ", "002009": "SZ", "002230": "SZ", "002050": "SZ", "002027": "SZ", "002044": "SZ", "002371": "SZ", "002415": "SZ", "002049": "SZ", "002456": "SZ", "002736": "SZ",
}

def detect_market(code):
    code = code.strip().upper().replace(".SH", "").replace(".SZ", "")
    if code in STOCK_MARKET_MAP:
        return code + "." + STOCK_MARKET_MAP[code]
    if code.startswith("6") or code.startswith("688"):
        return code + ".SH"
    return code + ".SZ"

# 页面配置
st.set_page_config(page_title="股票技术分析系统", page_icon="📈", layout="wide")
st.markdown('<p style="font-size:24px;font-weight:bold;color:#ff4b4b;text-align:center;">📈 股票技术分析与买卖指导系统</p>', unsafe_allow_html=True)
st.markdown("---")

def load_watchlist():
    f = WATCHLIST_FILE / "watchlist.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return DEFAULT_WATCHLIST.copy()

def save_watchlist(watchlist):
    f = WATCHLIST_FILE / "watchlist.json"
    f.write_text(json.dumps(watchlist, ensure_ascii=False, indent=2))

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    
    watchlist = load_watchlist()
    
    st.subheader("➕ 添加股票")
    new_stock = st.text_input("输入股票代码", placeholder="如: 600519")
    if st.button("添加"):
        if new_stock and new_stock not in watchlist:
            watchlist.append(new_stock)
            save_watchlist(watchlist)
            st.success(f"已添加 {detect_market(new_stock)}")
            st.rerun()
    
    st.subheader("🗑️ 删除股票")
    stock_to_delete = st.selectbox("选择删除", [""] + watchlist)
    if st.button("删除"):
        if stock_to_delete and stock_to_delete in watchlist:
            watchlist.remove(stock_to_delete)
            save_watchlist(watchlist)
            st.rerun()
    
    st.subheader("📊 选择股票")
    stock_code = st.selectbox("自选股", watchlist)
    st.subheader("📅 日期范围")
    end_date = st.date_input("结束日期", value=datetime.now(), key="end")
    start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=365), key="start")
    
    manual_input = st.text_input("手动输入", placeholder="如: 600519")
    if manual_input:
        stock_code = manual_input
    
    st.markdown("---")
    st.subheader("📐 指标参数")
    col1, col2 = st.columns(2)
    with col1:
        ma_short = st.number_input("MA短期", 1, 200, 5)
        rsi_period = st.number_input("RSI周期", 1, 100, 14)
    with col2:
        ma_long = st.number_input("MA长期", 1, 200, 60)
        macd_fast = st.number_input("MACD快线", 1, 50, 12)
    
    st.subheader("🎯 信号阈值")
    buy_threshold = st.slider("买入阈值", 0, 10, 3)
    sell_threshold = st.slider("卖出阈值", 0, 10, 3)
    
    analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

# 主内容区
if analyze_button or ('df' not in st.session_state and 'stock_code' in locals()):
    if 'stock_code' not in locals() or not stock_code:
        stock_code = "600519"
    
    full_code = detect_market(stock_code)
    
    with st.spinner("正在获取数据并分析..."):
        try:
            ds = AKShareDataSource()
            df = ds.get_daily_data(full_code, "str(start_date)", datetime.now().strftime("%Y-%m-%d"))
            
            if df is None or df.empty:
                st.error(f"❌ 无法获取 {full_code} 的数据")
                st.stop()
            
            # 计算MA
            df['ma5'] = df['close'].rolling(window=ma_short).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=ma_long).mean()
            
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 计算MACD
            exp1 = df['close'].ewm(span=macd_fast, adjust=False).mean()
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
            st.session_state.stock_code = stock_code
            st.session_state.full_code = full_code
            
        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
            st.stop()

if 'df' in st.session_state:
    df = st.session_state.df
    full_code = st.session_state.get('full_code', '')
    latest = df.iloc[-1]
    
    buy_score = 0
    sell_score = 0
    
    ma_signal = "震荡"
    if latest['ma5'] > latest['ma20'] > latest['ma60']:
        ma_signal = "多头"
        buy_score += 2
    elif latest['ma5'] < latest['ma20'] < latest['ma60']:
        ma_signal = "空头"
        sell_score += 2
    
    rsi = latest.get('rsi', 50)
    rsi_signal = "正常"
    if rsi > 70:
        rsi_signal = "超买"
        sell_score += 3
    elif rsi < 30:
        rsi_signal = "超卖"
        buy_score += 3
    
    macd_signal = "震荡"
    if latest.get('macd', 0) > latest.get('signal', 0):
        macd_signal = "多头"
        buy_score += 1
    else:
        macd_signal = "空头"
        sell_score += 1
    
    k = latest.get('k', 50)
    kdj_signal = "正常"
    if k > 80:
        kdj_signal = "超买"
        sell_score += 2
    elif k < 20:
        kdj_signal = "超卖"
        buy_score += 2
    
    if buy_score > sell_threshold + 2:
        overall = "🟢 买入"
    elif sell_score > buy_threshold + 2:
        overall = "🔴 卖出"
    else:
        overall = "🟡 持有"
    
    st.subheader(f"🎯 {full_code} 交易建议")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("当前价", f"{latest.get('close', 0):.2f}")
    with col2: st.metric("买入评分", f"{buy_score}/10", delta="🟢 买入" if buy_score > buy_threshold else None)
    with col3: st.metric("卖出评分", f"{sell_score}/10", delta="🔴 卖出" if sell_threshold > buy_threshold else None)
    with col4: st.metric("综合建议", overall)
    
    st.subheader("📊 技术指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info(f"MA: {ma_signal}")
    with col2: st.info(f"RSI: {rsi:.1f} ({rsi_signal})")
    with col3: st.info(f"MACD: {macd_signal}")
    with col4: st.info(f"KDJ: {k:.1f} ({kdj_signal})")
    
    st.subheader("📈 布林带")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("上轨", f"{latest.get('boll_upper', 0):.2f}")
    with col2: st.metric("中轨", f"{latest.get('boll_mid', 0):.2f}")
    with col3: st.metric("下轨", f"{latest.get('boll_lower', 0):.2f}")
    
    st.subheader("📉 K线图")
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        df_show = df.tail(60)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        fig.add_trace(go.Candlestick(x=df_show.index, open=df_show['open'], high=df_show['high'], low=df_show['low'], close=df_show['close'], name='K线'), row=1, col=1)
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
