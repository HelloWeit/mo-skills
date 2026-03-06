"""
状态管理模块 - state.json 读写工具
"""
import json
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel
from enum import Enum


class Stage(str, Enum):
    DISCOVERY = "discovery"
    OUTLINE = "outline"
    DRAFT = "draft"
    FINALIZE = "finalize"
    IMAGE_PLAN = "image-plan"
    IMAGE_GEN = "image-gen"
    COMPOSE = "compose"
    REVIEW = "review"
    PUBLISH = "publish"


class StateRecord(BaseModel):
    """单次迭代记录"""
    stage: Stage
    version: int
    changes: list[str] = []
    pending_questions: list[str] = []
    artifacts: dict[str, Any] = {}


class WorkflowState(BaseModel):
    """完整工作流状态"""
    current_stage: Stage = Stage.DISCOVERY
    version: int = 1
    history: list[StateRecord] = []

    # 输出目录配置
    output_dir: Optional[str] = None  # 用户指定的输出目录

    # 各阶段产出
    intent_brief: Optional[dict] = None
    constraints: Optional[dict] = None
    success_criteria: Optional[list] = None
    approved_outline: Optional[dict] = None
    draft_v1: Optional[str] = None
    final_article_wechat: Optional[str] = None
    final_article_xiaohongshu: Optional[str] = None
    image_requirements: Optional[list] = None
    image_assets: Optional[list] = None
    image_generation_log: Optional[list] = None
    composed_article: Optional[str] = None
    review_report: Optional[dict] = None
    final_publishable_article: Optional[str] = None
    publish_result: Optional[dict] = None
    export_package: Optional[dict] = None


def load_state(path: str | Path = "state.json") -> WorkflowState:
    """加载状态文件"""
    path = Path(path)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkflowState(**data)
    return WorkflowState()


def save_state(state: WorkflowState, path: str | Path = "state.json") -> None:
    """保存状态文件"""
    path = Path(path)
    path.write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8"
    )


def advance_stage(state: WorkflowState, next_stage: Stage) -> WorkflowState:
    """推进到下一阶段"""
    record = StateRecord(
        stage=state.current_stage,
        version=state.version,
        changes=[],
        pending_questions=[]
    )
    state.history.append(record)
    state.current_stage = next_stage
    state.version += 1
    return state
