"""
小红书发布适配器
"""
import os
from .base import PublishAdapter, PublishResult, ExportPackage


class XiaohongshuAdapter(PublishAdapter):
    """小红书发布适配器"""

    platform = "xiaohongshu"

    def __init__(self, cookie: str = None):
        self.cookie = cookie or os.getenv("XIAOHONGSHU_COOKIE")

    def publish(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> PublishResult:
        """发布到小红书"""
        if not self.cookie:
            return PublishResult(
                success=False,
                error="XIAOHONGSHU_COOKIE 未配置"
            )

        # TODO: 实现小红书 API/CDP 发布逻辑
        return PublishResult(
            success=False,
            error="待实现"
        )

    def export(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> ExportPackage:
        """生成小红书降级导出包"""
        # 转换标签格式
        formatted_tags = [f"#{tag}" for tag in (tags or [])]

        return ExportPackage(
            article=content,
            title=title,
            images=images or [],
            tags=formatted_tags,
            manual_steps=[
                "1. 打开小红书 APP 或创作者中心",
                "2. 点击「+」发布笔记",
                "3. 上传图片（建议 3-9 张）",
                "4. 填写标题（限 20 字）",
                "5. 填写正文（限 1000 字）",
                "6. 添加话题标签",
                "7. 发布"
            ]
        )
