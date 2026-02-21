"""
批量股票分析 - 网页应用
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_source import YFinanceDataSource
from analysis import SignalAnalyzer
from config import SIGNAL_CONFIG

# 页面配置
st.set_page_config(
    page_title="批量股票分析",
    page_icon="📊",
    layout="wide"
)

st.title("📊 批量股票分析")
st.markdown("自动分析多只股票，分类显示买卖建议")

# 股票池
STOCK_POOL = {
    # A股 - 银行
    '000001.SZ': '平安银行',
    '600036.SH': '招商银行',
    '601166.SH': '兴业银行',
    '601318.SH': '中国平安',
    '601398.SH': '工商银行',
    '601939.SH': '建设银行',

    # A股 - 科技
    '300750.SZ': '宁德时代',
    '002475.SZ': '立讯精密',
    '002594.SZ': '比亚迪',
    '600276.SH': '恒瑞医药',

    # A股 - 白马股
    '600519.SH': '贵州茅台',
    '000858.SZ': '五粮液',
    '600887.SH': '伊利股份',
    '002304.SZ': '洋河股份',

    # 美股 - 科技
    'AAPL': '苹果',
    'MSFT': '微软',
    'GOOGL': '谷歌',
    'TSLA': '特斯拉',
    'NVDA': '英伟达',
    'META': 'Meta',
    'AMZN': '亚马逊',

    # 美股 - 中概股
    'BABA': '阿里巴巴',
    'JD': '京东',
    'PDD': '拼多多',
}

# 侧边栏设置
with st.sidebar:
    st.header("设置")

    # 信号阈值
    buy_threshold = st.slider("买入信号阈值", 0, 10, 5)
    sell_threshold = st.slider("卖出信号阈值", 0, 10, 5)
    SIGNAL_CONFIG["BUY_THRESHOLD"] = buy_threshold
    SIGNAL_CONFIG["SELL_THRESHOLD"] = sell_threshold

    # 分析按钮
    analyze_button = st.button("开始批量分析", type="primary", use_container_width=True)

    st.markdown("---")
    st.write("**当前股票池**")
    for code, name in STOCK_POOL.items():
        st.write(f"{name} ({code})")

# 主内容区
if analyze_button or 'results' not in st.session_state:
    with st.spinner("正在分析所有股票..."):
        data_source = YFinanceDataSource()
        analyzer = SignalAnalyzer()

        # 结果分类
        buy_stocks = []
        sell_stocks = []
        hold_stocks = []
        failed_stocks = []

        # 日期范围
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        total = len(STOCK_POOL)
        progress_bar = st.progress(0)

        for i, (code, name) in enumerate(STOCK_POOL.items(), 1):
            try:
                # 获取数据
                df = data_source.get_daily_data(code, start_date, end_date)

                if df.empty:
                    failed_stocks.append({'code': code, 'name': name, 'reason': '无数据'})
                    continue

                # 技术分析
                df = analyzer.analyze(df)

                # 获取最新分析结果
                latest = df.iloc[-1]
                signal = latest.get('SIGNAL', 'HOLD')
                buy_score = latest.get('BUY_SCORE', 0)
                sell_score = latest.get('SELL_SCORE', 0)
                price = latest['close']

                stock_info = {
                    'code': code,
                    'name': name,
                    'price': price,
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'rsi': latest.get('RSI', 0),
                    'ma_trend': '多头' if latest['MA_SHORT'] > latest['MA_MEDIUM'] else '空头',
                }

                # 分类
                if signal == 'BUY':
                    buy_stocks.append(stock_info)
                elif signal == 'SELL':
                    sell_stocks.append(stock_info)
                else:
                    hold_stocks.append(stock_info)

            except Exception as e:
                failed_stocks.append({'code': code, 'name': name, 'reason': str(e)})

            progress_bar.progress(i / total)

        progress_bar.empty()

        # 保存到 session state
        st.session_state['results'] = {
            'buy': buy_stocks,
            'sell': sell_stocks,
            'hold': hold_stocks,
            'failed': failed_stocks
        }
        st.session_state['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 显示结果
if 'results' in st.session_state:
    results = st.session_state['results']

    # 统计概览
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("建议买入", len(results['buy']), delta="关注")
    with col2:
        st.metric("建议卖出", len(results['sell']), delta="警惕")
    with col3:
        st.metric("建议持有", len(results['hold']))
    with col4:
        st.metric("分析失败", len(results['failed']))

    st.markdown("---")

    # 建议买入
    st.subheader("🟢 建议买入")
    if results['buy']:
        df_buy = pd.DataFrame(results['buy'])
        st.dataframe(df_buy[['name', 'code', 'price', 'buy_score', 'rsi', 'ma_trend']].rename(columns={
            'name': '名称', 'code': '代码', 'price': '价格',
            'buy_score': '买入评分', 'rsi': 'RSI', 'ma_trend': 'MA趋势'
        }), use_container_width=True)
    else:
        st.info("当前没有建议买入的股票")

    st.markdown("---")

    # 建议卖出
    st.subheader("🔴 建议卖出")
    if results['sell']:
        df_sell = pd.DataFrame(results['sell'])
        st.dataframe(df_sell[['name', 'code', 'price', 'sell_score', 'rsi', 'ma_trend']].rename(columns={
            'name': '名称', 'code': '代码', 'price': '价格',
            'sell_score': '卖出评分', 'rsi': 'RSI', 'ma_trend': 'MA趋势'
        }), use_container_width=True)
    else:
        st.info("当前没有建议卖出的股票")

    st.markdown("---")

    # 建议持有
    st.subheader("🟡 建议持有")
    if results['hold']:
        df_hold = pd.DataFrame(results['hold'])
        st.dataframe(df_hold[['name', 'code', 'price', 'buy_score', 'sell_score', 'rsi', 'ma_trend']].rename(columns={
            'name': '名称', 'code': '代码', 'price': '价格',
            'buy_score': '买入评分', 'sell_score': '卖出评分',
            'rsi': 'RSI', 'ma_trend': 'MA趋势'
        }), use_container_width=True)
    else:
        st.info("当前没有建议持有的股票")

    st.markdown("---")

    # 下载按钮
    col1, col2 = st.columns(2)

    # 合并所有数据
    all_data = []

    for stock in results['buy']:
        all_data.append({
            '名称': stock['name'],
            '代码': stock['code'],
            '建议': '买入',
            '价格': stock['price'],
            '买入评分': stock['buy_score'],
            '卖出评分': 0,
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in results['sell']:
        all_data.append({
            '名称': stock['name'],
            '代码': stock['code'],
            '建议': '卖出',
            '价格': stock['price'],
            '买入评分': 0,
            '卖出评分': stock['sell_score'],
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    for stock in results['hold']:
        all_data.append({
            '名称': stock['name'],
            '代码': stock['code'],
            '建议': '持有',
            '价格': stock['price'],
            '买入评分': stock['buy_score'],
            '卖出评分': stock['sell_score'],
            'RSI': stock['rsi'],
            'MA趋势': stock['ma_trend']
        })

    df_all = pd.DataFrame(all_data)

    with col1:
        csv = df_all.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下载完整报告 (CSV)",
            data=csv,
            file_name=f"batch_report_{st.session_state['timestamp']}.csv",
            mime="text/csv"
        )

    with col2:
        if st.button("重新分析"):
            st.session_state.pop('results', None)
            st.rerun()

    # 更新时间
    st.caption(f"分析时间: {st.session_state['timestamp']}")
else:
    st.info("点击左侧 '开始批量分析' 按钮开始分析")

st.markdown("---")
st.warning("⚠️ 风险提示：技术分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
