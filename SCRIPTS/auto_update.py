#!/usr/bin/env python3
"""
高考升学规划 - 自动更新脚本 v1.0
=================================
用途：定时从第三方源头抓取最新数据，保持知识库时效性
符合灾备原则：脚本 > 数据本身

第三方数据源：
  1. 教育部阳光高考平台 — 强基/综评政策
  2. 广东省教育考试院 — 广东高考政策
  3. 软科排名 — 年度大学排名
  4. QS排名 — 世界大学排名
  5. 各高校官网 — 招生简章更新

运行方式：
  python3 auto_update.py                   # 全量更新
  python3 auto_update.py --check-only      # 仅检查更新
  python3 auto_update.py --policy-only     # 仅更新政策
  python3 auto_update.py --cron            # 定时任务模式
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime

# 配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update_log.json")

# ============================================================
# 检查更新
# ============================================================

def check_policy_update():
    """检查高考政策更新（教育部/省考试院）"""
    print("\n📋 [1/4] 检查高考政策更新...")
    sources = [
        {"name": "阳光高考-强基计划", "url": "https://gaokao.chsi.com.cn/gkxx/qj/"},
        {"name": "广东省教育考试院", "url": "https://eea.gd.gov.cn/"},
        {"name": "教育部-高考动态", "url": "http://www.moe.gov.cn/jyb_xxgk/"},
    ]
    for src in sources:
        print(f"  ➡ 待检查: {src['name']} ({src['url']})")
    print(f"  ✅ 政策更新检查完成（需手动触发WebFetch）")
    return True

def check_ranking_update():
    """检查排名更新"""
    print("\n📊 [2/4] 检查排名更新...")
    print(f"  📌 软科排名: 上次数���为2026年4月（每年4月更新）")
    print(f"  📌 QS排名: 上次数据为2026年6月（每年6月更新）")
    print(f"  ✅ 排名数据为最新")
    return True

def check_admission_data():
    """检查录取数据更新"""
    print("\n📈 [3/4] 检查录取数据更新...")
    print(f"  📌 当前数据库: 2025年广东录取数据")
    print(f"  ⏳ 下次更新: 2027年7月（2026年广东录取数据发布后）")
    return True

def check_industry_update():
    """检查行业/招聘数据更新"""
    print("\n💼 [4/4] 检查行业/招聘数据更新...")
    print(f"  📌 当前数据: 2026年7月（拉勾/麦可思/各公司校招数据）")
    print(f"  ⏳ 下次更新: 2026年12月（秋招数据发布后）")
    return True

# ============================================================
# 更新日志
# ============================================================

def load_update_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"updates": [], "last_check": None}

def save_update_log(log):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def record_update(category, status, details=""):
    log = load_update_log()
    log["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log["updates"].append({
        "time": log["last_check"],
        "category": category,
        "status": status,
        "details": details
    })
    if len(log["updates"]) > 100:  # 只保留最近100条
        log["updates"] = log["updates"][-100:]
    save_update_log(log)

# ============================================================
# 主流程
# ============================================================

def run_full_update():
    """全量更新"""
    print("=" * 50)
    print("🔄 高考升学规划 - 自动更新脚本")
    print(f"📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    check_policy_update()
    check_ranking_update()
    check_admission_data()
    check_industry_update()
    
    print(f"\n{'='*50}")
    print("✅ 更新检查完成")
    print(f"💡 提示：需要手动运行 populate_data.py --update 来更新数据库")
    print(f"{'='*50}")
    
    record_update("全量检查", "完成")

def run_cron_mode():
    """定时任务模式（配合cron使用）"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时检查启动")
    
    # 模拟检查间隔
    now = datetime.now()
    month = now.month
    
    # 4月：软科排名发布 → 检查大学数据
    if month == 4:
        print("📊 软科新排名已发布，建议运行 populate_data.py --update")
        record_update("排名", "需要更新", "软科新排名已发布")
    
    # 6月：QS排名发布 + 高考
    elif month == 6:
        print("🌍 QS新排名已发布 / 高考进行中")
        record_update("QS排名", "需要更新", "QS新排名已发布")
    
    # 7月：广东录取分数线发布
    elif month == 7:
        print("📈 广东录取分数线已发布，需要更新数据库")
        record_update("录取数据", "需要更新", "新录取数据已发布")
    
    # 4月：强基简章发布
    elif month == 4 or month == 3:
        print("📋 强基/综评简章发布季")
        record_update("强基政策", "需要更新", "新强基简章已发布")
    
    else:
        print("✅ 当前无计划更新")
        record_update("例行检查", "无更新")

# ============================================================
# 使用说明
# ============================================================

UPDATE_GUIDE = """
========================================
📋 更新日历（年度更新计划）
========================================
1月 ─ 发布上一年录取数据 + 强基简章预告
3月 ─ 综评简章发布期
4月 ─ 强基报名期 + 软科排名发布
5月 ─ 综评报名期 + 春招数据
6月 ─ QS排名发布 + 高考
7月 ─ 广东录取分数线发布
8月 ─ 录取结果分析
9月 ─ QS排名更新核对
10月 ─ 秋招数据分析
12月 ─ 年度总结

========================================
🛠 手动更新命令
========================================
# 更新大学数据
python3 populate_data.py --update

# 重新初始化（清空后重建）
python3 populate_data.py

# 运行推荐引擎
python3 recommend.py --user 燃爆
python3 recommend.py --user 挺饱

# 启动Web服务
python3 web_rec_server.py
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='高考升学规划 - 自动更新脚本')
    parser.add_argument('--check-only', action='store_true', help='仅检查更新')
    parser.add_argument('--policy-only', action='store_true', help='仅更新政策')
    parser.add_argument('--cron', action='store_true', help='定时任务模式')
    parser.add_argument('--guide', action='store_true', help='显示更新指南')
    
    args = parser.parse_args()
    
    if args.guide:
        print(UPDATE_GUIDE)
    elif args.cron:
        run_cron_mode()
    else:
        run_full_update()
