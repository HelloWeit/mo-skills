#!/usr/bin/env python3
"""
图片生成脚本

Usage:
    python scripts/generate_images.py --provider google --state state.json
    python scripts/generate_images.py --help
"""
import argparse
import os
import sys

# 添加父目录到 path 以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state
from providers.image import GoogleImageProvider, OpenAIImageProvider


def check_api_key(provider: str) -> tuple[bool, str]:
    """检查 API Key 是否配置"""
    if provider == "google":
        key = os.getenv("GOOGLE_API_KEY")
        if key:
            return True, f"GOOGLE_API_KEY 已配置 ({key[:8]}...)"
        return False, "GOOGLE_API_KEY 未配置，请设置环境变量: export GOOGLE_API_KEY=your_key"
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key:
            return True, f"OPENAI_API_KEY 已配置 ({key[:8]}...)"
        return False, "OPENAI_API_KEY 未配置，请设置环境变量: export OPENAI_API_KEY=your_key"
    return False, f"未知 provider: {provider}"


def get_provider(provider: str):
    """获取 provider 实例"""
    if provider == "google":
        return GoogleImageProvider()
    elif provider == "openai":
        return OpenAIImageProvider()
    raise ValueError(f"不支持的 provider: {provider}")


def generate_image(
    prompt: str,
    provider: str,
    width: int = 1024,
    height: int = 1024,
    **kwargs
) -> dict:
    """调用图片生成 API"""
    try:
        p = get_provider(provider)
        result = p.generate(prompt, width=width, height=height, **kwargs)
        return {
            "url": result.url,
            "prompt": result.prompt,
            "revised_prompt": result.revised_prompt,
            "width": result.width,
            "height": result.height,
            "provider": provider,
            "status": "success"
        }
    except Exception as e:
        return {
            "url": "",
            "prompt": prompt,
            "provider": provider,
            "status": "failed",
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="图片生成脚本 - 从 state.json 读取 image_requirements 并生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/generate_images.py --provider google
    python scripts/generate_images.py --provider openai --state state.json

环境变量:
    GOOGLE_API_KEY    Google Gemini API Key
    OPENAI_API_KEY    OpenAI API Key
        """
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["google", "openai"],
        default="google",
        help="图片生成 provider (default: google)"
    )
    parser.add_argument(
        "--state", "-s",
        default="state.json",
        help="状态文件路径 (default: state.json)"
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=1024,
        help="图片宽度 (default: 1024)"
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=1024,
        help="图片高度 (default: 1024)"
    )

    args = parser.parse_args()

    # 检查 API Key
    has_key, msg = check_api_key(args.provider)
    if not has_key:
        print(f"[error] {msg}")
        sys.exit(1)
    print(f"[info] {msg}")

    # 加载状态
    state = load_state(args.state)

    if not state.image_requirements:
        print("[error] 未找到配图需求，请先完成 image-plan 阶段")
        print("[hint] state.json 中需要 image_requirements 字段")
        sys.exit(1)

    print(f"[info] 发现 {len(state.image_requirements)} 个配图需求")

    # 生成图片
    assets = []
    logs = []
    success_count = 0
    fail_count = 0

    for i, req in enumerate(state.image_requirements, 1):
        prompt = req.get("prompt", "")
        position = req.get("position", f"位置 {i}")

        print(f"\n[info] 生成图片 {i}/{len(state.image_requirements)}: {position}")
        print(f"       Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")

        result = generate_image(
            prompt=prompt,
            provider=args.provider,
            width=args.width,
            height=args.height
        )
        result["position"] = position
        if "purpose" in req:
            result["purpose"] = req.get("purpose")
        if "style" in req:
            result["style"] = req.get("style")

        assets.append(result)
        logs.append(result)

        if result["status"] == "success":
            success_count += 1
            print(f"       ✓ 成功: {result['url'][:60]}...")
        else:
            fail_count += 1
            print(f"       ✗ 失败: {result.get('error', '未知错误')}")

    # 保存状态
    state.image_assets = assets
    state.image_generation_log = logs
    save_state(state, args.state)

    print(f"\n[summary] 生成完成: 成功 {success_count}, 失败 {fail_count}")
    print(f"[info] 结果已写入 {args.state}")


if __name__ == "__main__":
    main()
