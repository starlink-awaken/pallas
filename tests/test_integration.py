#!/usr/bin/env python3
"""Pallas 全工具集成测试 — 验证所有工具的命令和API"""

import json
import subprocess
import sys
from pathlib import Path

PASS = 0
FAIL = 0

def test(name, cmd, expect_in_output=None, expect_exit=0):
    global PASS, FAIL
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        exit_ok = result.returncode == expect_exit if isinstance(expect_exit, int) else True
        content_ok = True
        if expect_in_output:
            content_ok = all(e in output for e in expect_in_output)
        if exit_ok and content_ok:
            print(f"  ✅ {name}")
            PASS += 1
        else:
            print(f"  ❌ {name}")
            if not exit_ok:
                print(f"     exit={result.returncode} (expected {expect_exit})")
            if not content_ok and expect_in_output:
                missing = [e for e in expect_in_output if e not in output]
                print(f"     missing: {missing}")
                print(f"     output[:200]: {output[:200]}")
            FAIL += 1
        return result
    except Exception as e:
        print(f"  ❌ {name} — exception: {e}")
        FAIL += 1
        return None

import shutil

# 查找 ontoderive CLI：先搜 PATH，再回退到同级项目 venv
def _find_cli(name):
    # 优先检查 Workspace 同级项目 venv（避免 brew 安装的 stub）
    script_dir = Path(__file__).resolve().parent.parent
    workspace = script_dir.parent
    venv_path = workspace / name / ".venv" / "bin" / name
    if venv_path.exists():
        return str(venv_path)
    p = shutil.which(name)
    if p:
        return p
    return name

ONTODERIVE = _find_cli("ontoderive")
AGORA = _find_cli("agora")
PALLAS = _find_cli("pallas")
ONTODERIVE_ENGINE = str(Path(__file__).resolve().parent.parent.parent / "ontoderive" / "engine")

print("=" * 60)
print("  Pallas 全工具集成测试")
print("=" * 60)

# ═══ OntoDerive CLI ═══
print("\n━━━ OntoDerive CLI ━━━")
test("ontoderive --help",
     f"{ONTODERIVE} --help",
     ["init", "derive", "check", "rounds", "toolforge"])

test("ontoderive init",
     f"{ONTODERIVE} init test-verify",
     ["已初始化"])

test("ontoderive derive",
     f"{ONTODERIVE} derive --project test-verify",
     ["事实基座扫描", "事实="])

test("ontoderive check",
     f"{ONTODERIVE} check --project test-verify",
     ["规约检查", "/"])

test("ontoderive toolforge",
     f"{ONTODERIVE} toolforge '分析新能源汽车市场' --context '竞争,政策'",
     ["波特五力", "匹配度"])

test("ontoderive toolforge --inference-guide",
     f"{ONTODERIVE} toolforge '设计数字化平台' --context '政府,教育' --inference-guide",
     ["推导指导", "推荐推导框架"])

test("ontoderive toolforge --json",
     f"{ONTODERIVE} toolforge '产业园区规划' --context '区域,创新' --json",
     ["id", "name", "score"])

test("ontoderive derive --with-tools",
     f"{ONTODERIVE} derive --project examples/z-park --with-tools --goal '中关村科技园区'",
     ["ToolForge", "事实基座扫描"])

# ═══ ToolForge Python API ═══
print("\n━━━ ToolForge Python API ━━━")

api_test = """
import sys; sys.path.insert(0, 'ENGINE_PATH')
from toolforge import ToolForge

tf = ToolForge()

# 1. match
r = tf.match('分析新能源汽车市场', '竞争,政策')
assert r['methodologies'], 'no methodologies matched'
print('match: OK')

# 2. select
s = tf.select('设计数字化平台', '政府,教育', top_n=5)
assert len(s) > 0, 'no tools selected'
assert s[0]['score'] >= s[-1]['score'], 'not sorted by score'
print('select: OK')

# 3. to_inference_guide
guide2 = tf.to_inference_guide('产业园区规划', '区域,创新')
assert '推荐推导框架' in guide2
print('to_inference_guide: OK')

# 4. catalog integrity
tools = tf.catalog['tools']
assert len(tools) >= 50, f'only {len(tools)} tools'
categories = set(t['category'] for t in tools)
assert len(categories) == 6, f'expected 6 categories, got {len(categories)}'
ids = [t['id'] for t in tools]
assert len(ids) == len(set(ids)), 'duplicate IDs'
print(f'catalog: {len(tools)} tools, {len(categories)} categories')

# 5. score ordering
for cat, tools_in_cat in r.items():
    if tools_in_cat:
        scores = [t['score'] for t in tools_in_cat]
        assert scores == sorted(scores, reverse=True), f'{cat} not sorted'
print('score_ordering: OK')

print('All ToolForge API tests passed')
""".replace('ENGINE_PATH', ONTODERIVE_ENGINE)

result = subprocess.run(
    [sys.executable, "-c", api_test],
    capture_output=True, text=True, timeout=30
)
if result.returncode == 0:
    print(f"  ✅ ToolForge API (6 checks)")
    PASS += 1
else:
    print(f"  ❌ ToolForge API — {result.stderr[:200]}")
    FAIL += 1

# ═══ Agora CLI ═══
print("\n━━━ Agora CLI ━━━")
test("agora --help",
     f"{AGORA} --help",
     ["register", "pipeline", "pipelines"])

test("agora pipelines",
     f"{AGORA} pipelines",
     ["match-derive", "research-derive", "derive-check", "full-pipeline"])

# ═══ Pallas CLI ═══
print("\n━━━ Pallas CLI ━━━")
test("pallas --help",
     f"{PALLAS} --help",
     ["match", "derive", "check", "pipeline", "init"])

test("pallas init",
     f"{PALLAS} init test-pallas-verify",
     ["已初始化"])

test("pallas match",
     f"{PALLAS} match '分析新能源汽车市场' --context '竞争,政策'",
     ["波特五力", "匹配度"])

test("pallas derive",
     f"{PALLAS} derive --project test-verify --with-tools --goal '分析市场'",
     ["ToolForge", "事实="])

test("pallas check",
     f"{PALLAS} check --project test-verify",
     ["规约检查", "/"])

test("pallas pipeline (full)",
     f"ONTODERIVE_LLM_BACKEND=none {PALLAS} pipeline --goal '中关村科技园区创新生态' --project examples/z-park --context '区域,创新'",
     ["全流程完成", "通过"])

# ═══ 清理 ═══
print("\n━━━ 清理测试项目 ━━━")
subprocess.run("rm -rf test-verify test-pallas-verify", shell=True)
print("  ✅ 清理完成")

# ═══ 总结 ═══
print(f"\n{'=' * 60}")
print(f"  结果: {PASS} 通过, {FAIL} 失败")
if FAIL == 0:
    print(f"  ✅ 全部 {PASS} 项测试通过")
else:
    print(f"  ❌ {FAIL} 项测试失败")
print(f"{'=' * 60}")

sys.exit(0 if FAIL == 0 else 1)
