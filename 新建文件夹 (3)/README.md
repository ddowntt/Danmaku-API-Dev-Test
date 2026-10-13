# Danmaku-API-Dev-Test

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

个人学习与对接[弹弹play开放平台 API (v2)](https://doc.dandanplay.com/open/)的测试验证工程。

---

## 📌 项目定位

本项目为个人开发者学习网络协议、API 接入规范以及数据解析的本地测试项目，主要用于对接和验证[弹弹play开放弹幕网络 API v2](https://doc.dandanplay.com/open/)。

## 🚀 功能说明

1. **API 签名算法验证**：实现并验证官方规定的基于 SHA-256 的 `X-Signature` 签名认证机制（`base64(sha256(AppId + Timestamp + Path + AppSecret))`）。
2. **接口请求示例**：
   - 验证番剧搜索与信息接口（`/api/v2/search/episodes`、`/api/v2/bangumi/{animeId}`）。
   - 验证弹幕库获取接口（`/api/v2/comment/{episodeId}`）。
3. **本地响应调试**：本地格式化输出与解析返回的 JSON 数据，调试网络延迟与异常错误码处理。

## ⚠️ 声明与使用约定

- **非商业用途**：本项目仅用于个人学习、测试与协议对接验证，绝不用于任何商业运营、收费或盈利活动。
- **无公共服务**：本项目仅在开发者本地开发环境运行，不对外提供任何形式的公共在线服务、公共代理或第三方接口包装。
- **严格遵守规范**：严格遵循[弹弹play开放平台第三方接入使用约定](https://doc.dandanplay.com/open/)，合理设置请求间隔与本地缓存，严禁进行高频刷量、批量抓取、爬虫或恶意发送弹幕等行为。

---

## 🛠️ 项目结构

```text
Danmaku-API-Dev-Test/
├── main.py            # 签名生成与 API 测试请求主程序
├── requirements.txt   # Python 依赖清单
├── .gitignore         # Git 忽略文件（防止敏感密钥提交）
└── README.md          # 项目说明文档
```

---

## 📦 快速开始

### 1. 克隆/下载项目

```bash
git clone https://github.com/YOUR_USERNAME/Danmaku-API-Dev-Test.git
cd Danmaku-API-Dev-Test
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置凭证并运行

请通过环境变量设置申请到的 `AppId` 和 `AppSecret`（避免硬编码至代码仓库）：

**Linux / macOS:**
```bash
export DANDAN_APP_ID="your_app_id_here"
export DANDAN_APP_SECRET="your_app_secret_here"
python main.py
```

**Windows (PowerShell):**
```powershell
$env:DANDAN_APP_ID="your_app_id_here"
$env:DANDAN_APP_SECRET="your_app_secret_here"
python main.py
```

**Windows (CMD):**
```cmd
set DANDAN_APP_ID=your_app_id_here
set DANDAN_APP_SECRET=your_app_secret_here
python main.py
```

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 授权。
