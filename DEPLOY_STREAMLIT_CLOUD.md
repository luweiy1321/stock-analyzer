# 股票分析系统 - Streamlit Cloud 部署指南

## 为什么选择 Streamlit Cloud？

- ✅ 完全免费
- ✅ 不占用您自己的服务器资源
- ✅ 自动 HTTPS
- ✅ 全球 CDN 加速
- ✅ 支持自定义域名
- ✅ 连接 GitHub 自动部署

---

## 部署步骤

### 第一步：注册 Streamlit 账号

1. 访问 https://share.streamlit.io
2. 点击 "Sign up" 注册
   - 可以用 GitHub、Google、Email 注册

### 第二步：创建 GitHub 仓库

#### 方法A：网页创建（推荐）

1. 访问 https://github.com/new
2. 填写信息：
   - Repository name: `stock-analyzer`（或其他名字）
   - Description: 股票技术分析系统
   - Public: ✅ 公开（Streamlit Cloud 需要）
3. 点击 "Create repository"

#### 方法B：使用 GitHub Desktop

1. 下载 GitHub Desktop: https://desktop.github.com/
2. File → New Repository → 创建本地仓库
3. 把 `stock-analyzer` 文件夹复制到仓库目录
4. 提交并推送

### 第三步：上传代码到 GitHub

#### 方法A：网页上传（适合文件少）

1. 在新创建的 GitHub 仓库页面
2. 点击 "uploading an existing file"
3. 拖拽这些文件上传：

```
stock-analyzer/
├── requirements.txt          ← 必需
├── batch_web_enhanced.py    ← 必需（主程序）
├── config.py                ← 必需
├── data_source/             ← 文件夹，全部上传
│   ├── __init__.py
│   └── yfinance_source.py
├── analysis/                ← 文件夹，全部上传
│   ├── __init__.py
│   └── signal_analyzer.py
└── indicators/              ← 文件夹，全部上传
    ├── __init__.py
    ├── ma.py
    ├── rsi.py
    ├── macd.py
    └── kdj.py
```

**注意：**
- 传 `__pycache__` 里的文件不用传
- `.env` 文件不要传（包含敏感信息）

#### 方法B：使用 Git 命令（推荐，简单）

在本地项目目录 `d:\stock-analyzer` 执行：

```bash
# 初始化 Git
git init

# 添加所有文件（排除缓存）
git add .
git rm -r --cached __pycache__

# 提交
git commit -m "Initial commit: 股票分析系统"

# 连接 GitHub 仓库（替换您的用户名）
git remote add origin https://github.com/您的用户名/stock-analyzer.git

# 推送到 GitHub
git push -u origin main
```

### 第四步：在 Streamlit Cloud 部署

1. 访问 https://share.streamlit.io 并登录
2. 点击 "New app"
3. 选择 GitHub 仓库 `stock-analyzer`
4. 填写部署信息：

| 选项 | 填写 |
|------|------|
| Repository | stock-analyzer |
| Branch | main |
| Main file path | `batch_web_enhanced.py` |
| Python version | 3.10 或 3.11（选择最新） |

5. 点击 "Deploy" 开始部署

6. 等待几分钟，部署成功后会显示访问地址

---

## 获取访问地址

部署成功后，您会得到类似这样的地址：

```
https://your-app-name.streamlit.app
```

**例如：**
```
https://stock-analyzer123.streamlit.app
https://mytool-stock.streamlit.app
```

---

## 在 Readymag 中嵌入

在 mytool.help 的 Readymag 编辑器中添加：

```html
<div style="width: 100%; max-width: 1400px; margin: 0 auto;">
  <h2 style="text-align: center; margin: 20px 0;">📊 股票技术分析系统</h2>
  <div style="width: 100%; height: 85vh; border: 1px solid #ddd; border-radius: 8px;">
    <iframe
      src="https://您的应用名.streamlit.app"
      style="width: 100%; height: 100%; border: none;"
      title="股票分析系统"
      allowfullscreen>
    </iframe>
  </div>
  <p style="text-align: center; color: #999; font-size: 12px; margin-top: 10px;">
    使用账号访问，密码：stock2024
  </p>
</div>
```

---

## 自定义域名（可选）

如果您想用 `stock.mytool.help` 访问：

1. 在您的域名 DNS 管理添加 CNAME：
   ```
   stock.mytool.help → 您应用的.streamlit.app
   ```

2. 在 Streamlit Cloud 设置：
   - 进入您应用的 Settings
   - 点击 "Add a custom domain"
   - 输入 `stock.mytool.help`
   - 按提示配置 DNS

3. 等待验证完成，就能用 `https://stock.mytool.help` 访问了

---

## 修改密码

修改 `batch_web_enhanced.py` 中的密码：

```python
# 第 32 行左右
CORRECT_PASSWORD = "stock2024"  # 改成您想要的密码
```

修改后：
1. 提交到 GitHub：`git commit -am "更新密码" && git push`
2. Streamlit Cloud 会自动重新部署

---

## 常见问题

### Q: 部署失败怎么办？
A: 检查：
- GitHub 仓库是否设为 Public（公开）
- requirements.txt 文件是否存在
- 主程序文件路径是否正确

### Q: 部署成功但无法访问？
A: 检查：
- 浏览器是否屏蔽了第三方Cookie
- 等待几分钟让服务完全启动

### Q: 想要更新代码怎么办？
A: 直接 push 到 GitHub，Streamlit Cloud 会自动检测并重新部署

### Q: 免费额度够用吗？
A: Streamlit Cloud 免费版：
- 每月 750 小时运行时间（每天约24小时）
- 完全够个人使用
- 超额后需要等待或升级付费版

---

## 快速命令参考（使用 Git）

```bash
# 第一次设置
cd d:\stock-analyzer
git init
git add .
git rm -r --cached __pycache__
git commit -m "Initial commit"
git remote add origin https://github.com/您的用户名/stock-analyzer.git
git push -u origin main

# 后续更新
git add .
git commit -m "更新内容"
git push
```

---

## 完成！

部署成功后，任何人都可以通过网址访问您的股票分析系统！

有问题随时问我。
