"""
OpenAI 图片生成 Provider

使用 OpenAI Images API 进行图片生成。
文档: https://platform.openai.com/docs/api-reference/images
"""
import base64
import os
from typing import Optional

import httpx

from .base import ImageProvider, ImageResult


class OpenAIImageProvider(ImageProvider):
    """OpenAI DALL-E/GPT-Image 图片生成"""

    name = "openai"

    API_BASE = "https://api.openai.com/v1"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 未配置")

    def _get_size(self, width: int, height: int) -> str:
        """根据尺寸返回 OpenAI 支持的尺寸参数"""
        # DALL-E 3 支持的尺寸: 1024x1024, 1792x1024, 1024x1792
        # gpt-image-1 支持更多尺寸
        if width == height:
            return "1024x1024"
        elif width > height:
            return "1792x1024"
        else:
            return "1024x1792"

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        model: str = "gpt-image-1",
        quality: str = "standard",
        **kwargs
    ) -> ImageResult:
        """生成图片"""

        size = self._get_size(width, height)

        # gpt-image-1 使用新的 API 格式
        if model.startswith("gpt-image"):
            return self._generate_gpt_image(prompt, size, model, quality)
        else:
            # DALL-E 3
            return self._generate_dalle(prompt, size, model, quality)

    def _generate_gpt_image(
        self,
        prompt: str,
        size: str,
        model: str,
        quality: str
    ) -> ImageResult:
        """使用 gpt-image-1 API 生成图片"""

        url = f"{self.API_BASE}/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "output_format": "png",
            "response_format": "b64_json"  # 返回 base64
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"OpenAI API 错误 ({response.status_code}): {error_msg}")

            data = response.json()

        # 解析响应
        image_data = data.get("data", [])
        if not image_data:
            raise Exception("OpenAI API 未返回图片数据")

        first_image = image_data[0]
        b64_data = first_image.get("b64_json", "")
        revised_prompt = first_image.get("revised_prompt", prompt)

        # 保存为临时文件
        tmp_dir = os.environ.get("TMPDIR", "/tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        ext = "png"
        tmp_path = os.path.join(tmp_dir, f"openai_image_{os.getpid()}_{hash(b64_data) % 100000}.{ext}")

        with open(tmp_path, "wb") as f:
            f.write(base64.b64decode(b64_data))

        image_url = f"file://{tmp_path}"

        # 解析尺寸
        w, h = map(int, size.split("x"))

        return ImageResult(
            url=image_url,
            prompt=prompt,
            revised_prompt=revised_prompt,
            width=w,
            height=h,
            format="png"
        )

    def _generate_dalle(
        self,
        prompt: str,
        size: str,
        model: str,
        quality: str
    ) -> ImageResult:
        """使用 DALL-E 3 API 生成图片"""

        url = f"{self.API_BASE}/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
            "response_format": "url"  # DALL-E 3 返回 URL
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"OpenAI API 错误 ({response.status_code}): {error_msg}")

            data = response.json()

        # 解析响应
        image_data = data.get("data", [])
        if not image_data:
            raise Exception("OpenAI API 未返回图片数据")

        first_image = image_data[0]
        image_url = first_image.get("url", "")
        revised_prompt = first_image.get("revised_prompt", prompt)

        # 解析尺寸
        w, h = map(int, size.split("x"))

        return ImageResult(
            url=image_url,
            prompt=prompt,
            revised_prompt=revised_prompt,
            width=w,
            height=h,
            format="png"
        )

    def edit(
        self,
        image_url: str,
        prompt: str,
        model: str = "gpt-image-1",
        **kwargs
    ) -> ImageResult:
        """编辑图片"""

        url = f"{self.API_BASE}/images/edits"

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # 对于 gpt-image-1，使用新的编辑 API
        payload = {
            "model": model,
            "prompt": prompt,
            "image": image_url,  # 可以是 URL 或 base64
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = response.text
                raise Exception(f"OpenAI API 错误 ({response.status_code}): {error_msg}")

            data = response.json()

        image_data = data.get("data", [])
        if not image_data:
            raise Exception("OpenAI API 未返回图片数据")

        first_image = image_data[0]
        result_url = first_image.get("url", "") or first_image.get("b64_json", "")

        return ImageResult(
            url=result_url if result_url.startswith("http") else f"data:image/png;base64,{result_url}",
            prompt=prompt,
            revised_prompt=first_image.get("revised_prompt", prompt),
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024),
            format="png"
        )
