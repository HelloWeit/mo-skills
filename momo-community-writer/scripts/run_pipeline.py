#!/usr/bin/env python3
"""
主流程编排入口
"""
import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state, advance_stage, Stage, WorkflowState
from scripts.compose_article import compose_article_with_images
from scripts.image_plan import extract_image_requirements
from scripts.publish import generate_export_package, infer_title_from_state
from scripts.review_article import review_article as review_article_func


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
    requirements = state.image_requirements or []
    assets = []
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for i, req in enumerate(requirements, 1):
        assets.append(
            {
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
        )
    state.image_assets = assets
    state.image_generation_log = assets
    print(f"[image-gen] 已生成 mock 图片 {len(assets)} 张")
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
