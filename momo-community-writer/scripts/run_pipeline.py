#!/usr/bin/env python3
"""
主流程编排入口
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state, advance_stage, Stage, WorkflowState
from scripts.compose_article import compose_article_with_images
from scripts.image_plan import extract_image_requirements
from scripts.publish import generate_export_package, infer_title_from_state
from scripts.review_article import review_article as review_article_func


def ensure_output_dir(output_dir: str | None) -> Path:
    """确保输出目录存在，返回 Path 对象"""
    if output_dir is None:
        output_dir = "./output"
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_draft_to_output(state: WorkflowState, filename: str, content: str) -> str | None:
    """将草稿保存到输出目录，返回文件路径"""
    if not state.output_dir:
        return None
    output_path = ensure_output_dir(state.output_dir)
    file_path = output_path / filename
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def _infer_topic(state: WorkflowState) -> str:
    brief = state.intent_brief or {}
    topic = brief.get("topic") if isinstance(brief, dict) else None
    return topic or "社区内容创作方法论"


def run_discovery(state: WorkflowState) -> WorkflowState:
    """阶段1: 需求发现"""
    if not state.intent_brief:
        state.intent_brief = {
            "topic": "社区内容创作方法论",
            "target_platforms": ["wechat", "xiaohongshu"],
            "audience": "内容运营与社区运营从业者",
            "goal": "提升内容生产效率与质量稳定性",
            "tone": "专业、实操、清晰"
        }
    if not state.constraints:
        state.constraints = {
            "avoid_claims": True,
            "platform_compliance": True,
            "no_fake_data": True,
        }
    if not state.success_criteria:
        state.success_criteria = [
            "结构完整，有明确问题-方法-结论",
            "可直接用于公众号发布",
            "可改写为小红书版本",
        ]
    # 如果未设置输出目录，使用默认值并提示
    if not state.output_dir:
        state.output_dir = "./output"
        print(f"[discovery] 输出目录设置为默认值: {state.output_dir}")
        print("[discovery] 可通过在 state.json 中设置 output_dir 字段来修改")
    else:
        # 确保输出目录存在
        ensure_output_dir(state.output_dir)
        print(f"[discovery] 输出目录: {state.output_dir}")
    print("[discovery] 需求信息已确认")
    return state


def run_outline(state: WorkflowState) -> WorkflowState:
    """阶段2: 大纲生成"""
    topic = _infer_topic(state)
    state.approved_outline = {
        "titles": [
            f"{topic}：从低效到稳定产出的 5 步法",
            f"{topic}：一套可复用的内容流水线",
            f"{topic}：团队协作下的写作提效指南",
        ],
        "sections": [
            {"heading": "问题定义：为什么内容产出总是不稳定", "key_points": ["常见瓶颈", "质量波动原因"]},
            {"heading": "方法拆解：可执行的 5 步工作流", "key_points": ["选题", "大纲", "写作", "配图", "审核"]},
            {"heading": "落地建议：如何在团队中持续运行", "key_points": ["角色分工", "检查清单", "迭代机制"]},
        ],
        "platform_diff": {
            "wechat": "强调结构化和深度分析",
            "xiaohongshu": "强调场景化表达和高密度要点",
        },
    }
    print("[outline] 大纲已生成")
    return state


def run_draft(state: WorkflowState) -> WorkflowState:
    """阶段3: 初稿生成"""
    outline = state.approved_outline or {}
    titles = outline.get("titles", [])
    sections = outline.get("sections", [])
    title = titles[0] if titles else "社区内容创作实践"

    parts = [f"# {title}"]
    for sec in sections:
        heading = sec.get("heading", "章节")
        points = sec.get("key_points", [])
        parts.append(f"## {heading}")
        parts.append(
            "这部分围绕团队实际生产链路展开，重点说明问题背景、可执行动作与预期收益。"
        )
        if points:
            bullets = "\n".join([f"- {p}" for p in points])
            parts.append(bullets)

    parts.append("## 结语")
    parts.append("建议从一个固定主题试跑两周，用数据复盘流程效果并持续优化。")

    state.draft_v1 = "\n\n".join(parts)

    # 保存草稿到输出目录
    draft_path = save_draft_to_output(state, "draft_v1.md", state.draft_v1)
    if draft_path:
        print(f"[draft] 初稿已保存到: {draft_path}")

    print("[draft] 初稿已生成")
    return state


def run_finalize(state: WorkflowState) -> WorkflowState:
    """阶段4: 正式文章"""
    article = state.draft_v1 or "内容待补充"
    state.final_article_wechat = article

    # 小红书版本做轻量精简
    xhs_lines = []
    for line in article.splitlines():
        if line.startswith("## "):
            xhs_lines.append(line.replace("## ", "### "))
        elif line.startswith("- "):
            xhs_lines.append(f"• {line[2:]}")
        else:
            xhs_lines.append(line)
    state.final_article_xiaohongshu = "\n".join(xhs_lines)[:950]

    # 保存正式文章到输出目录
    wechat_path = save_draft_to_output(state, "final_article_wechat.md", state.final_article_wechat)
    xhs_path = save_draft_to_output(state, "final_article_xiaohongshu.md", state.final_article_xiaohongshu)
    if wechat_path:
        print(f"[finalize] 公众号文章已保存到: {wechat_path}")
    if xhs_path:
        print(f"[finalize] 小红书文章已保存到: {xhs_path}")

    print("[finalize] 双平台文章已生成")
    return state


def run_image_plan(state: WorkflowState) -> WorkflowState:
    """阶段5: 配图规划"""
    article = state.final_article_wechat or state.final_article_xiaohongshu or ""
    state.image_requirements = extract_image_requirements(article)
    print(f"[image-plan] 提取配图需求 {len(state.image_requirements or [])} 条")
    return state


def run_image_gen(state: WorkflowState) -> WorkflowState:
    """阶段6: 图片生成"""
    import urllib.request

    requirements = state.image_requirements or []
    assets = []
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 创建图片输出目录
    output_path = ensure_output_dir(state.output_dir)
    images_dir = output_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for i, req in enumerate(requirements, 1):
        asset = {
            "url": f"https://example.com/mock-image/{stamp}-{i}.png",
            "prompt": req.get("prompt", ""),
            "revised_prompt": req.get("prompt", ""),
            "width": 1024,
            "height": 1024,
            "provider": "mock",
            "status": "success",
            "position": req.get("position", f"位置 {i}"),
            "purpose": req.get("purpose"),
            "style": req.get("style"),
        }

        # 保存图片到本地（mock 模式下只是记录路径）
        local_filename = f"image_{stamp}_{i}.png"
        local_path = images_dir / local_filename
        asset["local_path"] = str(local_path)

        # 如果是真实 URL，尝试下载
        real_url = req.get("url") or asset["url"]
        if real_url and not real_url.startswith("https://example.com/"):
            try:
                urllib.request.urlretrieve(real_url, local_path)
                asset["downloaded"] = True
            except Exception as e:
                asset["downloaded"] = False
                asset["download_error"] = str(e)
        else:
            asset["downloaded"] = False
            asset["download_note"] = "mock 模式，未实际下载"

        assets.append(asset)

    state.image_assets = assets
    state.image_generation_log = assets
    print(f"[image-gen] 已生成 mock 图片 {len(assets)} 张")
    print(f"[image-gen] 图片目录: {images_dir}")
    return state


def run_compose(state: WorkflowState) -> WorkflowState:
    """阶段7: 图文整合"""
    article = state.final_article_wechat or state.final_article_xiaohongshu
    if not article:
        raise ValueError("compose 阶段缺少正式文章")
    images = state.image_assets or []
    platform = "wechat" if state.final_article_wechat else "xiaohongshu"
    state.composed_article = compose_article_with_images(article, images, platform=platform)
    print("[compose] 图文整合完成")
    return state


def run_review(state: WorkflowState) -> WorkflowState:
    """阶段8: 全文审核"""
    article = state.composed_article or state.final_article_wechat or ""
    title = infer_title_from_state(state, article)
    report = review_article_func(article=article, platform="wechat", title=title)
    state.review_report = report
    if report.get("passed"):
        state.final_publishable_article = article
        print("[review] 审核通过")
    else:
        print(f"[review] 审核未通过，问题数: {len(report.get('issues', []))}")
    return state


def run_publish(state: WorkflowState) -> WorkflowState:
    """阶段9: 发布"""
    import json

    article = state.final_publishable_article or state.composed_article
    if not article:
        raise ValueError("publish 阶段缺少可发布文章")

    title = infer_title_from_state(state, article)
    export = generate_export_package(
        article=article,
        images=state.image_assets or [],
        platform="wechat",
        title=title,
        tags=[],
    )
    state.export_package = export
    state.publish_result = {
        "success": False,
        "mode": "export_only",
        "reason": "MVP 默认导出，不直接调用平台 API",
    }

    # 保存导出包到输出目录
    output_path = ensure_output_dir(state.output_dir)
    export_dir = output_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # 保存文章
    safe_title = "".join(c for c in (title or "article") if c.isalnum() or c in " -_")[:50]
    article_file = export_dir / f"{safe_title}.md"
    article_file.write_text(article, encoding="utf-8")

    # 保存导出包 JSON
    export_json = export_dir / "export_package.json"
    export_json.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")

    # 保存手动发布步骤
    steps_file = export_dir / "manual_steps.txt"
    steps_content = "\n".join(export.get("manual_steps", []))
    steps_file.write_text(steps_content, encoding="utf-8")

    print(f"[publish] 导出包已保存到: {export_dir}")
    print(f"[publish] - 文章: {article_file}")
    print(f"[publish] - 元数据: {export_json}")
    print("[publish] 已生成导出发布包")
    return state


STAGE_HANDLERS = {
    Stage.DISCOVERY: run_discovery,
    Stage.OUTLINE: run_outline,
    Stage.DRAFT: run_draft,
    Stage.FINALIZE: run_finalize,
    Stage.IMAGE_PLAN: run_image_plan,
    Stage.IMAGE_GEN: run_image_gen,
    Stage.COMPOSE: run_compose,
    Stage.REVIEW: run_review,
    Stage.PUBLISH: run_publish,
}

STAGE_ORDER = [
    Stage.DISCOVERY,
    Stage.OUTLINE,
    Stage.DRAFT,
    Stage.FINALIZE,
    Stage.IMAGE_PLAN,
    Stage.IMAGE_GEN,
    Stage.COMPOSE,
    Stage.REVIEW,
    Stage.PUBLISH,
]


def run_pipeline(start_stage: Stage = Stage.DISCOVERY, state_path: str = "state.json"):
    """运行完整流程"""
    state = load_state(state_path)

    start_idx = STAGE_ORDER.index(start_stage)
    for stage in STAGE_ORDER[start_idx:]:
        handler = STAGE_HANDLERS[stage]
        print(f"[pipeline] 开始阶段: {stage.value}")

        try:
            state = handler(state)
        except Exception as e:
            print(f"[error] 阶段 {stage.value} 失败: {e}")
            print("[pipeline] 流程中止")
            save_state(state, state_path)
            return state

        # 推进到下一阶段
        next_idx = STAGE_ORDER.index(stage) + 1
        if next_idx < len(STAGE_ORDER):
            state = advance_stage(state, STAGE_ORDER[next_idx])

        save_state(state, state_path)

    print("[pipeline] 工作流完成!")
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", "-s", default="discovery")
    parser.add_argument("--state", "-f", default="state.json")
    args = parser.parse_args()

    run_pipeline(Stage(args.stage), args.state)
