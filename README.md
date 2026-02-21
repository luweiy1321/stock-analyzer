# 📈 股票技术分析与买卖指导系统

一个基于 Python 的股票技术分析系统，使用免费 API 获取 A 股数据，通过多个技术指标（MA、RSI、MACD、KDJ）综合分析，生成买卖信号。

## ✨ 功能特点

- 📊 **多指标分析**: 支持 MA（移动平均线）、RSI（相对强弱指数）、MACD、KDJ 等常用技术指标
- 🎯 **综合信号**: 基于多个指标的综合评分，生成买入/卖出/持有建议
- 📉 **数据可视化**: 自动生成 K 线图、指标图、信号评分图
- 💾 **数据存储**: 支持数据持久化存储，便于历史分析
- 🇨🇳 **A股数据**: 使用 Tushare 免费接口获取沪深股市数据

## 📋 技术指标说明

### MA（移动平均线）
- **短期均线 (MA5)**: 反映短期趋势
- **中期均线 (MA20)**: 反映中期趋势
- **长期均线 (MA60)**: 反映长期趋势
- **信号**: 金叉（买入）、死叉（卖出）

### RSI（相对强弱指数）
- **超买区域**: RSI > 70，价格可能回调
- **超卖区域**: RSI < 30，价格可能反弹
- **阈值**: 可配置

### MACD（移动平均收敛发散）
- **MACD 线**: 快线与慢线的差值
- **信号线**: MACD 的 EMA
- **柱状图**: MACD 与信号线的差值
- **信号**: 金叉、死叉

### KDJ（随机指标）
- **K 值**: 快速随机值
- **D 值**: 慢速随机值
- **J 值**: 超买超卖敏感指标
- **信号**: K > 80 超买、K < 20 超卖

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Windows / Linux / macOS

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Token

本项目使用 Tushare 作为数据源，需要先注册获取 Token：

1. 访问 [Tushare 官网](https://tushare.pro/) 注册账号
2. 登录后获取 API Token
3. 复制 `.env.example` 为 `.env`
4. 在 `.env` 文件中填入你的 token

```bash
cp .env.example .env
```

编辑 `.env` 文件:
```
TUSHARE_TOKEN=your_token_here
```

或者设置环境变量:
```bash
export TUSHARE_TOKEN=your_token_here
```

## 💻 使用方法

### 命令行模式

分析指定股票:
```bash
python main.py 000001.SZ
```

指定日期范围:
```bash
python main.py 000001.SZ 20240101 20241231
```

### 交互模式

直接运行进入交互模式:
```bash
python main.py
```

然后在提示符下输入股票代码即可。

### 股票代码格式

- **深交所**: `000xxx.SZ` (主板), `300xxx.SZ` (创业板)
- **上交所**: `600xxx.SH` (主板), `688xxx.SH` (科创板)

常见股票代码:
- `000001.SZ` - 平安银行
- `000002.SZ` - 万科A
- `600519.SH` - 贵州茅台
- `600036.SH` - 招商银行
- `300750.SZ` - 宁德时代

## 📊 输出说明

运行后会生成以下内容:

1. **终端输出**: 详细的股票技术分析报告
2. **CSV 文件**: 完整的分析数据（保存在 `data/` 目录）
3. **图表文件**:
   - `analysis_chart.png` - 完整的技术分析图
   - `signal_summary.png` - 买卖信号评分图

### 信号说明

| 信号 | 含义 | 操作建议 |
|------|------|----------|
| 🟢 BUY | 综合买入评分超过阈值 | 考虑买入 |
| 🔴 SELL | 综合卖出评分超过阈值 | 考虑卖出 |
| 🟡 HOLD | 无明显买卖信号 | 继续持有或观望 |

## ⚙️ 配置说明

在 `config.py` 中可以调整以下参数:

### 技术指标参数

```python
INDICATORS = {
    "MA": {
        "short_period": 5,      # 短期均线周期
        "medium_period": 20,    # 中期均线周期
        "long_period": 60       # 长期均线周期
    },
    "RSI": {
        "period": 14,           # RSI 周期
        "overbought": 70,       # 超买阈值
        "oversold": 30          # 超卖阈值
    },
    # ... 其他指标
}
```

### 信号策略配置

```python
SIGNAL_CONFIG = {
    "BUY_CONDITIONS": {      # 买入条件权重
        "MA_CROSS_UP": 3,
        "RSI_OVERSOLD": 2,
        "MACD_GOLDEN_CROSS": 3,
        "KDJ_OVERSOLD": 2
    },
    "BUY_THRESHOLD": 5,     # 买入信号总分阈值
    "SELL_THRESHOLD": 5     # 卖出信号总分阈值
}
```

## 📁 项目结构

```
stock-analyzer/
├── main.py              # 主入口
├── config.py            # 配置文件
├── chart.py             # 图表生成
├── requirements.txt     # 依赖包
├── .env.example        # 环境变量示例
├── indicators/          # 技术指标模块
│   ├── __init__.py
│   ├── base_indicator.py
│   ├── ma.py
│   ├── rsi.py
│   ├── macd.py
│   └── kdj.py
├── data_source/         # 数据源模块
│   ├── __init__.py
│   └── tushare_source.py
├── analysis/            # 分析模块
│   ├── __init__.py
│   └── signal_analyzer.py
├── utils/               # 工具模块
│   ├── __init__.py
│   └── logger.py
├── data/                # 数据存储目录
├── logs/                # 日志目录
└── README.md           # 说明文档
```

## ⚠️ 风险提示

1. 本系统仅供学习交流使用，不构成任何投资建议
2. 技术分析存在局限性，不能保证盈利
3. 投资有风险，入市需谨慎
4. 请结合基本面分析和风险管理策略

## 📝 待开发功能

- [ ] 支持更多技术指标（BOLL、ATR、OBV 等）
- [ ] 历史回测功能
- [ ] 多股票批量分析
- [ ] 邮件/微信推送买卖信号
- [ ] Web 界面
- [ ] 策略回测和优化

## 📄 许可证

MIT License

## 🙏 致谢

- [Tushare](https://tushare.pro/) - 提供免费的 A 股数据接口
- [pandas](https://pandas.pydata.org/) - 数据处理
- [matplotlib](https://matplotlib.org/) - 数据可视化
