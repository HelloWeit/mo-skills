"""
Google 图片生成 Provider

使用 Imagen API 进行图片生成。
文档: https://ai.google.dev/imagen
"""
import base64
import os
from typing import Optional

import httpx

from .base import ImageProvider, ImageResult


class GoogleImageProvider(ImageProvider):
    """Google Imagen 图片生成"""

    name = "google"

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 未配置")

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """根据尺寸返回 Imagen 支持的宽高比"""
        ratio = width / height
        if ratio > 2:
            return "21:9"  # 接近 2.35:1
        elif ratio > 1.5:
            return "16:9"
        elif ratio > 1.2:
            return "4:3"
        elif ratio < 0.8:
            return "9:16"
        elif ratio < 0.95:
            return "3:4"
        return "1:1"

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        model: str = "imagen-4.0-generate-001",
        **kwargs
    ) -> ImageResult:
        """生成图片"""

        aspect_ratio = self._get_aspect_ratio(width, height)

        # Imagen API 使用 predict 方法
        url = f"{self.API_BASE}/models/{model}:predict"

        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"Google API 错误 ({response.status_code}): {error_msg}")

            data = response.json()

        # 解析响应，提取图片
        image_url = None
        image_data = None

        predictions = data.get("predictions", [])
        if predictions:
            pred = predictions[0]
            # Imagen 返回 bytesBase64Encoded
            if "bytesBase64Encoded" in pred:
                b64_data = pred["bytesBase64Encoded"]

                # 保存为临时文件
                tmp_dir = os.environ.get("TMPDIR", "/tmp")
                os.makedirs(tmp_dir, exist_ok=True)
                suffix = abs(hash(b64_data)) % 100000
                tmp_path = os.path.join(tmp_dir, f"google_imagen_{os.getpid()}_{suffix}.png")

                with open(tmp_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))

                image_url = f"file://{tmp_path}"
                image_data = b64_data
            elif "image" in pred:
                # 可能有不同的响应格式
                img_info = pred["image"]
                if isinstance(img_info, dict) and "bytesBase64Encoded" in img_info:
                    b64_data = img_info["bytesBase64Encoded"]
                    tmp_dir = os.environ.get("TMPDIR", "/tmp")
                    os.makedirs(tmp_dir, exist_ok=True)
                    suffix = abs(hash(b64_data)) % 100000
                    tmp_path = os.path.join(tmp_dir, f"google_imagen_{os.getpid()}_{suffix}.png")

                    with open(tmp_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))

                    image_url = f"file://{tmp_path}"
                    image_data = b64_data

        if not image_url and not image_data:
            raise Exception(f"未能从响应中提取图片。响应: {data}")

        return ImageResult(
            url=image_url or "",
            prompt=prompt,
            revised_prompt=prompt,  # Imagen 不返回修改后的 prompt
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
        """编辑图片 - Imagen 目前不支持图片编辑，返回新图片"""
        return self.generate(
            prompt=f"Based on this description, modify: {prompt}",
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024)
        )
