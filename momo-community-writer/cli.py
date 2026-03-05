#!/usr/bin/env python3
"""
momo-community-writer CLI 入口
"""
import argparse
import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.generic_export import GenericExportAdapter
from scripts.run_pipeline import run_pipeline
from state import Stage, load_state, save_state


def main():
    parser = argparse.ArgumentParser(
        prog="momo-community-writer",
        description="社区文章创作与发布工作流，支持公众号与小红书"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行完整工作流")
    run_parser.add_argument("--stage", "-s", default="discovery",
                           help="从指定阶段开始 (default: discovery)")
    run_parser.add_argument("--state", "-f", default="state.json",
                           help="状态文件路径 (default: state.json)")

    # resume 命令
    resume_parser = subparsers.add_parser("resume", help="从中断处恢复")
    resume_parser.add_argument("--state", "-f", default="state.json",
                              help="状态文件路径 (default: state.json)")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出发布包")
    export_parser.add_argument("--state", "-f", default="state.json",
                              help="状态文件路径 (default: state.json)")
    export_parser.add_argument("--format", choices=["markdown", "html"],
                              default="markdown", help="导出格式 (default: markdown)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        run_pipeline(Stage(args.stage), args.state)
        return

    if args.command == "resume":
        state = load_state(args.state)
        run_pipeline(state.current_stage, args.state)
        return

    if args.command == "export":
        state = load_state(args.state)
        article = (
            state.final_publishable_article
            or state.composed_article
            or state.final_article_wechat
            or state.final_article_xiaohongshu
        )
        if not article:
            print("[error] 未找到可导出的文章内容")
            sys.exit(1)

        title = "未设置标题"
        outline = state.approved_outline or {}
        if isinstance(outline, dict):
            titles = outline.get("titles", [])
            if isinstance(titles, list) and titles:
                first = titles[0]
                if isinstance(first, str) and first.strip():
                    title = first.strip()

        adapter = GenericExportAdapter()
        export_pkg = adapter.export(
            title=title,
            content=article,
            images=state.image_assets or [],
            tags=[],
            format=args.format
        )
        state.export_package = asdict(export_pkg)
        save_state(state, args.state)
        print(f"[success] 导出包已写入 {args.state}")
        return


if __name__ == "__main__":
    main()
