"""
实时股票监控 - 单个股票当天行情动态分析与买卖信号提醒
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

from data_source import AKShareDataSource
from analysis import SignalAnalyzer
from config import SIGNAL_CONFIG, INDICATORS

# 自选股票文件路径
WATCHLIST_FILE = Path(__file__).parent / "data" / "watchlist.json"

# 页面配置
st.set_page_config(
    page_title="实时股票监控",
    page_icon="📈",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    /* 信号提醒样式 */
    .signal-buy {
        background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        animation: pulse 2s infinite;
        box-shadow: 0 4px 15px rgba(0, 200, 83, 0.4);
    }
    .signal-sell {
        background: linear-gradient(135deg, #ff1744 0%, #ff5252 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        animation: pulse 2s infinite;
        box-shadow: 0 4px 15px rgba(255, 23, 68, 0.4);
    }
    .signal-hold {
        background: linear-gradient(135deg, #ffc107 0%, #ffca28 100%);
        color: #333;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        color: #6c757d;
    }
    .price-up {
        color: #00c853;
    }
    .price-down {
        color: #ff1744;
    }
</style>
""", unsafe_allow_html=True)

# 密码保护
CORRECT_PASSWORD = "stock2024"

# 初始化登录状态
if 'rt_authenticated' not in st.session_state:
    st.session_state['rt_authenticated'] = False

# 检查是否已登录
if not st.session_state['rt_authenticated']:
    st.title("🔐 登录验证")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("请输入访问密码", type="password", key="rt_login_password")

        if st.button("登录", type="primary", use_container_width=True):
            if password == CORRECT_PASSWORD:
                st.session_state['rt_authenticated'] = True
                st.rerun()
            else:
                st.error("密码错误，请重试")

    st.markdown("---")
    st.caption("💡 这是受保护的内容，需要密码才能访问")
    st.stop()

# 初始化 session state
if 'rt_selected_stock' not in st.session_state:
    st.session_state['rt_selected_stock'] = '000001.SZ'
if 'rt_last_signal' not in st.session_state:
    st.session_state['rt_last_signal'] = None
if 'rt_signal_history' not in st.session_state:
    st.session_state['rt_signal_history'] = []
if 'rt_auto_refresh' not in st.session_state:
    st.session_state['rt_auto_refresh'] = True
if 'rt_refresh_interval' not in st.session_state:
    st.session_state['rt_refresh_interval'] = 30  # 默认30秒
if 'rt_show_alert' not in st.session_state:
    st.session_state['rt_show_alert'] = False
if 'rt_watchlist' not in st.session_state:
    st.session_state['rt_watchlist'] = None


# 默认自选股票列表
DEFAULT_WATCHLIST = {
    '000001.SZ': '平安银行',
    '000002.SZ': '万科A',
    '600519.SH': '贵州茅台',
    '600036.SH': '招商银行',
    '300750.SZ': '宁德时代',
    '600000.SH': '浦发银行',
    '600030.SH': '中信证券',
    '000333.SZ': '美的集团',
    '600690.SH': '海尔智家',
    '002594.SZ': '比亚迪',
    '601318.SH': '中国平安',
    '600276.SH': '恒瑞医药',
    '000858.SZ': '五粮液',
    '600887.SH': '伊利股份',
    '300059.SZ': '东方财富',
}


def load_watchlist():
    """加载自选股票列表"""
    try:
        if WATCHLIST_FILE.exists():
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 确保目录存在
            WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            # 保存默认列表
            save_watchlist(DEFAULT_WATCHLIST)
            return DEFAULT_WATCHLIST.copy()
    except Exception as e:
        st.error(f"加载自选股票列表失败: {e}")
        return DEFAULT_WATCHLIST.copy()


def save_watchlist(watchlist):
    """保存自选股票列表"""
    try:
        WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存自选股票列表失败: {e}")
        return False


def get_stock_name(stock_code, data_source=None):
    """获取股票名称"""
    try:
        if data_source:
            info = data_source.get_stock_info(stock_code)
            return info.get('name', stock_code)
        return stock_code
    except Exception:
        return stock_code


# 加载自选股票列表
if st.session_state['rt_watchlist'] is None:
    st.session_state['rt_watchlist'] = load_watchlist()

# 页面标题
st.title("📈 实时股票监控")

# 顶部导航链接
col1, col2, col3 = st.columns([3, 1, 1])
with col2:
    st.link_button("📊 批量分析", "https://mytool.streamlit.app/", use_container_width=True)
with col3:
    if st.button("🏠 刷新", use_container_width=True):
        st.rerun()

st.markdown("---")

# 侧边栏控制
with st.sidebar:
    st.header("⚙️ 控制面板")

    # 股票选择
    stock_input_method = st.radio("选择股票方式", ["从自选股选择", "手动输入代码"])

    if stock_input_method == "从自选股选择":
        watchlist = st.session_state['rt_watchlist']
        selected_stock = st.selectbox(
            "选择股票",
            options=list(watchlist.keys()),
            format_func=lambda x: f"{watchlist[x]} ({x})",
            index=list(watchlist.keys()).index(st.session_state['rt_selected_stock']) if st.session_state['rt_selected_stock'] in watchlist else 0
        )
    else:
        watchlist = st.session_state['rt_watchlist']
        default_code = st.session_state['rt_selected_stock'] if st.session_state['rt_selected_stock'] not in watchlist else '000001.SZ'
        selected_stock = st.text_input("输入股票代码", value=default_code, placeholder="如: 000001.SZ, 600519.SH")

    if selected_stock != st.session_state['rt_selected_stock']:
        st.session_state['rt_selected_stock'] = selected_stock
        st.session_state['rt_last_signal'] = None
        st.session_state['rt_signal_history'] = []
        st.rerun()

    st.markdown("---")

    # 自选股票管理
    st.header("⭐ 自选股管理")

    with st.expander("添加自选股", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_stock_code = st.text_input("股票代码", placeholder="如: 000001.SZ, 600519.SH", key="add_stock_code")
        with col2:
            new_stock_name = st.text_input("股票名称（可选）", placeholder="如: 平安银行", key="add_stock_name")

        if st.button("➕ 添加到自选", use_container_width=True):
            if new_stock_code:
                watchlist = st.session_state['rt_watchlist']
                if new_stock_code in watchlist:
                    st.warning("⚠️ 该股票已在自选中")
                else:
                    # 如果没有提供名称，尝试自动获取
                    if not new_stock_name:
                        try:
                            temp_source = AKShareDataSource()
                            new_stock_name = get_stock_name(new_stock_code, temp_source)
                        except Exception:
                            new_stock_name = new_stock_code

                    watchlist[new_stock_code] = new_stock_name
                    if save_watchlist(watchlist):
                        st.session_state['rt_watchlist'] = watchlist
                        st.success(f"✅ 已添加: {new_stock_name} ({new_stock_code})")
                        st.rerun()
                    else:
                        st.error("❌ 添加失败")
            else:
                st.warning("⚠️ 请输入股票代码")

    with st.expander("删除自选股", expanded=False):
        watchlist = st.session_state['rt_watchlist']
        if watchlist:
            stock_to_delete = st.selectbox(
                "选择要删除的股票",
                options=list(watchlist.keys()),
                format_func=lambda x: f"{watchlist[x]} ({x})",
                key="delete_stock_select"
            )

            if st.button("🗑️ 删除选中股票", use_container_width=True):
                stock_name = watchlist[stock_to_delete]
                del watchlist[stock_to_delete]
                if save_watchlist(watchlist):
                    st.session_state['rt_watchlist'] = watchlist
                    # 如果删除的是当前选中的股票，切换到第一个
                    if st.session_state['rt_selected_stock'] == stock_to_delete:
                        st.session_state['rt_selected_stock'] = list(watchlist.keys())[0] if watchlist else '000001.SZ'
                    st.success(f"✅ 已删除: {stock_name} ({stock_to_delete})")
                    st.rerun()
                else:
                    st.error("❌ 删除失败")
        else:
            st.info("📋 自选股列表为空")

    st.markdown("---")

    # 自动刷新设置
    st.header("🔄 自动刷新")
    auto_refresh = st.checkbox("启用自动刷新", value=st.session_state['rt_auto_refresh'])
    st.session_state['rt_auto_refresh'] = auto_refresh

    if auto_refresh:
        refresh_interval = st.slider(
            "刷新间隔（秒）",
            min_value=10,
            max_value=300,
            value=st.session_state['rt_refresh_interval'],
            step=10
        )
        st.session_state['rt_refresh_interval'] = refresh_interval
        st.caption(f"⏱️ 每 {refresh_interval} 秒自动刷新一次")

    st.markdown("---")

    # 技术指标参数设置
    st.header("📊 技术指标参数")

    with st.expander("信号阈值"):
        col1, col2 = st.columns(2)
        with col1:
            buy_threshold = st.slider("买入阈值", 1, 10, SIGNAL_CONFIG.get('BUY_THRESHOLD', 3))
        with col2:
            sell_threshold = st.slider("卖出阈值", 1, 10, SIGNAL_CONFIG.get('SELL_THRESHOLD', 3))

    with st.expander("RSI 参数"):
        col1, col2 = st.columns(2)
        with col1:
            rsi_overbought = st.slider("RSI 超买线", 60, 90, INDICATORS['RSI']['overbought'])
        with col2:
            rsi_oversold = st.slider("RSI 超卖线", 10, 50, INDICATORS['RSI']['oversold'])

    with st.expander("KDJ 参数"):
        col1, col2 = st.columns(2)
        with col1:
            kdj_overbought = st.slider("KDJ 超买线", 70, 95, INDICATORS['KDJ']['overbought'])
        with col2:
            kdj_oversold = st.slider("KDJ 超卖线", 5, 40, INDICATORS['KDJ']['oversold'])

    with st.expander("MA 参数"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ma_short = st.slider("短期MA", 3, 15, INDICATORS['MA']['short_period'])
        with col2:
            ma_medium = st.slider("中期MA", 10, 40, INDICATORS['MA']['medium_period'])
        with col3:
            ma_long = st.slider("长期MA", 30, 120, INDICATORS['MA']['long_period'])

    st.markdown("---")

    # 数据周期
    data_days = st.selectbox(
        "历史数据周期（天）",
        options=[30, 60, 90, 180, 365],
        index=3
    )

# 主内容区
stock_code = st.session_state['rt_selected_stock']

# 优先从自选股列表获取名称，否则使用代码本身
watchlist = st.session_state['rt_watchlist']
stock_name = watchlist.get(stock_code, stock_code)

# 显示当前选择的股票
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown(f"### 🎯 当前监控: **{stock_name}** ({stock_code})")
with col2:
    if st.button("🔄 立即刷新", use_container_width=True):
        st.rerun()
with col3:
    last_update = st.session_state.get('rt_last_update', '未更新')
    st.caption(f"最后更新: {last_update}")

st.markdown("---")

# 获取数据和分析
try:
    # 更新参数
    SIGNAL_CONFIG["BUY_THRESHOLD"] = buy_threshold
    SIGNAL_CONFIG["SELL_THRESHOLD"] = sell_threshold
    INDICATORS["RSI"]["overbought"] = rsi_overbought
    INDICATORS["RSI"]["oversold"] = rsi_oversold
    INDICATORS["KDJ"]["overbought"] = kdj_overbought
    INDICATORS["KDJ"]["oversold"] = kdj_oversold
    INDICATORS["MA"]["short_period"] = ma_short
    INDICATORS["MA"]["medium_period"] = ma_medium
    INDICATORS["MA"]["long_period"] = ma_long

    # 获取数据
    data_source = AKShareDataSource()
    analyzer = SignalAnalyzer()

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=data_days)).strftime('%Y-%m-%d')

    with st.spinner("正在获取数据..."):
        df = data_source.get_daily_data(stock_code, start_date, end_date)

    if df.empty:
        st.error(f"❌ 无法获取股票 {stock_code} 的数据，请检查股票代码是否正确")
    else:
        # 技术分析
        df = analyzer.analyze(df)

        # 获取最新数据
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        # 更新最后更新时间
        st.session_state['rt_last_update'] = datetime.now().strftime('%H:%M:%S')

        # 获取当前信号
        current_signal = latest.get('SIGNAL', 'HOLD')
        buy_score = latest.get('BUY_SCORE', 0)
        sell_score = latest.get('SELL_SCORE', 0)

        # 检查信号变化
        signal_changed = False
        if st.session_state['rt_last_signal'] != current_signal:
            signal_changed = True
            st.session_state['rt_last_signal'] = current_signal

            # 记录信号历史
            st.session_state['rt_signal_history'].append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'signal': current_signal,
                'price': latest['close']
            })
            # 保留最近20条记录
            if len(st.session_state['rt_signal_history']) > 20:
                st.session_state['rt_signal_history'].pop(0)

        # 信号提醒（当信号变化时）
        if signal_changed and current_signal in ['BUY', 'SELL']:
            st.session_state['rt_show_alert'] = True

        if st.session_state['rt_show_alert']:
            if current_signal == 'BUY':
                st.markdown(f"""
                <div class="signal-buy">
                    🟢 买入信号！<br>
                    <span style="font-size: 18px;">{stock_name} ({stock_code})</span><br>
                    <span style="font-size: 16px;">当前价格: ¥{latest['close']:.2f} | 买入评分: {buy_score}</span>
                </div>
                """, unsafe_allow_html=True)
            elif current_signal == 'SELL':
                st.markdown(f"""
                <div class="signal-sell">
                    🔴 卖出信号！<br>
                    <span style="font-size: 18px;">{stock_name} ({stock_code})</span><br>
                    <span style="font-size: 16px;">当前价格: ¥{latest['close']:.2f} | 卖出评分: {sell_score}</span>
                </div>
                """, unsafe_allow_html=True)
            elif current_signal == 'HOLD':
                st.markdown(f"""
                <div class="signal-hold">
                    🟡 观望信号<br>
                    <span style="font-size: 16px;">{stock_name} - 当前无明显买卖信号</span>
                </div>
                """, unsafe_allow_html=True)

            if st.button("关闭提醒"):
                st.session_state['rt_show_alert'] = False
                st.rerun()

        # 主要数据展示
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        price_change = latest['close'] - previous['close']
        price_change_pct = (price_change / previous['close']) * 100 if previous['close'] > 0 else 0

        price_color_class = "price-up" if price_change >= 0 else "price-down"
        price_arrow = "↑" if price_change >= 0 else "↓"

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {price_color_class}">¥{latest['close']:.2f}</div>
                <div class="metric-label">当前价</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {price_color_class}">{price_arrow} {abs(price_change):.2f}</div>
                <div class="metric-label">涨跌额</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {price_color_class}">{price_arrow} {abs(price_change_pct):.2f}%</div>
                <div class="metric-label">涨跌幅</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">¥{latest['high']:.2f}</div>
                <div class="metric-label">最高价</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">¥{latest['low']:.2f}</div>
                <div class="metric-label">最低价</div>
            </div>
            """, unsafe_allow_html=True)

        with col6:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{latest['volume']:,.0f}</div>
                <div class="metric-label">成交量</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 技术指标展示
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 技术指标")

            # MA趋势
            ma_trend = "多头排列" if latest['MA_SHORT'] > latest['MA_MEDIUM'] > latest['MA_LONG'] else \
                      "空头排列" if latest['MA_SHORT'] < latest['MA_MEDIUM'] < latest['MA_LONG'] else "震荡"

            # 指标数据
            indicator_data = {
                'MA5': f"{latest['MA_SHORT']:.2f}",
                'MA20': f"{latest['MA_MEDIUM']:.2f}",
                'MA60': f"{latest['MA_LONG']:.2f}",
                'RSI': f"{latest['RSI']:.2f}",
                'MACD': f"{latest['MACD']:.4f}",
                'K': f"{latest['KDJ_K']:.2f}",
                'D': f"{latest['KDJ_D']:.2f}",
                'J': f"{latest['KDJ_J']:.2f}"
            }

            # 创建指标表格
            indicator_df = pd.DataFrame({
                '指标': list(indicator_data.keys()),
                '数值': list(indicator_data.values()),
                '状态': [
                    '短期均线上扬' if latest['MA_SHORT'] > latest['MA_MEDIUM'] else '短期均线下压',
                    '中期均线' if latest['MA_MEDIUM'] > latest['MA_LONG'] else '中期均线',
                    '长期均线' if latest['MA_LONG'] > 0 else '长期均线',
                    '超买' if latest['RSI'] > rsi_overbought else '超卖' if latest['RSI'] < rsi_oversold else '正常',
                    '金叉' if latest['MACD'] > latest['MACD_SIGNAL'] else '死叉',
                    '超买' if latest['KDJ_K'] > kdj_overbought else '超卖' if latest['KDJ_K'] < kdj_oversold else '正常',
                    '超买' if latest['KDJ_D'] > kdj_overbought else '超卖' if latest['KDJ_D'] < kdj_oversold else '正常',
                    '超买' if latest['KDJ_J'] > 100 else '超卖' if latest['KDJ_J'] < 0 else '正常'
                ]
            })
            st.dataframe(indicator_df, hide_index=True, use_container_width=True)

        with col2:
            st.subheader("🎯 信号分析")

            # 信号评分展示
            signal_col1, signal_col2 = st.columns(2)

            with signal_col1:
                # 买入评分
                buy_progress = min(buy_score / buy_threshold * 100, 100) if buy_threshold > 0 else 0
                buy_color = "#00c853" if buy_score >= buy_threshold else "#ffc107"

                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <div style="font-size: 14px; color: #6c757d; margin-bottom: 10px;">买入评分</div>
                    <div style="font-size: 32px; font-weight: bold; color: {buy_color};">{buy_score} / {buy_threshold}</div>
                    <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 10px;">
                        <div style="background: {buy_color}; height: 100%; border-radius: 4px; width: {buy_progress}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with signal_col2:
                # 卖出评分
                sell_progress = min(sell_score / sell_threshold * 100, 100) if sell_threshold > 0 else 0
                sell_color = "#ff1744" if sell_score >= sell_threshold else "#ffc107"

                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <div style="font-size: 14px; color: #6c757d; margin-bottom: 10px;">卖出评分</div>
                    <div style="font-size: 32px; font-weight: bold; color: {sell_color};">{sell_score} / {sell_threshold}</div>
                    <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 10px;">
                        <div style="background: {sell_color}; height: 100%; border-radius: 4px; width: {sell_progress}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 当前建议
            if current_signal == 'BUY':
                st.markdown("""
                <div class="signal-buy" style="font-size: 18px; padding: 15px;">
                    🟢 建议买入
                </div>
                """, unsafe_allow_html=True)
            elif current_signal == 'SELL':
                st.markdown("""
                <div class="signal-sell" style="font-size: 18px; padding: 15px;">
                    🔴 建议卖出
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="signal-hold" style="font-size: 18px; padding: 15px;">
                    🟡 观望
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # K线图和指标图
        st.subheader("📈 价格走势图")

        # 创建子图
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('K线图与均线', 'RSI', 'MACD')
        )

        # K线图
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ), row=1, col=1)

        # 均线
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA_SHORT'],
            name=f'MA{ma_short}',
            line=dict(color='#ff6b6b', width=1)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA_MEDIUM'],
            name=f'MA{ma_medium}',
            line=dict(color='#4ecdc4', width=1)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA_LONG'],
            name=f'MA{ma_long}',
            line=dict(color='#45b7d1', width=1)
        ), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['RSI'],
            name='RSI',
            line=dict(color='#9b59b6', width=2)
        ), row=2, col=1)

        # RSI 超买超卖线
        fig.add_hline(y=rsi_overbought, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=rsi_oversold, line_dash="dash", line_color="green", row=2, col=1)

        # MACD
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD'],
            name='MACD',
            line=dict(color='#3498db', width=2)
        ), row=3, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD_SIGNAL'],
            name='Signal',
            line=dict(color='#e74c3c', width=2)
        ), row=3, col=1)

        # 更新布局
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_dark'
        )

        fig.update_xaxes(title_text="日期", row=3, col=1)
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 信号历史记录
        if st.session_state['rt_signal_history']:
            st.subheader("📜 信号历史")

            history_df = pd.DataFrame(st.session_state['rt_signal_history'])

            def color_signal(val):
                if val == 'BUY':
                    return 'background-color: #00c853; color: white;'
                elif val == 'SELL':
                    return 'background-color: #ff1744; color: white;'
                else:
                    return 'background-color: #ffc107; color: black;'

            st.dataframe(
                history_df,
                column_config={
                    'time': '时间',
                    'signal': '信号',
                    'price': st.column_config.NumberColumn('价格', format='¥%.2f')
                },
                hide_index=True,
                use_container_width=True
            )

except Exception as e:
    st.error(f"❌ 发生错误: {str(e)}")
    st.exception(e)

# 自动刷新逻辑
if st.session_state['rt_auto_refresh']:
    # 显示刷新倒计时
    refresh_interval = st.session_state['rt_refresh_interval']

    # 使用JavaScript定时刷新
    refresh_js = f"""
    <script>
        setTimeout(function() {{
            location.reload();
        }}, {refresh_interval * 1000});
    </script>
    """
    st.components.v1.html(refresh_js, height=0)

    # 显示刷新提示
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"⏱️ 页面将在 {refresh_interval} 秒后自动刷新...")

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 12px;">
    ⚠️ 风险提示: 技术分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。<br>
    数据来源: Yahoo Finance，更新频率受数据源限制。
</div>
""", unsafe_allow_html=True)
