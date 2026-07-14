# 雪峰人AI 长期记忆库
# 创建：2026-07-14
# 用途：所有新会话必须先读这个文件，遵守以下规则
# ══════════════════════════════════════════════════════════════

## 1. 数据准确性铁律
(继承自 data_accuracy_rules.md)

### 校友信息：
- 必须确认本科在该校完整毕业
- 同一人只归属本科院校
- 不收录有重大争议或法律定罪的人

### 数据来源：
- 软科2026 / QS2026 / 各高校就业质量报告
- 标注来源、报告年份
- 不编造数据

## 2. 算法核心规则

### 分数→位次映射必须考虑学校实力（2026-07-14）
**重要：** 同一分数在不同学校对应的省排名差异巨大。

```
普通高中（前1000）→ 620分 ≈ 省排5000-15000
深圳头部高中（深中、深科、实验等）→ 620分 ≈ 省排1500-5000
广州头部高中（华附、执信等）→ 620分 ≈ 省排1200-4000
```

**规则：**
1. 顶级高中（深中、实验、深科、华附等）的省排要×0.3
2. 普通大湾区高中的省排×0.85（强基/综评资源）
3. 普通高中的省排×1.0
4. 同一分数在更强高中 = 更好的省排名

### 学生案例重要提醒
- **燃爆**：深圳科学高中（不是深圳中学）排名2
- **挺饱**：深北莫附中排名靠前

### 学校判断规则
```
深圳头部高中：深中、实验、深高级、深外、红岭、育才、科学高中(深科)、宝安中学、南山实验
广州头部高中：华附、执信、广雅、二中、省实
其他：按普通处理
```

## 3. 项目架构

### 当前部署
- 服务器：47.103.94.73 (xue.agilecdn.cn)
- HTTPS：Let's Encrypt (自动续期)
- 进程管理：Supervisor
- 反向代理：Nginx
- 巡检：check_server.py 每15分钟
- fail2ban：SSH爆破防护

### 报告生成路径（关键：自己来必须与燃爆/挺饱一致）
- 自己来(离线版) → rec_engine.js (前端JS算法)
- 燃爆/挺饱/自己来(在线版) → recommend.py (Python算法)
- 两个引擎必须产生相同结构的数据

### 报告标准字段（保持完全一致）
```
user_name, user_school, school_tier, school_size
estimated_score_min/max, estimated_province_rank_min/max
family_background, family_implication
exam_scores, exam_ranks
interests, weak_analysis
segment: {level, description}
chong_wen_bao: {chong, wen, bao}  (每个item: name, level, city, score, match)
qiangji: {recommended, reason, suitable_schools, tip_2026}  ← DICT 不是list
zongping: {recommended, reason, high_level, medium_level, tip}  ← DICT 不是list
majors: [{major, priority, reason, schools, suitable, note}]  ← 包含suitable
timeline: [{period, tasks}]  ← 用tasks不用events
future_outlook: {top_industries_10y, geo_impact, career_advice_10y, risk_warning}
top3_unis: [{name, level, source, stars}]
```

## 4. 设计原则

### 用户体验
- 自己来是主模块（不是按钮）
- 燃爆/挺饱作为示例案例放在底部
- 表单分3步，第三步用绿色提交按钮
- 所有信息本地持久化（IndexedDB可选）

### 数据展示
- 三星推荐是核心
- 校友信息有数据来源
- 就业数据分城市/行业/雇主

## 5. 同步与维护规则

### 三个数据源必须保持同步
- /workspace/SCRIPTS/ (沙箱)
- /workspace/vercel-deploy/ (GitHub Pages静态版)
- /workspace/gaokao-advisor-skill/ (GitHub Skill包)
- /opt/gaokao-advisor/ (服务器)

每次修改后：
1. 沙箱改完
2. 验证Playwright测试通过
3. 同步到vercel-deploy并git push
4. 同步到gaokao-advisor-skill
5. 上传到服务器

## 6. 常见错误与教训

### 2026-07-12：马云错误归入浙大
不要凭记忆/印象输出任何数据，必须逐人核实

### 2026-07-12：JS语法错误导致页面崩溃
不要在沙箱手动拼接HTML和JS字符串，必须用模板文件或正则替换

### 2026-07-14：分数预测没考虑学校实力
必须检查用户当前场景下的所有上下文（学校、地域、年级）

## 7. 训练与LLM

### 报告生成不依赖LLM
- 算法引擎（JS或Python）负责结构化输出
- LLM仅用于聊天功能（右下角浮动按钮）
- 报告内容是100%可控的规则输出
## 8. 重建HTML必须消除旧函数
**bug:** 反复在index_v2.html中inlined rec_engine.js时，旧的generateFullReport函数残留。
**症状:** 新版本修复不生效，旧函数被后加载覆盖新函数。
**修复:** 重建HTML前必须删除重复的函数定义。
**验证:** `grep -c "function generateFullReport" index_v2.html` 必须为1。

## 9. 深圳科学高中排名算法修正
- 同一分数在不同实力高中对应省排差异巨大
- 顶级高中（深中/深科/华附等）→ 分数 × 0.3 = 省排
- 大湾区高中 → 再 × 0.85

## 10. 预估分数范围算法（校强+排名→分数推高）
**核心逻辑：** 强校里排名靠前的学生，高考还有提升空间。
**公式（rec_engine.js + recommend.py 共享）：**
- rank <= 10 且 学校为头部高中 → 上限 = score + (11-rank)*3 + 15, 上限不超过+40
- rank <= 3 且 头部高中 → 下限 = score - 5（收窄强度）
- 其他 → 上限 = score + 15, 下限 = score - 15
**适用场景：** 用户输入645分#2深科 → 预估640-685分
**同步要求：** rec_engine.js 和 recommend.py 必须维护相同的算法

## 11. 工作机制：必须自己验证通过再告知用户
**铁律：** 所有修改必须在沙箱内完整测试通过后，再同步到服务器和告知用户。
**验证方式：** Playwright端到端测试或Node.js语法验证。
**绕过场景：** 纯数据内容修改（如新增就业数据）可直接部署。
**代码逻辑修改（如JS/Python算法）：** 必须测试后再同步。
