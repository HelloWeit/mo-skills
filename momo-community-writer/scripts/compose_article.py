#!/usr/bin/env python3
"""
图文整合脚本
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state


def compose_article_with_images(article: str, images: list[dict], platform: str = "wechat") -> str:
    """将图片整合到文章中

    Args:
        article: 文章内容
        images: 图片列表， 每个包含 url 和可选的 position 信息
        platform: 目标平台

    Returns:
        整合后的文章
    """
    if not images:
        return article

    # 根据平台选择插入格式
    if platform == "wechat":
        return _compose_for_wechat(article, images)
    else:
        return _compose_for_xiaohongshu(article, images)


def _compose_for_wechat(article: str, images: list[dict]) -> str:
    """公众号图文整合 - 按 position 定位并插入段后。"""
    paragraphs = article.split("\n\n")
    marker_re = re.compile(r"<!--\s*图片位置:\s*段中-第(\d+)段?\s*-->")

    cover_images = []
    para_images: dict[int, list[dict]] = {}
    fallback_images = []

    for img in images:
        position = str(img.get("position", "")).strip()

        if position == "封面":
            cover_images.append(img)
            continue

        match = re.search(r"段中-第(\d+)段", position)
        if match:
            para_idx = int(match.group(1)) - 1
            if 0 <= para_idx < len(paragraphs):
                para_images.setdefault(para_idx, []).append(img)
                continue

        fallback_images.append(img)

    composed_parts = []

    for i, img in enumerate(cover_images, 1):
        if img.get("url"):
            composed_parts.append(f"![封面{i}]({img['url']})")

    for idx, para in enumerate(paragraphs):
        cleaned = marker_re.sub("", para).strip()
        if cleaned:
            composed_parts.append(cleaned)

        for img in para_images.get(idx, []):
            if img.get("url"):
                composed_parts.append(f"![配图]({img['url']})")

    for img in fallback_images:
        if img.get("url"):
            composed_parts.append(f"![配图]({img['url']})")

    return "\n\n".join(composed_parts).strip()


def _compose_for_xiaohongshu(article: str, images: list[dict]) -> str:
    """小红书图文整合 - 图片放在正文后"""
    # 小红书图片放在最后
    image_markdown = "\n\n---\n\n## 配图\n"
    for i, img in enumerate(images, 1):
        image_markdown += f"\n\n![图{i}]({img['url']})\n"
    return article + image_markdown


def main():
    state = load_state()

    article = state.final_article_wechat or state.final_article_xiaohongshu
    images = state.image_assets or []

    if not article:
        print("[error] 未找到正式文章")
        return

    composed = compose_article_with_images(article, images)
    state.composed_article = composed
    save_state(state)

    print("[compose] 图文整合完成")


if __name__ == "__main__":
    main()
