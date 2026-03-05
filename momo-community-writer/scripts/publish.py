#!/usr/bin/env python3
"""
发布脚本

Usage:
    python scripts/publish.py --platform wechat --state state.json
    python scripts/publish.py --help
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state


def infer_title_from_state(state, article: str = "") -> str | None:
    """从 state 推断标题，优先使用大纲标题。"""
    outline = state.approved_outline or {}
    if isinstance(outline, dict):
        titles = outline.get("titles", [])
        if isinstance(titles, list):
            for t in titles:
                if isinstance(t, str) and t.strip():
                    return t.strip()

    for line in article.splitlines():
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title
    return None


def check_platform_config(platform: str) -> tuple[bool, str]:
    """检查平台配置"""
    if platform == "wechat":
        app_id = os.getenv("WECHAT_APP_ID")
        app_secret = os.getenv("WECHAT_APP_SECRET")
        if app_id and app_secret:
            return True, "公众号配置完整"
        return False, "WECHAT_APP_ID 或 WECHAT_APP_SECRET 未配置"
    elif platform == "xiaohongshu":
        cookie = os.getenv("XIAOHONGSHU_COOKIE")
        if cookie:
            return True, "小红书配置完整"
        return False, "XIAOHONGSHU_COOKIE 未配置"
    return False, f"未知平台: {platform}"


def publish_to_wechat(article: str, title: str = None, **kwargs) -> dict:
    """发布到公众号"""
    # TODO: 实现公众号发布逻辑
    return {"success": False, "error": "API 发布待实现"}


def publish_to_xiaohongshu(article: str, title: str = None, **kwargs) -> dict:
    """发布到小红书"""
    # TODO: 实现小红书发布逻辑
    return {"success": False, "error": "API 发布待实现"}


def generate_export_package(
    article: str,
    images: list,
    platform: str,
    title: str = None,
    tags: list = None
) -> dict:
    """生成降级发布包"""
    manual_steps = {
        "wechat": [
            "1. 登录微信公众平台 (mp.weixin.qq.com)",
            "2. 进入「素材管理」→「新建图文」",
            "3. 填入标题和正文内容",
            "4. 按位置说明上传并插入图片",
            "5. 设置封面图、摘要、标签",
            "6. 保存并发布"
        ],
        "xiaohongshu": [
            "1. 打开小红书 APP 或创作者中心",
            "2. 点击「+」发布笔记",
            "3. 上传图片（建议 3-9 张）",
            "4. 填写标题（限 20 字）",
            "5. 填写正文（限 1000 字）",
            "6. 添加话题标签",
            "7. 发布"
        ]
    }

    return {
        "article": article,
        "title": title or "未设置标题",
        "images": images or [],
        "tags": tags or [],
        "platform": platform,
        "manual_steps": manual_steps.get(platform, ["请手动发布到目标平台"])
    }


def main():
    parser = argparse.ArgumentParser(
        description="发布脚本 - 发布文章到目标平台或生成降级发布包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/publish.py --platform wechat
    python scripts/publish.py --platform xiaohongshu --state state.json

环境变量:
    WECHAT_APP_ID       公众号 AppID
    WECHAT_APP_SECRET   公众号 AppSecret
    XIAOHONGSHU_COOKIE  小红书 Cookie

输出:
    成功: state.json 中的 publish_result
    失败: state.json 中的 export_package（降级发布包）
        """
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["wechat", "xiaohongshu"],
        required=True,
        help="目标发布平台 (required)"
    )
    parser.add_argument(
        "--state", "-s",
        default="state.json",
        help="状态文件路径 (default: state.json)"
    )

    args = parser.parse_args()

    # 加载状态
    state = load_state(args.state)

    article = state.final_publishable_article or state.composed_article
    if not article:
        print("[error] 未找到可发布的文章，请先完成 compose 阶段")
        sys.exit(1)
    title = infer_title_from_state(state, article)

    # 检查平台配置
    has_config, msg = check_platform_config(args.platform)
    print(f"[info] {msg}")

    # 尝试发布
    if has_config:
        print(f"[info] 尝试 API 发布到 {args.platform}...")

        if args.platform == "wechat":
            result = publish_to_wechat(article, title=title)
        else:
            result = publish_to_xiaohongshu(article, title=title)

        if result.get("success"):
            state.publish_result = result
            save_state(state, args.state)
            print(f"[success] 发布成功!")
            if result.get("url"):
                print(f"[info] 文章链接: {result['url']}")
            return

        print(f"[warn] API 发布失败: {result.get('error')}")

    # 降级导出
    print("[info] 生成降级发布包...")
    export = generate_export_package(
        article=article,
        images=state.image_assets or [],
        platform=args.platform,
        title=title,
        tags=[]
    )
    state.export_package = export
    save_state(state, args.state)

    print("[success] 降级发布包已生成")
    print("\n手动发布步骤:")
    for step in export["manual_steps"]:
        print(f"  {step}")


if __name__ == "__main__":
    main()
