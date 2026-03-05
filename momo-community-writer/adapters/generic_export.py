"""
通用导出适配器（兜底）
"""
from .base import PublishAdapter, PublishResult, ExportPackage


class GenericExportAdapter(PublishAdapter):
    """通用导出适配器，仅生成导出包不实际发布"""

    platform = "generic"

    def publish(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> PublishResult:
        """通用适配器不支持直接发布"""
        return PublishResult(
            success=False,
            error="通用适配器仅支持导出，请使用 export() 方法"
        )

    def export(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        format: str = "markdown",
        **kwargs
    ) -> ExportPackage:
        """生成通用导出包"""
        return ExportPackage(
            article=content,
            title=title,
            images=images or [],
            tags=tags or [],
            format=format,
            manual_steps=[
                "1. 复制正文内容",
                "2. 下载图片资源",
                "3. 登录目标平台",
                "4. 粘贴内容并插入图片",
                "5. 发布"
            ]
        )
