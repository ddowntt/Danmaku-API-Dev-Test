# Danmaku-Media-Helper (个人学习与原型验证项目)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

本项目为个人开发者对接 [弹弹play开放弹幕网络](https://www.dandanplay.com/) 开放接口（v2）的**技术学习与本地原型验证工程**。

---

## 📌 项目性质与定位

- **申报层级**：**个人开发者学习 / 测试**（仅用于本地开发调试、学习研究或原型验证）。
- **项目定位**：个人在学习 Python 网络编程、多媒体特征计算与 API 鉴权协议时所建立的**本地原型（Prototype）**。
- **服务范围**：**绝不面向公众提供服务**。本项目仅限开发者本人在个人本地电脑环境（Localhost）中进行算法调试与数据结构验证，不提供任何线上公共代理，亦无公开发布客户端软件的计划。

---

## 🚀 原型验证内容

为了完整验证客户端对接弹弹play开放平台的技术链路，本项目在本地实现了以下功能原型：

1. **官方规范特征提取验证**：本地读取测试视频前 16MB 数据并计算 MD5，验证与官方文件识别接口（`/api/v2/match`）的特征匹配逻辑。
2. **SHA-256 签名鉴权验证**：严格按照官方安全规范，在本地实现基于 `base64(sha256(AppId + Timestamp + Path + AppSecret))` 的 `X-Signature` 动态鉴权。
3. **配额保护与本地缓存验证（遵循 Quota 规范）**：验证本地缓存降载策略，对匹配数据设置 24 小时本地文件缓存，防止开发调试阶段重复请求服务器。
4. **数据格式转换验证**：验证将开放平台返回的弹幕 JSON 数据解析转换为本地标准 XML 格式的技术可行性。

---

## 🛡️ 平台合规、配额与隐私声明

本项目严格遵守 [弹弹play开放弹幕网络](https://www.dandanplay.com/) 的各项开发者治理与规范要求：

### 1. 严格限定个人非商业学习
- **零公众服务**：本项目严格遵守“个人开发者学习/测试”层级约束，仅供个人本地技术研究，不对任何第三方公众或社群提供服务。
- **完全非商业**：项目以 MIT 协议开源代码，绝无任何商业变现、会员收费或增值服务计划。
- **致谢与来源**：测试调用的数据均由 **[弹弹play开放弹幕网络](https://www.dandanplay.com/)**（官网：`https://www.dandanplay.com`）提供。

### 2. 避免消耗平台资源（配额管理）
- **本地持久化缓存**：测试脚本内置缓存机制，同一测试文件绝对不重复请求接口。
- **按需单次调试**：仅在本地手动执行脚本时单次触发，严禁且绝不包含任何自动化脚本、定时轮询或批量爬虫逻辑。

### 3. 数据隐私与最小化传输（隐私规范）
- **数据传输最小化**：本地测试时仅上传官方接口必需的测试文件哈希与文件名，绝不收集、不上传任何个人隐私、设备信息或系统指纹。
- **全链路加密**：网络请求严格采用全链路 HTTPS（`https://api.dandanplay.net`）。
- **凭据安全隔离**：个人的 `AppId` 与 `AppSecret` 仅在本地通过环境变量注入，绝不硬编码提交至 Git 仓库。

---

## 📦 本地调试运行方法

### 1. 配置本地开发凭据
```bash
# Linux / macOS
export DANDAN_APP_ID="your_app_id"
export DANDAN_APP_SECRET="your_app_secret"

# Windows (PowerShell)
$env:DANDAN_APP_ID="your_app_id"
$env:DANDAN_APP_SECRET="your_app_secret"
```

### 2. 运行本地验证脚本
```bash
# 验证指定本地测试视频的匹配与弹幕转换逻辑
python main.py --file "/path/to/test_video.mp4"
```

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 协议开源。
