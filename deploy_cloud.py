"""
云端部署脚本 - 用于将Streamlit应用部署到云服务器
"""
import os
import sys
from pathlib import Path

# 读取并替换 localhost 为实际部署地址
script_dir = Path(__file__).parent

print("""
========================================
    股票分析系统 - 云端部署指南
========================================

【方案一：云服务器部署（推荐）】

1. 购买云服务器
   - 阿里云: https://www.aliyun.com
   - 腾讯云: https://cloud.tencent.com
   - 推荐配置: 1核2G内存起步即可

2. 连接服务器
   Windows用户下载: https://putty.org/
   Mac/Linux用户使用终端: ssh root@服务器IP

3. 安装Python和依赖
   curl -o install.sh https://bootstrap.pypa.io/get-pip.py
   python install.sh
   pip install streamlit pandas yfinance

4. 上传代码到服务器
   使用 FileZilla 或 scp 上传整个 stock-analyzer 文件夹

5. 启动应用（后台运行）
   nohup streamlit run batch_web_enhanced.py --server.port 8503 --server.address 0.0.0.0 > app.log 2>&1 &

6. 配置服务器防火墙（开放8503端口）
   阿里云: 安全组 -> 添加规则 -> 端口8503
   腾讯云: 防火墙 -> 添加规则 -> 端口8503

7. 获取访问地址
   http://您的服务器IP:8503
   或
   http://您的域名:8503（如果有域名）


【方案二：Streamlit Cloud（最简单）】

1. 访问: https://share.streamlit.io

2. 登录或注册账号

3. 将代码上传到GitHub仓库
   - 创建仓库: https://github.com/new
   - 上传 stock-analyzer 文件夹内容

4. 在 Streamlit Cloud 中连接 GitHub

5. 选择 batch_web_enhanced.py 作为入口文件

6. 点击部署，获得访问地址如: https://your-app.streamlit.app


【方案三：Render/PaaS平台】

1. 访问: https://render.com

2. 创建新 Web Service

3. 连接 GitHub 仓库

4. 设置构建命令:
   pip install -r requirements.txt
   streamlit run batch_web_enhanced.py --server.port $PORT

5. 部署后获得免费域名


【配置域名（可选）】

如果您有域名 mytool.help，可以这样配置:

1. 添加子域名解析
   stock.mytool.help -> 您的服务器IP

2. 在 Streamlit Cloud 中添加自定义域名（如用方案二）


【修改密码】

编辑 batch_web_enhanced.py 文件中的这一行:

    CORRECT_PASSWORD = "stock2024"

修改为您想要的密码，然后重新部署。


【创建 requirements.txt】

请在项目目录创建 requirements.txt 文件，内容如下:

streamlit
pandas
yfinance
numpy
""")

print("\n请选择部署方案...")
