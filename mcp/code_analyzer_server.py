"""
MCP 代码质量分析器 — AI Coding 教学演示

本文件是一个 MCP Server，向 AI 助手（如 WorkBuddy）提供三个工具：
  1. analyze_file    — 分析单文件质量指标
  2. scan_directory  — 扫描目录代码文件
  3. compare_files   — 对比两个文件结构

技术栈：Python + FastMCP
运行方式：WorkBuddy 自动管理生命周期，无需手动启动
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# =========================================================================
# 创建 MCP Server 实例
# =========================================================================
mcp = FastMCP(
    "code-analyzer",
    instructions=(
        # 对该MCP server做介绍
        "代码质量分析工具 — 分析代码文件的行数、复杂度、函数结构、依赖导入等指标。"
        "支持 Python、JavaScript/TypeScript、Java、C++ 等多种语言。"
        "当你需要了解某个代码文件的质量状况、扫描项目目录结构、或对比两个文件的代码差异时使用。"
    )
)


# =========================================================================
#  工具 1：analyze_file — 分析单个代码文件
# =========================================================================
@mcp.tool(
    description="分析单个代码文件的质量指标，支持 lines（行数统计）、functions（函数结构）、"
                "complexity（圈复杂度估算）、imports（依赖分析）、summary（总览）。"
                "传入 'all' 分析所有指标，或传逗号分隔的指标名，如 'lines,functions'"
)
def analyze_file(
    file_path: str,
    metrics: str = "all"
) -> str:
    path = Path(file_path)

    # --- 文件存在性检查 ---
    if not path.exists():
        return json.dumps({"error": f"文件不存在：{file_path}"}, ensure_ascii=False)

    if not path.is_file():
        return json.dumps({"error": f"路径不是文件：{file_path}"}, ensure_ascii=False)

    # --- 读取文件 ---
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="gbk")
        except Exception:
            return json.dumps({"error": f"无法解码文件：{file_path}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"读取文件失败：{str(e)}"}, ensure_ascii=False)

    lines = content.splitlines()
    ext = path.suffix.lower()

    # 决定哪些指标要分析
    metric_list = ["lines", "functions", "complexity", "imports"] if metrics == "all" \
        else [m.strip().lower() for m in metrics.split(",")]

    valid_metrics = {"lines", "functions", "complexity", "imports"}
    requested = [m for m in metric_list if m in valid_metrics]

    result = {
        "file": str(path.resolve()),
        "extension": ext,
        "size_bytes": path.stat().st_size,
    }

    if "lines" in requested:
        result["lines"] = _analyze_lines(lines)

    if "functions" in requested or "complexity" in requested:
        functions = _extract_functions(content, ext)

    if "functions" in requested:
        result["functions"] = functions

    if "complexity" in requested:
        func_only = [f for f in functions if f["kind"] in ("function", "async_function")]
        for fn in func_only:
            fn["cyclomatic_complexity"] = _estimate_complexity(fn.get("body", ""))
        result["function_complexities"] = [
            {"name": f["name"], "line": f["line"], "complexity": f["cyclomatic_complexity"]}
            for f in func_only
        ]
        total_cx = sum(f["cyclomatic_complexity"] for f in func_only)
        result["total_complexity"] = total_cx
        avg_cx = round(total_cx / len(func_only), 1) if func_only else 0
        result["avg_complexity"] = avg_cx

    if "imports" in requested:
        result["imports"] = _extract_imports(content, ext)

    return json.dumps(result, ensure_ascii=False, indent=2)


# =========================================================================
#  工具 2：scan_directory — 扫描目录，统计所有代码文件
# =========================================================================
@mcp.tool(
    description="扫描指定目录，统计所有匹配文件扩展名的代码文件的基本信息（路径、大小、行数概览）。"
                "默认扫描 .py,.js,.ts,.java,.cpp,.h,.cs,.go,.rs,.rb 等常见扩展名"
)
def scan_directory(
    directory_path: str,
    extensions: str = ".py,.js,.ts,.java,.cpp,.h,.cs,.go,.rs,.rb,.php,.swift,.kt,.scala"
) -> str:
    """
    扫描目录并返回所有代码文件的摘要。

    参数
    ----
    directory_path : str
        要扫描的目录路径
    extensions     : str
        要包含的文件扩展名（逗号分隔），默认覆盖常见编程语言

    返回
    ----
    str : JSON 格式的目录扫描报告
    """
    path = Path(directory_path)

    if not path.exists():
        return json.dumps({"error": f"目录不存在：{directory_path}"}, ensure_ascii=False)

    if not path.is_dir():
        return json.dumps({"error": f"路径不是目录：{directory_path}"}, ensure_ascii=False)

    ext_list = [e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}"
                for e in extensions.split(",")]

    # 扫描文件（排除 common 无关目录）
    skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode",
                 "build", "dist", ".next", ".nuxt", "target", "bin", "obj", ".workbuddy"}
    skip_dirs_lower = {d.lower() for d in skip_dirs}

    files_info = []
    total_bytes = 0

    try:
        for root, dirs, filenames in os.walk(path):
            # 跳过无关目录
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs_lower]

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ext_list:
                    continue

                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                    total_bytes += size
                    rel_path = os.path.relpath(full_path, path)
                    files_info.append({
                        "relative_path": rel_path,
                        "extension": ext,
                        "size_bytes": size,
                        "size_kb": round(size / 1024, 1)
                    })
                except (OSError, PermissionError):
                    continue
    except PermissionError:
        return json.dumps({"error": f"无权限访问目录：{directory_path}"}, ensure_ascii=False)

    # 按扩展名分组统计
    ext_counts = {}
    for f in files_info:
        ext_counts[f["extension"]] = ext_counts.get(f["extension"], 0) + 1

    # 按类型排序
    ext_summary = [{"extension": ext, "count": count}
                    for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])]

    result = {
        "directory": str(path.resolve()),
        "total_files": len(files_info),
        "total_size_kb": round(total_bytes / 1024, 1),
        "by_extension": ext_summary,
        "files": sorted(files_info, key=lambda x: -x["size_bytes"])
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


# =========================================================================
#  工具 3：compare_files — 对比两个代码文件
# =========================================================================
@mcp.tool(
    description="对比两个代码文件的结构差异（行数、函数、导入、扩展名等维度）。"
                "适合用来快速了解两个文件在结构层面上的异同"
)
def compare_files(
    file_a: str,
    file_b: str
) -> str:
    """
    对比两个代码文件的结构信息。

    参数
    ----
    file_a : str
        第一个文件的绝对路径
    file_b : str
        第二个文件的绝对路径

    返回
    ----
    str : JSON 格式的对比报告
    """
    info_a = _quick_file_info(file_a)
    info_b = _quick_file_info(file_b)

    if not info_a or not info_b:
        missing = []
        if not info_a:
            missing.append(file_a)
        if not info_b:
            missing.append(file_b)
        return json.dumps({"error": f"以下文件无法读取：{'、'.join(missing)}"}, ensure_ascii=False)

    # 计算差异
    diff = {
        "size_bytes": info_b["size_bytes"] - info_a["size_bytes"],
        "total_lines": info_b["total_lines"] - info_a["total_lines"],
        "code_lines": info_b["code_lines"] - info_a["code_lines"],
        "comment_lines": info_b["comment_lines"] - info_a["comment_lines"],
        "blank_lines": info_b["blank_lines"] - info_a["blank_lines"],
        "func_count": info_b["func_count"] - info_a["func_count"],
        "class_count": info_b["class_count"] - info_a["class_count"],
        "import_count": info_b["import_count"] - info_a["import_count"],
    }

    result = {
        "file_a": info_a,
        "file_b": info_b,
        "difference": diff,
        "comparison_summary": (
            f"文件 A「{os.path.basename(file_a)}」vs 文件 B「{os.path.basename(file_b)}」：\n"
            f"  - B 比 A {'大' if diff['size_bytes'] >= 0 else '小'} {abs(diff['size_bytes'])} 字节\n"
            f"  - 代码行 B {'多' if diff['code_lines'] >= 0 else '少'} {abs(diff['code_lines'])} 行\n"
            f"  - 函数数量 B {'多' if diff['func_count'] >= 0 else '少'} {abs(diff['func_count'])} 个\n"
            f"  - 类数量 B {'多' if diff['class_count'] >= 0 else '少'} {abs(diff['class_count'])} 个"
        )
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


# =========================================================================
#  辅助函数
# =========================================================================

def _analyze_lines(lines: list[str]) -> dict:
    """统计行数：总行、代码行、注释行、空行"""
    total = len(lines)
    code = 0
    comments = 0
    blank = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            comments += 1
        elif stripped.startswith("--") or stripped.startswith("%"):
            comments += 1
        else:
            code += 1

    return {
        "total_lines": total,
        "code_lines": code,
        "comment_lines": comments,
        "blank_lines": blank,
        "comment_ratio": f"{round(comments / max(total, 1) * 100, 1)}%"
    }


def _extract_functions(content: str, ext: str) -> list[dict]:
    """提取文件中的函数/方法结构（支持 Python 和通用语言）"""
    functions = []

    if ext == ".py":
        return _extract_python_functions(content)
    else:
        # 通用正则匹配：function name(...) 或 name = (...) => 等模式
        patterns = [
            (r'(?:function\s+)?(\w+)\s*\([^)]*\)\s*\{', "function"),
            (r'(?:def|fun|func|fn)\s+(\w+)\s*\(', "function"),
            (r'(?:public|private|protected)?\s*(?:static\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+)?\s*\{', "method"),
            (r'class\s+(\w+)', "class"),
        ]
        for pattern, kind in patterns:
            for match in re.finditer(pattern, content):
                line_no = content[:match.start()].count("\n") + 1
                start = max(0, match.start() - 50)
                snippet = content[start:match.end() + 80]
                functions.append({
                    "name": match.group(1),
                    "line": line_no,
                    "kind": kind,
                    "body": snippet
                })
        return functions


def _extract_python_functions(content: str) -> list[dict]:
    """使用 AST 解析 Python 文件中的函数和类"""
    functions = []
    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                source_lines, _ = _get_node_source(content, node)
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "kind": "function",
                    "args_count": len(node.args.args),
                    "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                    "has_docstring": ast.get_docstring(node) is not None,
                    "body": source_lines or content
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                source_lines, _ = _get_node_source(content, node)
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "kind": "async_function",
                    "args_count": len(node.args.args),
                    "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                    "has_docstring": ast.get_docstring(node) is not None,
                    "body": source_lines or content
                })
            elif isinstance(node, ast.ClassDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "kind": "class",
                    "methods": sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
                    "has_docstring": ast.get_docstring(node) is not None,
                })

    except SyntaxError:
        # 如果是语法错误，回退到正则匹配
        return _extract_functions(content, ".py")

    return functions


def _get_node_source(content: str, node) -> tuple[str, int]:
    """获取 AST node 对应的源码片段"""
    try:
        lines = content.splitlines()
        start = max(0, node.lineno - 1)
        end = min(len(lines), getattr(node, 'end_lineno', node.lineno + 10))
        return "\n".join(lines[start:end]), end - start
    except Exception:
        return "", 0


def _estimate_complexity(body: str) -> int:
    """
    估算圈复杂度（McCabe Cyclomatic Complexity）。
    简化版：每个控制流分支 +1
    """
    if not body:
        return 1
    complexity = 1  # 基线
    # Python / 通用控制流关键词
    keywords = [
        r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
        r'\band\b', r'\bor\b', r'\bexcept\b', r'\bcase\b', r'\bwhen\b',
        r'\bcatch\b', r'\b&&\b', r'\bor\b', r'\?\s',
    ]
    for kw in keywords:
        complexity += len(re.findall(kw, body))
    return complexity


def _extract_imports(content: str, ext: str) -> list[dict]:
    """提取文件的导入/引用依赖"""
    imports = []

    if ext == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "source": alias.name,
                            "alias": alias.asname or None
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append({
                            "type": "from_import",
                            "source": module,
                            "name": alias.name,
                            "alias": alias.asname or None
                        })
        except SyntaxError:
            # 回退到正则
            for match in re.finditer(r'^(?:import|from)\s+(\S+)', content, re.MULTILINE):
                imports.append({"type": "statement", "raw": match.group(0).strip()})
    else:
        # 通用导入匹配
        patterns = [
            (r'(?:import|require)\s+[\'\"]([^\'\"]+)[\'\"]', "import"),
            (r'(?:from|using|include|import)\s+(\w+(?:\.\w+)*)', "import_statement"),
            (r'#include\s*[<\"]([^>\"]+)[>\"]', "include"),
        ]
        for pattern, kind in patterns:
            for match in re.finditer(pattern, content):
                imports.append({"type": kind, "value": match.group(1)})

    return imports


def _quick_file_info(file_path: str) -> Optional[dict]:
    """快速提取文件基本信息（供 compare_files 使用）"""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="gbk")
        except Exception:
            return None

    lines = content.splitlines()
    ext = path.suffix.lower()
    line_info = _analyze_lines(lines)
    functions = _extract_functions(content, ext)
    imports = _extract_imports(content, ext)

    return {
        "file": str(path.resolve()),
        "extension": ext,
        "size_bytes": path.stat().st_size,
        "total_lines": line_info["total_lines"],
        "code_lines": line_info["code_lines"],
        "comment_lines": line_info["comment_lines"],
        "blank_lines": line_info["blank_lines"],
        "func_count": len([f for f in functions if f["kind"] in ("function", "async_function")]),
        "class_count": len([f for f in functions if f["kind"] == "class"]),
        "import_count": len(imports),
    }


# =========================================================================
#  入口
# =========================================================================
if __name__ == "__main__":
    mcp.run()
