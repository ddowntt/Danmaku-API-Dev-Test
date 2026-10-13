"""
Danmaku-API-Dev-Test
弹弹play 开放弹幕网络 API (v2) 本地测试验证脚本
官方文档: https://doc.dandanplay.com/open/
"""

import os
import sys
import time
import json
import base64
import hashlib
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional

API_BASE_URL = "https://api.dandanplay.net"


def generate_signature(app_id: str, timestamp: int, path: str, app_secret: str) -> str:
    """
    根据弹弹play官方规范计算 X-Signature 签名。

    算法规则：
        base64(sha256(AppId + Timestamp + Path + AppSecret))

    说明：
        1. AppId、Timestamp、Path 和 AppSecret 按顺序拼接成字符串，区分大小写。
        2. Path 为小写 API 相对路径，以 '/' 开头，不包含协议、域名和 '?' 后面的查询参数。
        3. 对拼接后的字符串使用 SHA-256 算法计算哈希值（二进制摘要）。
        4. 将哈希结果转换为 Base64 编码字符串。

    :param app_id: 申请到的应用程序 ID (AppId)
    :param timestamp: 当前时间的 Unix 时间戳（秒，UTC 时间）
    :param path: 请求的 API 路径（如 '/api/v2/comment/123450001'）
    :param app_secret: 应用程序密钥 (AppSecret)
    :return: 计算出的 Base64 签名字符串
    """
    # 保证 path 为小写且以 '/' 开头，去除可能传入的 query string
    normalized_path = path.split("?")[0].lower()
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path

    # 按顺序拼接：AppId + Timestamp + Path + AppSecret
    raw_data = f"{app_id}{timestamp}{normalized_path}{app_secret}"

    # 使用 SHA-256 计算哈希二进制摘要
    sha256_hash = hashlib.sha256(raw_data.encode("utf-8")).digest()

    # 转换为 Base64 编码字符串
    signature = base64.b64encode(sha256_hash).decode("utf-8")
    return signature


def build_request_headers(app_id: str, app_secret: str, path: str) -> Dict[str, str]:
    """
    构建符合弹弹play签名验证模式规范的 HTTP 请求头。

    必选请求头：
        X-AppId: 应用程序 ID
        X-Timestamp: 当前 UTC 时间戳（秒）
        X-Signature: 动态计算的签名
    """
    timestamp = int(time.time())
    signature = generate_signature(app_id, timestamp, path, app_secret)

    return {
        "Accept": "application/json",
        "User-Agent": "Danmaku-API-Dev-Test/1.0",
        "X-AppId": app_id,
        "X-Timestamp": str(timestamp),
        "X-Signature": signature,
    }


def call_api(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    向弹弹play开放平台发送 GET 请求的基础测试函数。

    :param path: API 路径，例如 '/api/v2/search/episodes'
    :param params: URL 查询参数字典
    :param app_id: 应用 ID（默认从环境变量 DANDAN_APP_ID 读取）
    :param app_secret: 应用 Secret（默认从环境变量 DANDAN_APP_SECRET 读取）
    :return: 解析后的 JSON 字典数据
    """
    # 读取环境变量或使用默认占位符
    resolved_app_id = app_id or os.environ.get("DANDAN_APP_ID", "your_test_app_id")
    resolved_app_secret = app_secret or os.environ.get("DANDAN_APP_SECRET", "your_test_app_secret")

    # 规范化路径
    clean_path = path.split("?")[0].lower()

    # 构造请求 URL
    query_string = urllib.parse.urlencode(params) if params else ""
    full_url = f"{API_BASE_URL}{clean_path}"
    if query_string:
        full_url += f"?{query_string}"

    # 生成签名并构建请求头
    headers = build_request_headers(resolved_app_id, resolved_app_secret, clean_path)

    print(f"\n[Request] GET {full_url}")
    print("[Headers]")
    for k, v in headers.items():
        # 为保护密钥安全，打印时仅展示脱敏信息
        display_val = v if k != "X-Signature" else f"{v[:6]}...{v[-4:]} (len={len(v)})"
        print(f"  {k}: {display_val}")

    req = urllib.request.Request(full_url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            body_bytes = response.read()
            data = json.loads(body_bytes.decode("utf-8"))
            print(f"[Response] HTTP {status_code} Success")
            return data
    except urllib.error.HTTPError as e:
        print(f"[Error] HTTP {e.code} {e.reason}")
        # 弹弹play 403 错误会在响应头返回 X-Error-Message
        error_msg = e.headers.get("X-Error-Message")
        if error_msg:
            print(f"[Error Detail] X-Error-Message: {error_msg}")
        try:
            err_body = e.read().decode("utf-8")
            print(f"[Error Body] {err_body}")
        except Exception:
            pass
        return None
    except urllib.error.URLError as e:
        print(f"[Network Error] 无法连接到服务器: {e.reason}")
        return None


def main():
    print("=" * 60)
    print(" Danmaku-API-Dev-Test: 弹弹play API (v2) 签名验证与测试")
    print(" 声明: 仅限个人本地测试与协议学习，严禁用于商业用途")
    print("=" * 60)

    # 1. 签名算法单元演示
    test_app_id = "test_app_id_1001"
    test_app_secret = "test_secret_key_8888"
    test_timestamp = 1735660800  # 2025-01-01 00:00:00 UTC
    test_path = "/api/v2/comment/123450001"

    demo_signature = generate_signature(test_app_id, test_timestamp, test_path, test_app_secret)
    print("\n[1. 签名算法演示验证]")
    print(f"AppId      : {test_app_id}")
    print(f"Timestamp  : {test_timestamp}")
    print(f"Path       : {test_path}")
    print(f"AppSecret  : {test_app_secret}")
    print(f"Signature  : {demo_signature}")

    # 2. 真实接口调用测试骨架
    print("\n[2. 测试接口调用骨架示例]")
    app_id = os.environ.get("DANDAN_APP_ID")
    app_secret = os.environ.get("DANDAN_APP_SECRET")

    if not app_id or not app_secret:
        print("未检测到环境变量 DANDAN_APP_ID / DANDAN_APP_SECRET。")
        print("提示：获得官方审核发放的凭证后，请配置环境变量再进行真实网络调用测试。")
        print("当前将使用演示参数构造测试请求头...")

    # 示例 A: 测试搜索番剧与分集信息 (/api/v2/search/episodes)
    print("\n>>> 示例 A: 测试搜索番剧接口")
    call_api(
        path="/api/v2/search/episodes",
        params={"anime": "海贼王", "episode": "1"},
        app_id=app_id,
        app_secret=app_secret,
    )

    # 示例 B: 测试弹幕获取接口 (/api/v2/comment/{episodeId})
    print("\n>>> 示例 B: 测试获取弹幕接口")
    call_api(
        path="/api/v2/comment/123450001",
        params={"withRelated": "true"},
        app_id=app_id,
        app_secret=app_secret,
    )


if __name__ == "__main__":
    main()
