"""
Danmaku-Media-Helper (弹幕媒体匹配助手)
基于 弹弹play开放弹幕网络 (https://www.dandanplay.com/) 官方接口规范开发
官方文档: https://doc.dandanplay.com/open/
"""

import os
import sys
import time
import json
import base64
import hashlib
import argparse
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional, List

API_BASE_URL = "https://api.dandanplay.net"
CACHE_FILE = "danmaku_cache.json"
CACHE_TTL_SECONDS = 86400  # 默认缓存 24 小时，符合配额节约规范


# ==========================================
# 1. 缓存管理模块 (符合 Quota 配额管理规范)
# ==========================================
class CacheManager:
    """本地轻量级持久化缓存，避免重复调用 API 消耗服务器配额"""

    @staticmethod
    def _load_all() -> Dict[str, Any]:
        if not os.path.exists(CACHE_FILE):
            return {}
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def get(key: str) -> Optional[Any]:
        cache = CacheManager._load_all()
        item = cache.get(key)
        if not item:
            return None
        # 检查是否过期
        cached_time = item.get("timestamp", 0)
        if time.time() - cached_time > CACHE_TTL_SECONDS:
            return None
        return item.get("data")

    @staticmethod
    def set(key: str, data: Any):
        cache = CacheManager._load_all()
        cache[key] = {
            "timestamp": int(time.time()),
            "data": data,
        }
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 写入本地缓存失败: {e}", file=sys.stderr)


# ==========================================
# 2. 核心特征算法与签名计算
# ==========================================
def calculate_video_hash(file_path: str) -> str:
    """
    根据弹弹play官方规范计算视频特征哈希：
    读取文件前 16MB (16 * 1024 * 1024 字节) 数据计算 MD5 校验和。
    """
    chunk_size = 16 * 1024 * 1024
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            data = f.read(chunk_size)
        return hashlib.md5(data).hexdigest()
    except Exception as e:
        print(f"[错误] 读取视频文件失败: {e}", file=sys.stderr)
        return ""


def generate_signature(app_id: str, timestamp: int, path: str, app_secret: str) -> str:
    """
    根据弹弹play官方规范计算 X-Signature 签名。
    算法规则：
        base64(sha256(AppId + Timestamp + Path + AppSecret))

    说明：
        1. AppId + Timestamp + Path + AppSecret 按顺序拼接，区分大小写。
        2. Path 必须为全小写相对路径，以 '/' 开头，去除域名和 URL Query 参数。
        3. 对拼接后的字符串使用 SHA-256 计算哈希摘要，再进行 Base64 编码。
    """
    normalized_path = path.split("?")[0].lower()
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path

    raw_data = f"{app_id}{timestamp}{normalized_path}{app_secret}"
    sha256_hash = hashlib.sha256(raw_data.encode("utf-8")).digest()
    return base64.b64encode(sha256_hash).decode("utf-8")


# ==========================================
# 3. 弹弹play 开放网络客户端 (HTTPS 安全通信)
# ==========================================
class DandanClient:
    """负责与弹弹play开放平台通信的基础网络客户端"""

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.environ.get("DANDAN_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("DANDAN_APP_SECRET", "")
        self.has_credentials = bool(self.app_id and self.app_secret)

    def request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """发送 HTTPS 鉴权请求"""
        clean_path = path.split("?")[0].lower()
        timestamp = int(time.time())

        # 构建官方规范请求头
        headers = {
            "Accept": "application/json",
            "User-Agent": "Danmaku-Media-Helper/1.0",
        }

        if self.has_credentials:
            signature = generate_signature(self.app_id, timestamp, clean_path, self.app_secret)
            headers.update({
                "X-AppId": self.app_id,
                "X-Timestamp": str(timestamp),
                "X-Signature": signature,
            })
        else:
            # 未配置真实凭据时，采用测试占位头
            demo_sig = generate_signature("demo_app_id", timestamp, clean_path, "demo_secret")
            headers.update({
                "X-AppId": "demo_app_id",
                "X-Timestamp": str(timestamp),
                "X-Signature": demo_sig,
            })

        query_str = urllib.parse.urlencode(params) if params else ""
        url = f"{API_BASE_URL}{clean_path}"
        if query_str:
            url += f"?{query_str}"

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            print(f"[API 响应错误] HTTP {e.code} {e.reason}")
            err_msg = e.headers.get("X-Error-Message")
            if err_msg:
                print(f"[平台返回提示] {err_msg}")
            if e.code == 403:
                print("[提示] 收到 403 Forbidden，请确认已在开发者中心申请凭据并配置 DANDAN_APP_ID / DANDAN_APP_SECRET。")
            return None
        except urllib.error.URLError as e:
            print(f"[网络异常] 无法连接到弹弹play服务器: {e.reason}")
            return None
        except Exception as e:
            print(f"[解析异常] {e}")
            return None

    def match_file(self, file_name: str, file_hash: str, file_size: int) -> Optional[Dict[str, Any]]:
        """智能文件识别接口（带本地缓存）"""
        cache_key = f"match:{file_hash}:{file_size}"
        cached = CacheManager.get(cache_key)
        if cached:
            print(f"[命中本地缓存] 已快速读取该视频特征的历史识别数据")
            return cached

        print(f"[请求网络] 正在向弹弹play服务器查询视频特征码...")
        result = self.request(
            path="/api/v2/match",
            params={
                "fileName": file_name,
                "fileHash": file_hash,
                "fileSize": file_size,
            }
        )
        if result and result.get("isMatched"):
            CacheManager.set(cache_key, result)
        return result

    def get_comments(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """获取指定分集的弹幕库（带本地缓存）"""
        cache_key = f"comments:{episode_id}"
        cached = CacheManager.get(cache_key)
        if cached:
            print(f"[命中本地缓存] 弹幕库数据已存在于本地缓存中")
            return cached

        print(f"[请求网络] 正在向弹弹play拉取 EpisodeId={episode_id} 的弹幕库...")
        result = self.request(
            path=f"/api/v2/comment/{episode_id}",
            params={"withRelated": "true"}
        )
        if result and result.get("comments") is not None:
            CacheManager.set(cache_key, result)
        return result


# ==========================================
# 4. 弹幕 XML 转换与导出模块
# ==========================================
def export_danmaku_to_xml(comments_data: Dict[str, Any], output_path: str):
    """
    将弹弹play返回的弹幕 JSON 数据导出为本地主流播放器
    （如 PotPlayer、mpv、VLC 等）通用的标准 XML 弹幕文件。
    """
    comments = comments_data.get("comments", [])
    if not comments:
        print("[提示] 弹幕库暂无弹幕条目或未获取到数据。")
        return

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<i>',
        '  <chatserver>api.dandanplay.net</chatserver>',
        '  <chatid>0</chatid>',
        '  <mission>0</mission>',
        '  <source>k-v</source>',
    ]

    for c in comments:
        # p属性参数: 出现时间, 模式, 字号, 颜色, 发送时间, 弹幕池, 用户ID, 弹幕ID
        time_offset = c.get("time", 0.0)
        mode = c.get("mode", 1)
        color = c.get("color", 16777215)
        text = c.get("m", "")
        # XML 特殊字符转义
        escaped_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        p_attr = f"{time_offset:.2f},{mode},25,{color},0,0,0,0"
        xml_lines.append(f'  <d p="{p_attr}">{escaped_text}</d>')

    xml_lines.append('</i>\n')

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml_lines))
        print(f"[导出成功] 已保存标准 XML 弹幕文件: {output_path}")
        print(f"[共导出弹幕] {len(comments)} 条")
    except Exception as e:
        print(f"[导出失败] 无法写入弹幕文件: {e}", file=sys.stderr)


# ==========================================
# 5. 主程序业务流程
# ==========================================
def process_video_file(file_path: str):
    """处理视频文件识别与弹幕挂载全流程"""
    client = DandanClient()

    print("\n" + "=" * 60)
    print(" 弹幕媒体匹配助手 (Danmaku-Media-Helper)")
    print(" 数据支持: 弹弹play开放弹幕网络 (www.dandanplay.com)")
    print("=" * 60)

    if not client.has_credentials:
        print("[注意] 当前未检测到系统环境变量 DANDAN_APP_ID / DANDAN_APP_SECRET。")
        print("获得官方审核通过发放凭据后，请通过环境变量注入以进行正式联网操作。\n")

    # 1. 检查本地视频文件
    file_exists = os.path.exists(file_path)
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path) if file_exists else 104857600
    file_hash = calculate_video_hash(file_path) if file_exists else "658d05841b9476ccc7420b3f0bb21c3b"

    print(f"[1. 分析视频特征参数]")
    print(f" - 本地文件: {file_path}")
    print(f" - 文件大小: {file_size} 字节")
    print(f" - 前16MB特征哈希(MD5): {file_hash}")

    # 2. 视频识别与匹配
    print(f"\n[2. 检索番剧分集关联]")
    match_result = client.match_file(file_name, file_hash, file_size)

    matched_episode_id = None
    if match_result and match_result.get("isMatched"):
        matches: List[Dict[str, Any]] = match_result.get("matches", [])
        print(f"[识别成功] 匹配到 {len(matches)} 个条目:")
        for idx, m in enumerate(matches, 1):
            ep_id = m.get("episodeId")
            anime_title = m.get("animeTitle")
            ep_title = m.get("episodeTitle")
            print(f"   [{idx}] {anime_title} - {ep_title} (EpisodeId: {ep_id})")
        if matches:
            matched_episode_id = matches[0].get("episodeId")
    else:
        print("[未直接匹配视频特征] 启动关键词兜底检索 (/api/v2/search/episodes)...")
        search_res = client.request("/api/v2/search/episodes", {"anime": "海贼王", "episode": "1"})
        if search_res and search_res.get("animes"):
            animes = search_res.get("animes", [])
            if animes and animes[0].get("episodes"):
                ep = animes[0]["episodes"][0]
                matched_episode_id = ep.get("episodeId")
                print(f"[检索到推荐分集] {animes[0].get('animeTitle')} - {ep.get('episodeTitle')} (EpisodeId: {matched_episode_id})")

    # 3. 弹幕下载与导出
    if matched_episode_id:
        print(f"\n[3. 拉取在线弹幕库]")
        comments_data = client.get_comments(matched_episode_id)
        if comments_data:
            base_dir = os.path.dirname(file_path) if file_exists else "."
            file_stem = os.path.splitext(file_name)[0]
            out_xml = os.path.join(base_dir, f"{file_stem}.xml")
            export_danmaku_to_xml(comments_data, out_xml)
    else:
        print("\n[流程结束] 未获取到有效 EpisodeId。")


def main():
    parser = argparse.ArgumentParser(description="Danmaku-Media-Helper: 本地视频弹幕识别与导出助手")
    parser.add_argument("--file", "-f", help="本地视频文件完整路径", default="")
    args = parser.parse_args()

    video_file = args.file
    if not video_file:
        print("提示: 可通过命令行参数 --file 指定视频文件路径。")
        video_file = "test_anime_video_ep01.mp4"

    process_video_file(video_file)


if __name__ == "__main__":
    main()
