#!/usr/bin/env python3
"""检查Web端是否有新的未回答问题"""
import json, os
path = "/workspace/SCRIPTS/questions.json"
if not os.path.exists(path):
    print("📭 没有问题文件")
    exit()
with open(path) as f:
    qs = json.load(f)
pending = [q for q in qs if not q.get("answered")]
if pending:
    print(f"\n⚠️ 有 {len(pending)} 个未回答的问题！")
    for q in pending:
        print(f"   #{q['id']} [{q['user']}] {q['time']}")
        print(f"     问：{q['question'][:60]}")
        print()
else:
    print("✅ 所有问题都已回答")
