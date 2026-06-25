"""
完整的 MCP 协议冒烟测试
测试流程：initialize → initialized → tools/list → tools/call(analyze_file)
"""
import json
import subprocess
import sys
import os
import time

server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code_analyzer_server.py")
py_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", "sample_code.py")

requests = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "analyze_file",
                "arguments": {"file_path": py_file, "metrics": "lines,imports"}}},
]

input_data = "\n".join(json.dumps(r, ensure_ascii=False) for r in requests)

sp = subprocess.Popen(
    [sys.executable, server_path],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
out, err = sp.communicate(input=input_data.encode(), timeout=10)

print("=" * 60)
print("MCP 协议测试结果")
print("=" * 60)

lines = out.decode("utf-8", errors="replace").strip().split("\n")
for line in lines:
    try:
        parsed = json.loads(line.strip())
        rid = parsed.get("id")
        method = parsed.get("method", "")
        rsl = parsed.get("result")

        if "error" in parsed:
            print(f"\n[ERROR id={rid}] {json.dumps(parsed['error'], ensure_ascii=False)}")
        elif method == "notifications/message":
            continue
        elif rsl and "tools" in rsl:
            print(f"\n>> tools/list (id={rid}) — {len(rsl['tools'])} tools:")
            for t in rsl["tools"]:
                desc = t.get("description", "")[:60]
                schema = t.get("inputSchema", {})
                props = list(schema.get("properties", {}).keys()) if schema else []
                print(f"  ├─ {t['name']}")
                print(f"  │  desc: {desc}")
                print(f"  │  params: {props}")
            print()
        elif rsl and "content" in rsl:
            print(f"\n>> tools/call (id={rid}) — result:")
            for c in rsl.get("content", []):
                if c.get("type") == "text":
                    text = c["text"]
                    try:
                        data = json.loads(text)
                        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
                    except json.JSONDecodeError:
                        print(text[:500])
            print()
        elif rsl:
            print(f"\n>> Other response (id={rid}): {json.dumps(rsl, ensure_ascii=False)[:200]}")
    except json.JSONDecodeError:
        pass

if err:
    err_text = err.decode("utf-8", errors="replace")
    if err_text.strip():
        print(f"\n[STDERR] {err_text[:500]}")

print("\n" + "=" * 60)
print("协议测试完成!")
print("=" * 60)
