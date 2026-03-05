"""
公众号发布适配器
"""
import os
from .base import PublishAdapter, PublishResult, ExportPackage


class WeChatOfficialAdapter(PublishAdapter):
    """微信公众号发布适配器"""

    platform = "wechat_official"

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("WECHAT_APP_ID")
        self.app_secret = app_secret or os.getenv("WECHAT_APP_SECRET")

    def publish(
        self,
        title: str,
        content: str,
        images: list = None,
        tags: list = None,
        **kwargs
    ) -> PublishResult:
        """发布到公众号"""
        if not self.app_id or not self.app_secret:
            return PublishResult(
                success=False,
                error="WECHAT_APP_ID 或 WECHAT_APP_SECRET 未配置"
            )

        # TODO: 实现公众号 API 发布逻辑
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
        """生成公众号降级导出包"""
        return ExportPackage(
            article=content,
            title=title,
            images=images or [],
            tags=tags or [],
            manual_steps=[
                "1. 登录微信公众平台 (mp.weixin.qq.com)",
                "2. 进入「素材管理」→「新建图文」",
                "3. 填入标题和正文内容",
                "4. 按位置说明上传并插入图片",
                "5. 设置封面图、摘要、标签",
                "6. 保存并发布"
            ]
        )
