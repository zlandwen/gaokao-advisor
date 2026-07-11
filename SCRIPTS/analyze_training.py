#!/usr/bin/env python3
"""分析训练数据，生成用户洞察"""
import json, os
from collections import Counter

BASE = "/workspace/SCRIPTS"
DATA_FILE = os.path.join(BASE, "training_data.jsonl")
QUESTIONS_FILE = os.path.join(BASE, "questions.json")

def analyze():
    print("\n📊 训练数据分析")
    print("=" * 50)
    
    # 从questions.json获取结构化数据
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE) as f:
            qs = json.load(f)
        print(f"\n📝 总对话条数: {len(qs)}")
        
        # 按用户统计
        user_count = Counter(q["user"] for q in qs)
        for user, count in user_count.most_common():
            print(f"   {user}: {count} 条对话")
        
        # 话题分析
        topics = Counter()
        topic_map = {
            "专业": ["专业","学什么","方向","计算机","金融","医学","师范"],
            "学校": ["学校","大学","985","211","录取","分数"],
            "强基综评": ["强基","综评","南科大","港中深","校测"],
            "学习方法": ["怎么学","提分","提高","英语","数学","物理","语文"],
            "暑假规划": ["暑假","假期","安排","计划"],
            "焦虑情绪": ["焦虑","压力","累","坚持不住","烦","emo"],
            "未来方向": ["创业","接班","考研","考公","出国","留学"],
        }
        for q in qs:
            msg = q.get("question","")
            for topic, keywords in topic_map.items():
                if any(k in msg for k in keywords):
                    topics[topic] += 1
        
        print(f"\n📈 话题分布:")
        for topic, count in topics.most_common():
            bar = "█" * min(count, 20)
            print(f"   {topic}: {bar} {count}")
    
    # 从training_data.jsonl获取原始数据
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            lines = f.readlines()
        print(f"\n💾 训练数据文件: {len(lines)} 条记录")
        size = os.path.getsize(DATA_FILE)
        print(f"   文件大小: {size/1024:.1f}KB")
    
    print("\n" + "=" * 50)
    print("💡 训练数据持续积累中，可定期运行此脚本查看趋势")

if __name__ == "__main__":
    analyze()
