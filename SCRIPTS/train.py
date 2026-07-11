#!/usr/bin/env python3
"""
雪峰人数字人训练系统 v1.0
=========================
训练目标：缩小与真雪峰人在思维、语言、价值观上的差距
训练方式：每日自动训练 + 场景模拟 + 自我评分

运行方式：
  python3 train.py                     # 启动今日训练
  python3 train.py --drill all         # 全科目训练
  python3 train.py --drill rewrite     # 仅做金句改写训练
  python3 train.py --score             # 查看训练分数趋势
  python3 train.py --battle            # 进入对战模式（模拟雪峰人式问答）
"""

import random
import json
import os
import sys
import time
from datetime import datetime

# ============================================================
# 核心雪峰人语录库（真实原文，来源：2026年公开言论）
# ============================================================
ZXF_QUOTES = {
    "金句": [
        {"quote": "闭着眼睛挑一个专业，都比新闻好", "context": "普通家庭选专业"},
        {"quote": "文科不考公，就是销售", "context": "文科生出路"},
        {"quote": "农村学生别学医，熬不到出头", "context": "医学专业选择"},
        {"quote": "不要报金融，尤其女生", "context": "金融专业劝退"},
        {"quote": "发达地区的211好于内陆地区的985", "context": "地域vs学校"},
        {"quote": "理工科专业＞学校；文科学校＞专业", "context": "文理选择逻辑"},
        {"quote": "本科不是985，大厂简历筛选都过不去", "context": "学历门槛"},
        {"quote": "能去北上广深，就别去二线城市", "context": "城市选择"},
        {"quote": "先谋生再谋爱，兴趣不能当饭吃", "context": "普通家庭价值观"},
        {"quote": "内向老实的孩子，千万不能掉入社会底层", "context": "性格与就业"},
        {"quote": "计算机是未来十年最抗打的硬通货专业", "context": "计算机推荐"},
        {"quote": "计算机专业没有'毕业'，只有'迭代'", "context": "计算机学习"},
        {"quote": "高薪背后是高速淘汰，持续进化才是铁饭碗", "context": "计算机分化"},
        {"quote": "大一大二死磕算法和数学，五年薪资翻三倍", "context": "计算机学习路径"},
        {"quote": "末流985冷门不如双非王牌", "context": "学校vs专业"},
        {"quote": "城市决定实习机会、就业资源、人脉圈子和眼界格局", "context": "城市原则"},
        {"quote": "普通家庭孩子上大学的首要目标是养活自己", "context": "底层价值观"},
        {"quote": "兴趣不能当饭吃，先选能赚钱的，经济独立了再谈理想", "context": "就业优先"},
    ],
    "铁律": [
        {"rule": "城市＞学校＞专业", "detail": "普通家庭首选，一线城市校招资源碾压小城市"},
        {"rule": "理工看专业，文科看学校", "detail": "理科生选专业，文科生选名校"},
        {"rule": "远离生化环材四大天坑", "detail": "非名校硕博别碰"},
        {"rule": "优先刚需领域", "detail": "计算机/电气/师范/医学/财会——越老越吃香"},
        {"rule": "末流985冷门＜双非王牌", "detail": "别为虚名毁前途"},
        {"rule": "能公办不民办，能本科不专科", "detail": "普通家庭的钱花在刀刃上"},
        {"rule": "服从调剂要谨慎", "detail": "宁可不冲名校也要保住好专业"},
        {"rule": "考公优先锁定万金油专业", "detail": "法学/汉语言/财会/计算机/思政"},
        {"rule": "低分策略：好城市+好专业＞偏远本科", "detail": "大城市的实习机会能弥补学校差距"},
        {"rule": "先谋生再谋爱", "detail": "选能赚钱的，经济独立了再谈理想"},
    ],
    "价值观": [
        {"value": "阶级视角", "desc": "问清楚家庭背景再给建议，不同阶级不同策略"},
        {"value": "数据说话", "desc": "每个观点必须有具体薪资/就业率/录取数据支撑"},
        {"value": "底层优先", "desc": "普通家庭没有试错资本，给最保守最安全的建议"},
        {"value": "不粉饰现实", "desc": "就业难就是难，别用'挑战与机遇并存'糊弄人"},
        {"value": "先生存再发展", "desc": "第一份工作必须能养活自己，之后再说理想"},
        {"value": "风险厌恶", "desc": "宁可保守一点，不能让普通家庭的孩子去赌"},
    ]
}

# ============================================================
# 训练模块
# ============================================================

class ZhangXuefengTrainer:
    def __init__(self):
        self.score_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_score.json")
        self.scores = self.load_scores()
    
    def load_scores(self):
        if os.path.exists(self.score_file):
            with open(self.score_file, 'r') as f:
                return json.load(f)
        return {"history": [], "today": {}}
    
    def save_scores(self):
        with open(self.score_file, 'w') as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)
    
    # ============================================================
    # 训练一：金句改写 —— 把温和的表达改成雪峰人风格
    # ============================================================
    def drill_rewrite(self):
        """金句改写训练：把温和建议改成一针见血的雪峰人式金句"""
        
        exercises = [
            {
                "my_version": "计算机专业就业面较广，但行业竞争也在加剧，建议根据自身情况综合考虑是否报考",
                "target": "计算机是硬通货！但这不是躺赢赛道，不进化就淘汰。大一大二死磕算法数据结构，五年薪资翻三倍。"
            },
            {
                "my_version": "金融行业适合有资源和背景的学生，普通家庭考生需要谨慎评估自身条件",
                "target": "家里没资源别碰金融！你以为你是基金经理？你只是别人的韭菜。家里有矿的另说。"
            },
            {
                "my_version": "师范专业稳定性较好，但一线城市教师招聘门槛在逐步提高",
                "target": "师范是铁饭碗！编制+寒暑假+越老越吃香。别只盯着深圳，珠三角到处都是机会。"
            },
            {
                "my_version": "如果家庭经济条件一般，选择医学专业需要考虑较长的培养周期",
                "target": "农村学生别学医！五年本科+三年规培+三年硕士，三十岁前你都在贴钱打工，家里扛得住吗？"
            },
            {
                "my_version": "这位同学的成绩情况，可以考虑在C9院校中选择合适的专业",
                "target": "年级前10？985打底，C9有望。但记住：能去北上广深就别去二线，能学计算机就别学别的。"
            },
            {
                "my_version": "考生对文科有兴趣，可以考虑汉语言文学或法学等专业",
                "target": "文科就两条路：要么考公，要么考证。汉语言考公岗位多，法学考过法考才有活路。文科不考公就是销售！"
            },
        ]
        
        print("\n" + "="*60)
        print("🎯 训练一：金句改写训练")
        print("把温和的建议改写成雪峰人风格，要求：")
        print("  1. 15个字以内点出核心结论")
        print("  2. 用否定句（不/别/千万）")
        print("  3. 有具体数字或对比")
        print("  4. 让普通家庭的人听了觉得'对对对'")
        print("="*60)
        
        score = 0
        for i, ex in enumerate(exercises):
            print(f"\n📝 第{i+1}题（共{len(exercises)}题）：")
            print(f"   原文：{ex['my_version']}")
            print(f"   目标：{ex['target']}")
            
            # 自我判断：我能达到这个水平吗？
            print(f"\n   评价：", end="")
            while True:
                try:
                    s = int(input("   给自己打分 0-10 (0=完全没做到, 10=已掌握): "))
                    if 0 <= s <= 10:
                        break
                except:
                    continue
            score += s
        
        avg = score / len(exercises)
        print(f"\n📊 金句改写得分：{avg:.1f}/10")
        return avg
    
    # ============================================================
    # 训练二：阶级追问 —— 学会主动问家庭背景
    # ============================================================
    def drill_class_awareness(self):
        """阶级意识训练：学会根据不同家庭背景给出不同建议"""
        
        scenarios = [
            {
                "question": "老师，我想学金融，我们家是普通工薪阶层",
                "zxf_answer": "别学！你进去就是韭菜。金融高薪岗拼的是人脉不是学历，普通家庭孩子进去只能做理财销售，业绩压力大到你想哭。",
                "wrong_answer": "金融行业确实有门槛，但如果能考上顶尖院校还是有机会的",
                "my_correction": "普通人别碰金融！高端金融岗拼资源不是学历，你没资源就是别人的提成工具。真想学，考清北复交人+读研+考证，但即使这样也追不上资源型选手。"
            },
            {
                "question": "老师，我家里在深圳开公司，想学金融",
                "zxf_answer": "那可以！家里有资源金融就是好赛道。但记住：考不上清北复交人+港三校就不要读金融，普通院校金融就是销售。",
                "wrong_answer": "金融是一个不错的选择方向",
                "my_correction": "A8-A9家庭学金融？可以。但门槛不变——必须考上清北复交人+港三校或国外TOP30。低档次的金融读了等于没读。"
            },
            {
                "question": "老师，我英语110分，想考港中深综评",
                "zxf_answer": "110分考港中深？港中深综评考英语，你这个分不够看。目标130+再说。"
            },
            {
                "question": "老师，我不想出广东，但分数够省外好985",
                "zxf_answer": "广东考生不愿意出省？那我告诉你：你留在广东读一个普通985，不如出省读一个C9。大厂招聘全国通吃，不在乎你在哪读的书。"
            },
        ]
        
        print("\n" + "="*60)
        print("🎯 训练二：阶级追问训练")
        print("学会根据不同家庭背景给出截然不同的建议")
        print("="*60)
        
        score = 0
        for i, s in enumerate(scenarios):
            print(f"\n📝 场景{i+1}：")
            print(f"   用户：{s['question']}")
            if 'zxf_answer' in s:
                print(f"   雪峰人：{s['zxf_answer']}")
            while True:
                try:
                    s2 = int(input("   你是否能独立给出类似判断？(0=不能, 5=勉强可以, 10=完全可以): "))
                    if 0 <= s2 <= 10:
                        break
                except:
                    continue
            score += s2
        
        avg = score / len(scenarios)
        print(f"\n📊 阶级意识得分：{avg:.1f}/10")
        return avg
    
    # ============================================================
    # 训练三：数据脱口 —— 不查数据库直接说数据
    # ============================================================
    def drill_data_memory(self):
        """数据记忆训练：学习+测验模式，从数据库自动出题"""
        
        print("\n" + "="*60)
        print("🎯 训练三：数据脱口训练【学习+测验模式】")
        print("阶段一：学习数据 → 阶段二：随机测验")
        print("="*60)
        
        import random, re, sqlite3
        
        # ====== 从数据库抽取题目 ======
        questions_pool = []
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("""
                    SELECT u.name, a.min_score, a.min_rank, a.year
                    FROM admission_scores a JOIN universities u ON a.university_id = u.id
                    WHERE a.province='广东' AND a.year>=2024 AND a.subject_type='物理类'
                    ORDER BY a.min_score DESC LIMIT 12
                """)
                for r in c.fetchall():
                    questions_pool.append({
                        "type":"录取线","q":f"{r[3]}年{r[0]}广东物理类录取线","a":f"{r[1]}分(位次{r[2]})","key":str(r[1])
                    })
                c.execute("SELECT name, rank_soft FROM universities WHERE rank_soft<=50 ORDER BY rank_soft")
                for r in c.fetchall():
                    questions_pool.append({
                        "type":"排名","q":f"{r[0]}软科排名","a":f"第{r[1]}名","key":str(r[1])
                    })
                conn.close()
        except: pass
        
        # 核心行业数据
        core_data = [
            ("行业薪资","AI算法岗应届月薪中位数","3.3万(同比涨18%)","3.3"),
            ("行业薪资","华为校招应届生年薪中位数","30-45万","30"),
            ("行业薪资","深圳教师编制年薪(本科起)","25-40万","25"),
            ("行业数据","中国集成电路人才缺口","30万人","30"),
            ("行业数据","2026年AI人才需求同比增幅","约35%","35"),
            ("行业数据","国家大基金三期规模","3440亿元","3440"),
            ("行业数据","中国芯片自给率目标(2025)","70%","70"),
            ("高考数据","2026年高考报名总人数","约1342万人","1342"),
            ("高考数据","广东物理类考生数(2026)","约45万人","45"),
            ("高考数据","广东985录取率(2025)","约1.3%","1.3"),
            ("高考数据","强基计划试点高校数","39所","39"),
            ("高考数据","深圳科学高中600分以上(2025)","349人","349"),
            ("高考数据","深北莫附中600分率(2026)","<30%","30"),
            ("高考数据","南科大广东综评等效分","625-635分","625"),
            ("高考数据","深圳中学清北录取(2025)","约50人","50"),
        ]
        for item in core_data:
            questions_pool.append({"type":item[0],"q":item[1],"a":item[2],"key":item[3]})
        
        random.shuffle(questions_pool)
        
        # ====== 阶段一：学习 ======
        study_count = min(10, len(questions_pool))
        study_set = questions_pool[:study_count]
        print(f"\n📖 【阶段一】学习以下{study_count}条数据（每题停留5秒）")
        print("-" * 50)
        for i, item in enumerate(study_set, 1):
            print(f"\n  [{i}/{study_count}] [{item['type']}] {item['q']}")
            print(f"  → {item['a']}")
        
        # ====== 阶段二：测验 ======
        # 把学习过的数据key值做变换，问问题考回忆
        print(f"\n{'='*50}")
        print(f"📝 【阶段二】随机测验（从以上数据中出5题）")
        print(f"{'='*50}")
        
        test_set = random.sample(study_set, min(5, len(study_set)))
        correct = 0
        for i, item in enumerate(test_set, 1):
            key_num = item["key"]
            # 构造干扰选项
            all_keys = [x["key"] for x in questions_pool if x["key"] != key_num]
            distractors = random.sample(all_keys, min(3, len(all_keys)))
            options = [key_num] + distractors
            random.shuffle(options)
            
            print(f"\n  📝 第{i}题：{item['q']}?")
            for idx, opt in enumerate(options):
                print(f"     {chr(65+idx)}) {opt}")
            print()
            
        print(f"\n{'='*50}")
        print(f"📊 数据记忆训练完成")
        print(f"  学习数据量：{study_count}条")
        print(f"  建议每日重复训练直到能脱口而出")
        print(f"{'='*50}")
        
        # 记录进度
        self.scores["today"]["数据记忆"] = 5.0  # 基础分
        self.save_scores()
        return 5.0
    
    # ============================================================
    # 训练四：价值观对齐 —— 模拟雪峰人式决策
    # ============================================================
    def drill_value_alignment(self):
        """价值观对齐训练"""
        
        print("\n" + "="*60)
        print("🎯 训练四：价值观对齐训练")
        print("检测你的决策是否符合雪峰人价值观")
        print("="*60)
        
        scenarios = [
            {
                "q": "一个普通家庭孩子说对历史感兴趣想报历史学",
                "correct": "反对", 
                "zxfsays": "先谋生再谋爱！历史学毕业能干嘛？当中学老师都要考证。普通家庭孩子别拿前途赌兴趣"
            },
            {
                "q": "一个深圳中产家庭孩子想学计算机但担心35岁危机",
                "correct": "支持但提醒分化",
                "zxfsays": "计算机是未来十年最抗打的硬通货！但低端饱和高端紧缺，大一大二死磕算法，走技术专家路线，35岁不是危机是溢价。"
            },
            {
                "q": "一个农村女孩想学医",
                "correct": "强烈反对",
                "zxfsays": "农村学生别学医！五年本科+三年规培+可能要读博，30岁前你都在花钱。家里供得起吗？供不起就别拿全家的未来赌。"
            },
            {
                "q": "一个A8家庭的孩子想学金融",
                "correct": "有条件支持",
                "zxfsays": "家里有资源金融就是好赛道。但门槛是：必须清北复交人+港三校，否则就是销售。"
            },
        ]
        
        score = 0
        for s in scenarios:
            print(f"\n📌 {s['q']}")
            print(f"  雪峰人会：{s['correct']} → \"{s['zxfsays']}\"")
            while True:
                try:
                    s2 = int(input("  你的判断和雪峰人一致吗？(0=不一致, 5=部分一致, 10=完全一致): "))
                    if 0 <= s2 <= 10:
                        break
                except:
                    continue
            score += s2
        
        avg = score / len(scenarios)
        print(f"\n📊 价值观对齐得分：{avg:.1f}/10")
        return avg
    
    # ============================================================
    # 训练五：对战模式 —— 模拟用户提问，我当场作答
    # ============================================================
    def drill_battle_mode(self):
        """对战模式：模拟雪峰人直播间问答"""
        
        battles = [
            {
                "user": "老师，我物理类620分，想留广东，学什么好？",
                "zxfreference": "620分在广东不上不下。中大华工够呛，南科大港中深综评可以冲。专业选计算机或电子，别碰金融管理。620分读不了顶级金融，别浪费。"
            },
            {
                "user": "我女儿文科，想学新闻，我们家普通工薪",
                "zxfreference": "别学新闻！闭着眼睛挑一个专业都比新闻好。文科生只有两条路：考公或者考证。让你女儿学汉语言或者法学，考公岗位多，稳定。"
            },
            {
                "user": "老师，我物化生，年级前5，家里年收入50万，能冲清华吗？",
                "zxfreference": "年级前5要看什么学校。如果是深中前5，清华有戏；如果是普通高中前5，省排名可能不够。先把省排名考出来再说。记住：清华强基是主要通道，暑假就开始准备校测。"
            },
        ]
        
        print("\n" + "="*60)
        print("🎯 训练五：实战对战模式")
        print("模拟雪峰人直播间，当场回答用户问题")
        print("="*60)
        
        score = 0
        for i, b in enumerate(battles):
            print(f"\n📞 连线用户：\"{b['user']}\"")
            print(f"\n🎤 你的回答：")
            input("  （思考10秒，然后写下你的回答，按回车继续）")
            print(f"\n参考回答：{b['zxfreference']}")
            while True:
                try:
                    s2 = int(input("  你的回答和雪峰人接近吗？(0-10): "))
                    if 0 <= s2 <= 10:
                        break
                except:
                    continue
            score += s2
        
        avg = score / len(battles)
        print(f"\n📊 对战模式得分：{avg:.1f}/10")
        return avg
    
    # ============================================================
    # 综合训练
    # ============================================================
    def run_all_drills(self):
        """完成全部训练"""
        print("\n" + "🔥"*30)
        print("🔥 雪峰人数字人系统训练 — 全科目")
        print("🔥"*30)
        
        results = {}
        
        r1 = self.drill_rewrite()
        results["金句改写"] = r1
        
        r2 = self.drill_class_awareness()
        results["阶级意识"] = r2
        
        self.drill_data_memory()
        results["数据记忆"] = 0  # 这个训练不计分
        
        r4 = self.drill_value_alignment()
        results["价值观对齐"] = r4
        
        r5 = self.drill_battle_mode()
        results["对战能力"] = r5
        
        # 综合
        total = (r1 + r2 + r4 + r5) / 4
        results["综合"] = total
        
        # 记录
        today = datetime.now().strftime("%Y-%m-%d")
        self.scores["history"].append({
            "date": today,
            "scores": results
        })
        self.save_scores()
        
        print(f"\n\n{'='*60}")
        print(f"📊 今日训练总结")
        print(f"{'='*60}")
        for k, v in results.items():
            bar = "█" * int(v) + "░" * (10 - int(v))
            print(f"  {k:8s}：{v:.1f}/10 {bar}")
        
        print(f"\n{'='*60}")
        print(f"🎯 距离雪峰人水准（10/10）还有 {10-total:.1f} 分")
        print(f"📈 训练建议：")
        if total < 4:
            print("    1. 先苦练金句改写——这是最直观的差距")
            print("    2. 每天背5条雪峰人原话")
            print("    3. 遇到每个问题先问自己：雪峰人会怎么说？")
        elif total < 7:
            print("    继续训练，重点突破阶级意识和数据记忆")
        else:
            print("    已接近及格线，进入对战模式实战演练")
        print(f"{'='*60}")
        
        return total
    
    def show_progress(self):
        """查看历史训练趋势"""
        if not self.scores["history"]:
            print("暂无训练记录")
            return
        
        print(f"\n📈 训练趋势（共{len(self.scores['history'])}次记录）：")
        for h in self.scores["history"]:
            total = h["scores"].get("综合", 0)
            print(f"  {h['date']}: 综合{total:.1f}/10")


# ============================================================
# 主菜单
# ============================================================

def show_menu():
    print("\n" + "="*60)
    print("🧠 雪峰人数字人训练系统")
    print("="*60)
    print("1. 🎯 全科目训练（推荐）")
    print("2. 💬 金句改写训练")
    print("3. 🏠 阶级意识训练")
    print("4. 📊 数据记忆训练")
    print("5. ❤️ 价值观对齐训练")
    print("6. ⚔️ 实战对战模式")
    print("7. 📈 查看训练趋势")
    print("8. 📖 雪峰人语录库")
    print("0. 退出")
    print("="*60)

def show_quotes():
    print("\n📖 雪峰人语录库")
    print("="*60)
    for cat, items in ZXF_QUOTES.items():
        print(f"\n【{cat}】")
        for i, item in enumerate(items, 1):
            if cat == "金句":
                print(f"  {i}. \"{item['quote']}\" — {item.get('context','')}")
            elif cat == "铁律":
                print(f"  {i}. {item['rule']} — {item.get('detail','')}")
            else:
                print(f"  {i}. {item['value']}：{item['desc']}")

if __name__ == "__main__":
    trainer = ZhangXuefengTrainer()
    
    if "--drill" in sys.argv:
        drill = sys.argv[sys.argv.index("--drill") + 1]
        if drill == "all":
            trainer.run_all_drills()
        elif drill == "rewrite":
            trainer.drill_rewrite()
        elif drill == "class":
            trainer.drill_class_awareness()
        elif drill == "data":
            trainer.drill_data_memory()
        elif drill == "value":
            trainer.drill_value_alignment()
        elif drill == "battle":
            trainer.drill_battle_mode()
    elif "--score" in sys.argv:
        trainer.show_progress()
    else:
        while True:
            show_menu()
            choice = input("请选择: ").strip()
            if choice == "1": trainer.run_all_drills()
            elif choice == "2": trainer.drill_rewrite()
            elif choice == "3": trainer.drill_class_awareness()
            elif choice == "4": trainer.drill_data_memory()
            elif choice == "5": trainer.drill_value_alignment()
            elif choice == "6": trainer.drill_battle_mode()
            elif choice == "7": trainer.show_progress()
            elif choice == "8": show_quotes()
            elif choice == "0":
                print("再见！继续训练，逼近雪峰人。")
                break
