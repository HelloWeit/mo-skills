#!/usr/bin/env python3
"""
配图规划脚本
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state


def extract_image_requirements(article: str) -> list[dict]:
    """从文章中提取配图需求

    输出结构:
    [
      {"position": "封面", "purpose": "...", "prompt": "...", "style": "..."},
      {"position": "段中-第2段", "purpose": "...", "prompt": "...", "style": "..."}
    ]
    """
    if not article or not article.strip():
        return []

    lines = [line.strip() for line in article.splitlines() if line.strip()]
    title = "社区内容配图"
    for line in lines:
        if line.startswith("#"):
            title = line.lstrip("#").strip() or title
            break

    paragraphs = _extract_paragraphs(article)
    if not paragraphs:
        return [
            _build_requirement(
                position="封面",
                purpose="吸引点击",
                topic=title,
                paragraph_text=article.strip()[:180]
            )
        ]

    selected = _select_key_paragraphs(paragraphs, max_count=4)

    requirements = [
        _build_requirement(
            position="封面",
            purpose="吸引点击",
            topic=title,
            paragraph_text=selected[0][1]
        )
    ]

    for para_idx, para_text in selected:
        requirements.append(
            _build_requirement(
                position=f"段中-第{para_idx + 1}段",
                purpose=_infer_purpose(para_text),
                topic=title,
                paragraph_text=para_text
            )
        )

    return requirements


def _extract_paragraphs(article: str) -> list[str]:
    """提取正文段落，过滤标题、图片和过短段落。"""
    raw_paragraphs = [p.strip() for p in article.split("\n\n") if p.strip()]
    paragraphs = []

    for para in raw_paragraphs:
        if para.startswith("#"):
            continue
        if para.startswith("![" ):
            continue
        plain = re.sub(r"\s+", " ", para)
        if len(plain) < 40:
            continue
        paragraphs.append(plain)

    return paragraphs


def _select_key_paragraphs(paragraphs: list[str], max_count: int = 4) -> list[tuple[int, str]]:
    """从段落中均匀抽样，兼顾前中后内容。"""
    if len(paragraphs) <= max_count:
        return list(enumerate(paragraphs))

    picked_indexes = []
    last = len(paragraphs) - 1
    for i in range(max_count):
        idx = round(i * last / (max_count - 1))
        if idx not in picked_indexes:
            picked_indexes.append(idx)

    return [(idx, paragraphs[idx]) for idx in picked_indexes]


def _infer_purpose(paragraph_text: str) -> str:
    """根据段落内容推断配图目的。"""
    text = paragraph_text.lower()

    if re.search(r"\d+|%|同比|增长|下降|数据|统计|图表", text):
        return "数据可视化"
    if re.search(r"步骤|方法|流程|建议|清单|技巧|实操", text):
        return "步骤解释"
    if re.search(r"案例|故事|经历|客户|用户|场景", text):
        return "场景代入"
    if re.search(r"风险|误区|问题|坑|注意", text):
        return "风险提示"
    return "增强理解"


def _build_requirement(position: str, purpose: str, topic: str, paragraph_text: str) -> dict:
    snippet = paragraph_text[:120]
    style = "写实插画，简洁构图，暖色调，中文互联网内容风格"
    prompt = (
        f"主题：{topic}。"
        f"用途：{purpose}，用于{position}。"
        f"内容要点：{snippet}。"
        "画面需突出主体，信息清晰，无文字水印，无品牌 logo，4:3 构图。"
    )
    return {
        "position": position,
        "purpose": purpose,
        "prompt": prompt,
        "style": style
    }


def main():
    parser = argparse.ArgumentParser(
        description="配图规划脚本 - 从正式文章提取配图需求"
    )
    parser.add_argument(
        "--state", "-s",
        default="state.json",
        help="状态文件路径 (default: state.json)"
    )
    args = parser.parse_args()

    state = load_state(args.state)
    article = state.final_article_wechat or state.final_article_xiaohongshu

    if not article:
        print("[error] 未找到正式文章，请先完成 finalize 阶段")
        return

    requirements = extract_image_requirements(article)
    state.image_requirements = requirements
    save_state(state, args.state)

    print(f"[image-plan] 提取到 {len(requirements)} 个配图需求")
    print(f"[info] 结果已写入 {args.state}")


if __name__ == "__main__":
    main()
