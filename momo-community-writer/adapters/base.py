"""
发布适配器抽象基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExportPackage:
    """降级导出包"""
    article: str
    title: str
    images: list
    tags: list[str]
    manual_steps: list[str]
    format: str = "markdown"


class PublishAdapter(ABC):
    """发布适配器抽象基类"""

    platform: str = "base"

    @abstractmethod
    def publish(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> PublishResult:
        """发布内容"""
        pass

    @abstractmethod
    def export(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> ExportPackage:
        """生成降级导出包"""
        pass
