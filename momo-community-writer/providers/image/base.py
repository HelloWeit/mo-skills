"""
图片生成抽象基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageResult:
    """图片生成结果"""
    url: str
    prompt: str
    revised_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: str = "png"


class ImageProvider(ABC):
    """图片生成 Provider 抽象基类"""

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> ImageResult:
        """生成图片"""
        pass

    @abstractmethod
    def edit(
        self,
        image_url: str,
        prompt: str,
        **kwargs
    ) -> ImageResult:
        """编辑图片"""
        pass
