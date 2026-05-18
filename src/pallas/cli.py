"""Pallas CLI — 知识工程工具集统一入口

用法:
    pallas match "分析新能源汽车市场"              # ToolForge 工具匹配
    pallas derive --project . --with-tools        # OntoDerive 推导
    pallas research "量子计算最新进展"              # Minerva 深度研究 (需 pip install pallas[full])
    pallas pipeline "分析市场" --full              # 全流程: match → derive → check
    pallas serve                                   # 启动 Agora + 注册所有 MCP 服务 (需 full)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _find_cli(cmd: str, pkg: str) -> str | None:
    """查找 CLI 路径（非代码级耦合，运行时发现）。返回路径或 None。"""
    path = shutil.which(cmd)
    if path:
        return cmd  # 在 PATH 中，用命令名即可
    # 检查当前 venv 的 bin 目录
    venv_bin = Path(sys.executable).parent
    full = venv_bin / cmd
    if full.exists():
        return str(full)
    print(f"⚠️  {cmd} CLI 未安装 → pip install pallas[{pkg}]")
    return None


def cmd_match(args):
    """Run ToolForge matching via ontoderive CLI."""
    cmd = [_ontoderive_cmd, "toolforge", args.goal]
    if args.context:
        cmd.extend(["--context", args.context])
    if args.inference_guide:
        cmd.append("--inference-guide")
    elif args.json:
        cmd.append("--json")
    subprocess.run(cmd)


def cmd_derive(args):
    """Run OntoDerive derivation."""
    cmd = [_ontoderive_cmd, "derive", "--project", args.project]
    if args.with_tools:
        cmd.append("--with-tools")
        if args.goal:
            cmd.extend(["--goal", args.goal])
        if args.tool_context:
            cmd.extend(["--tool-context", args.tool_context])
    subprocess.run(cmd)


def cmd_check(args):
    """Run OntoDerive protocol check."""
    cmd = [_ontoderive_cmd, "check", "--project", args.project]
    subprocess.run(cmd)


def cmd_pipeline(args):
    """Run the full pipeline: match → derive → check."""
    goal = args.goal
    project = args.project
    context = args.context or ""

    print(f"\n{'═' * 60}")
    print("  Pallas 全流程推导")
    print(f"  目标: {goal}")
    print(f"  项目: {project}")
    print(f"{'═' * 60}\n")

    # Step 1: ToolForge matching
    print("━ Step 1/3: ToolForge 工具匹配")
    cmd = [_ontoderive_cmd, "toolforge", goal, "--inference-guide"]
    if context:
        cmd.extend(["--context", context])
    subprocess.run(cmd)

    # Step 2: Derivation
    print("\n━ Step 2/3: OntoDerive 事实推导")
    cmd = [
        "ontoderive", "derive", "--project", project,
        "--with-tools", "--goal", goal,
    ]
    if context:
        cmd.extend(["--tool-context", context])
    subprocess.run(cmd)

    # Step 3: Protocol check
    print("\n━ Step 3/3: 规约检查")
    cmd = [_ontoderive_cmd, "check", "--project", project]
    subprocess.run(cmd)

    print(f"\n{'═' * 60}")
    print("  ✅ 全流程完成")
    print(f"  推导指导: {project}/inferences/_toolforge_guide.md")
    print(f"{'═' * 60}\n")


def cmd_init(args):
    """Initialize a new project."""
    cmd = [_ontoderive_cmd, "init", args.name]
    subprocess.run(cmd)
    print("\n💡 下一步:")
    print(f"   pallas pipeline --goal '你的目标' --project {args.name}")


def cmd_serve(args):
    """Start all services via Agora."""
    print("启动 Agora MCP Hub...")
    print("(需要 pip install pallas[agora])")
    if _find_cli("agora", "agora"):
        subprocess.run(["agora", "mcp"])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pallas",
        description="Pallas — 知识工程工具集统一入口 v0.1.0",
        epilog="示例: pallas pipeline --goal '分析新能源汽车市场' --project .",
    )
    sub = p.add_subparsers(dest="command", help="子命令")

    # match
    m = sub.add_parser("match", help="ToolForge 思维工具匹配")
    m.add_argument("goal", help="目标描述")
    m.add_argument("--context", default="", help="上下文关键词")
    m.add_argument("--inference-guide", action="store_true", help="输出推导指导")
    m.add_argument("--json", action="store_true", help="JSON 输出")

    # derive
    d = sub.add_parser("derive", help="OntoDerive 事实推导")
    d.add_argument("--project", default=".", help="项目路径")
    d.add_argument("--with-tools", action="store_true", help="前置 ToolForge 匹配")
    d.add_argument("--goal", default="", help="目标描述")
    d.add_argument("--tool-context", default="", help="ToolForge 上下文")

    # check
    c = sub.add_parser("check", help="规约检查")
    c.add_argument("--project", default=".", help="项目路径")

    # pipeline
    pl = sub.add_parser("pipeline", help="全流程: match → derive → check")
    pl.add_argument("--goal", required=True, help="目标描述")
    pl.add_argument("--project", default=".", help="项目路径")
    pl.add_argument("--context", default="", help="上下文关键词")

    # init
    i = sub.add_parser("init", help="初始化新项目")
    i.add_argument("name", help="项目名称")

    # serve
    sub.add_parser("serve", help="启动 Agora MCP Hub (需 pallas[full])")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # 运行时依赖检查：ontoderive CLI (非代码级耦合)
    global _ontoderive_cmd
    if args.command in ("match", "derive", "check", "pipeline", "init"):
        _ontoderive_cmd = _find_cli("ontoderive", "ontoderive")
        if not _ontoderive_cmd:
            return 1

    commands = {
        "match": cmd_match,
        "derive": cmd_derive,
        "check": cmd_check,
        "pipeline": cmd_pipeline,
        "init": cmd_init,
        "serve": cmd_serve,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
