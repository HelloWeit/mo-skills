"""
Google 图片生成 Provider

使用 Gemini API 进行图片生成。
文档: https://ai.google.dev/gemini-api/docs/image-generation
"""
import base64
import os
from typing import Optional

import httpx

from .base import ImageProvider, ImageResult


class GoogleImageProvider(ImageProvider):
    """Google Gemini 图片生成"""

    name = "google"

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 未配置")

    def _get_size_params(self, width: int, height: int) -> tuple[str, str]:
        """根据尺寸返回 Gemini 支持的尺寸参数"""
        # Gemini 支持的尺寸: "256x256", "512x512", "1024x1024" 等
        if width == height:
            if width <= 256:
                return "256x256", "256x256"
            elif width <= 512:
                return "512x512", "512x512"
            elif width <= 1024:
                return "1024x1024", "1024x1024"
        # 非正方形，使用最接近的尺寸
        return "1024x1024", f"{width}x{height}"

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        model: str = "gemini-2.0-flash-exp",
        **kwargs
    ) -> ImageResult:
        """生成图片"""

        gemini_size, original_size = self._get_size_params(width, height)

        # 构建请求体
        # 参考: https://ai.google.dev/gemini-api/docs/image-generation
        url = f"{self.API_BASE}/models/{model}:generateContent"

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Generate an image: {prompt}"
                }]
            }],
            "generationConfig": {
                "responseModalities": ["image", "text"],
                "imageSizes": [gemini_size]
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"Google API 错误 ({response.status_code}): {error_msg}")

            data = response.json()

        # 解析响应，提取图片
        image_url = None
        image_data = None

        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                # 检查是否有 inline_data (base64 编码的图片)
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    mime_type = inline_data.get("mimeType", "image/png")
                    b64_data = inline_data.get("data", "")

                    # 保存为临时文件并返回 URL
                    ext = mime_type.split("/")[-1] if "/" in mime_type else "png"

                    # 使用系统临时目录
                    tmp_dir = os.environ.get("TMPDIR", "/tmp")
                    os.makedirs(tmp_dir, exist_ok=True)
                    suffix = abs(hash(b64_data)) % 100000
                    tmp_path = os.path.join(tmp_dir, f"google_image_{os.getpid()}_{suffix}.{ext}")

                    with open(tmp_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))

                    image_url = f"file://{tmp_path}"
                    image_data = b64_data
                    break
                # 检查是否有 URL
                elif "fileData" in part:
                    file_data = part["fileData"]
                    image_url = file_data.get("fileUri", "")
                    break

        if not image_url and not image_data:
            raise Exception("未能从响应中提取图片")

        return ImageResult(
            url=image_url or "",
            prompt=prompt,
            revised_prompt=prompt,  # Google 不返回修改后的 prompt
            width=width,
            height=height,
            format="png"
        )

    def edit(
        self,
        image_url: str,
        prompt: str,
        **kwargs
    ) -> ImageResult:
        """编辑图片 - Gemini 目前不支持图片编辑，返回新图片"""
        # Gemini 的图片编辑能力有限，这里简化为重新生成
        return self.generate(
            prompt=f"Based on this description, modify: {prompt}",
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024)
        )
