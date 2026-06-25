"""
测试脚本：验证 MCP 代码质量分析器的各项功能

这个脚本直接调用 server 内部的函数（绕过了 MCP 协议层），
目的是快速验证分析逻辑是否正确，方便调试。
"""
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_analyzer_server import analyze_file, scan_directory, compare_files

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
PY_FILE = os.path.join(SAMPLES_DIR, "sample_code.py")
JS_FILE = os.path.join(SAMPLES_DIR, "sample_code.js")

print("=" * 60)
print("测试 1：analyze_file — 分析 Python 文件（all 指标）")
print("=" * 60)
result = json.loads(analyze_file(PY_FILE, "all"))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("测试 2：analyze_file — 仅分析 imports")
print("=" * 60)
result = json.loads(analyze_file(PY_FILE, "imports"))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("测试 3：analyze_file — 仅分析 complexity")
print("=" * 60)
result = json.loads(analyze_file(PY_FILE, "complexity"))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("测试 4：scan_directory — 扫描 samples 目录")
print("=" * 60)
result = json.loads(scan_directory(SAMPLES_DIR, ".py,.js"))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("测试 5：compare_files — 对比 .py 和 .js 文件")
print("=" * 60)
result = json.loads(compare_files(PY_FILE, JS_FILE))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("测试 6：analyze_file — 文件不存在")
print("=" * 60)
result = json.loads(analyze_file("/path/to/nonexistent.py", "all"))
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
print("所有测试完成！")
print("=" * 60)
