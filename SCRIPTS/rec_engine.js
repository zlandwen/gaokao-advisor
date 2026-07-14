// ═════════════════════════════════════════════════════════════════
// 雪峰人AI - 前端推荐引擎（离线版）
// 移植自 recommend.py，数据结构与之完全一致
// 数据来源：knowledge_base.db (软科2026排名)
// ═════════════════════════════════════════════════════════════════

var GAOKAO_DB = null;

function loadRecommendDB() {
  if (GAOKAO_DB) return;
  var el = document.getElementById('recDB');
  if (!el) return;
  try { GAOKAO_DB = JSON.parse(el.textContent); } catch(e) {}
}

// ====== 分数段判断 ======
function scoreToSegment(score) {
  if (score >= 680) return 'S段'; if (score >= 660) return 'A+段';
  if (score >= 640) return 'A段'; if (score >= 610) return 'B+段';
  if (score >= 580) return 'B段'; if (score >= 500) return 'C段';
  return 'D段';
}

function segmentDesc(score) {
  if (score >= 680) return '清北复交浙科南 — 强基主通道';
  if (score >= 660) return 'C9院校 — 强基+高考双通道';
  if (score >= 640) return '中坚985 — 强基+综评+高考';
  if (score >= 610) return '211/综评985 — 综评冲985，高考稳211';
  if (score >= 580) return '深大/华师/广工 — 保研+考研路径';
  if (score >= 500) return '普通一本 — 考研改变命运';
  return '专科/二本 — 专升本+考研长期规划';
}

// ====== 查找匹配高校 ======
function findSchools(subject, score) {
  if (!GAOKAO_DB || !GAOKAO_DB.universities) return [];
  var unis = GAOKAO_DB.universities || [];
  var scores = GAOKAO_DB.scores || [];
  var qjUnis = GAOKAO_DB.qj_unis || [];
  var zpUnis = GAOKAO_DB.zp_unis || [];
  var result = [];
  
  for (var i = 0; i < unis.length; i++) {
    var u = unis[i];
    var matchedScore = null;
    for (var j = 0; j < scores.length; j++) {
      if (scores[j].name === u.name) { matchedScore = scores[j].score; break; }
    }
    var diff = matchedScore ? score - matchedScore : 0;
    var match = '';
    if (matchedScore) {
      if (diff >= 5) match = 'chong';
      else if (diff >= -5) match = 'wen';
      else if (diff >= -20) match = 'bao';
      else match = 'diwen';
    } else { match = 'wen'; }
    
    result.push({
      name: u.name, level: u.level, city: u.city, rank_soft: u.rank,
      score: matchedScore, match: match, diff: diff,
      hasQJ: qjUnis.indexOf(u.name) >= 0,
      hasZP: zpUnis.indexOf(u.name) >= 0
    });
  }
  
  result.sort(function(a, b) {
    var order = { 'chong': 0, 'wen': 1, 'bao': 2, 'diwen': 3 };
    var oa = order[a.match] || 99, ob = order[b.match] || 99;
    if (oa !== ob) return oa - ob;
    return Math.abs(a.diff) - Math.abs(b.diff);
  });
  return result;
}

// ====== 冲稳保 ======
function getChongWenBao(profile) {
  var score = profile.estimated_score || 600;
  var all = findSchools('', score);
  return {
    chong: all.filter(function(u) { return u.match === 'chong'; }).slice(0, 4),
    wen: all.filter(function(u) { return u.match === 'wen'; }).slice(0, 4),
    bao: all.filter(function(u) { return u.match === 'bao'; }).slice(0, 3)
  };
}

// ====== 强基分析（返回dict，与Python一致）======
function getQiangji(profile) {
  var score = profile.estimated_score || 600;
  var all = findSchools('', score);
  var qj = all.filter(function(u) { return u.hasQJ && u.match !== 'diwen'; }).slice(0, 5);
  if (qj.length === 0) return { recommended: false, reason: "", suitable_schools: [], tip_2026: "" };
  
  var schoolNames = qj.map(function(u) { return u.name; });
  var hasTop = qj.some(function(u) { return u.rank_soft <= 10; });
  
  return {
    recommended: true,
    reason: "你目前的分数适合走强基计划通道。强基计划高考占比85%+校测15%，适合数理基础好的学生。",
    suitable_schools: schoolNames,
    tip_2026: hasTop ? "暑假开始准备目标校的强基校测笔试（数学+物理）" : "强基可降5-15分入围，但需确认目标校是否在广东有强基名额"
  };
}

// ====== 综评分析 ======
function getZongping(profile) {
  var score = profile.estimated_score || 600;
  var zpUnis = (GAOKAO_DB && GAOKAO_DB.zp_unis) || [];
  if (zpUnis.length === 0 || score < 550) {
    return { recommended: false, reason: "", high_level: [], medium_level: [], tip: "" };
  }
  var all = findSchools('', score);
  var high = [], medium = [];
  for (var i = 0; i < zpUnis.length; i++) {
    var name = zpUnis[i];
    var found = null;
    for (var j = 0; j < all.length; j++) {
      if (all[j].name === name) { found = all[j]; break; }
    }
    if (found && found.match !== 'diwen') {
      if (found.match === 'chong' || found.match === 'wen') high.push(name);
      else medium.push(name);
    }
  }
  return {
    recommended: high.length > 0 || medium.length > 0,
    reason: "广东省综合评价录取：高考60%+校测30%+学考10%，可降10-20分录取。",
    high_level: high.slice(0, 3),
    medium_level: medium.slice(0, 3),
    tip: "综评需要在5月前完成报名，提前准备校测（南科大：数理机考；港中深：英语机考+面试）"
  };
}

// ====== 专业推荐 ======
function getMajorRecommendations(profile) {
  var score = profile.estimated_score || 600;
  var family = profile.family_background || '';
  var goal = profile.interests || '';
  var isWealthy = family.indexOf('A8') >= 0 || family.indexOf('开公司') >= 0 || family.indexOf('高净值') >= 0 || family.indexOf('富裕') >= 0;
  var isTeacher = goal.indexOf('老师') >= 0 || goal.indexOf('师范') >= 0 || goal.indexOf('教书') >= 0;
  var allUnis = findSchools('', score);
  
  function pickTop(filterFn) {
    var picks = allUnis.filter(filterFn).slice(0, 3);
    return picks.map(function(u) { return [u.name, u.level]; });
  }
  
  function eligible(filterFn) {
    return allUnis.filter(filterFn).length > 0;
  }
  
  var majors = [];
  var csReason = isWealthy ? "想创业？计算机是最好的起点。" : "计算机是硬通货，不进化就淘汰。";
  majors.push({
    major: '计算机科学与技术', priority: '🥇 强推', reason: csReason,
    schools: pickTop(function(u) { return u.match !== 'diwen'; }),
    suitable: true, note: '雪峰人：低端饱和高端缺人。大一大二死磕算法和数学。'
  });
  
  if (score >= 620) {
    var aiNote = '想做AI算法得读到硕博。';
    majors.push({
      major: '人工智能', priority: score >= 640 ? '🥇 强推' : '🥈 推荐',
      reason: '未来十年最热赛道，2026年AI岗薪资涨18%。',
      schools: pickTop(function(u) { return u.match !== 'diwen'; }),
      suitable: true, note: aiNote
    });
  }
  
  if (score >= 580) {
    majors.push({
      major: '集成电路/电子', priority: '🥇 强推',
      reason: '卡脖子领域，大基金3440亿砸进去，人才缺口30万。',
      schools: pickTop(function(u) { return u.match !== 'diwen'; }),
      suitable: true, note: '雪峰人：唯一可以靠国家战略吃饭的专业。'
    });
  }
  
  if (score >= 580) {
    majors.push({
      major: '机器人工程', priority: '🥈 推荐',
      reason: '制造业升级+老龄化，机器人需求只增不减。',
      schools: pickTop(function(u) { return u.match !== 'diwen'; }),
      suitable: true, note: '深圳大疆优必选都在招，动手能力越强越吃香。'
    });
  }
  
  majors.push({
    major: '师范（公费师范生/信息技术方向）', priority: isTeacher ? '🥇 强推' : '🥈 推荐',
    reason: '深圳教师年薪25-40万，编制铁饭碗。',
    schools: pickTop(function(u) { return u.name.indexOf('师范') >= 0 && u.match !== 'diwen'; }),
    suitable: true, note: '公费师范生免学费包分配，适合求稳。'
  });
  
  if (score >= 580) {
    majors.push({
      major: '新能源/电气工程', priority: '🥈 推荐',
      reason: '新能源转型核心赛道，年复合增速30-50%。',
      schools: pickTop(function(u) { return u.match !== 'diwen'; }),
      suitable: true, note: '比亚迪扩招迅猛，国企民企双通路。'
    });
  }
  
  return majors;
}

// ====== 时间线 ======
function getTimeline(profile) {
  var now = new Date();
  var y = now.getFullYear();
  var m = now.getMonth() + 1;
  var currentYear = 2026;
  
  function semesterLabel(y, m) {
    if (y == currentYear && m >= 7 && m <= 8) return '高一升高二暑假';
    if (y == currentYear && m >= 9) return '高二上学期';
    if (y == currentYear + 1 && m <= 1) return '高二上学期';
    if (y == currentYear + 1 && m >= 2 && m <= 6) return '高二下学期';
    if (y == currentYear + 1 && m >= 7 && m <= 8) return '高二升高三暑假';
    if (y == currentYear + 1 && m >= 9) return '高三上学期';
    if (y == currentYear + 2 && m <= 6) return '高三下学期（高考冲刺）';
    return '当前';
  }
  
  return [
    { period: semesterLabel(y, m), tasks: ['稳固年级排名，保持优势科目', '补齐短板科目（弱科优先）', '建立错题本和知识框架', '关注升学政策变化'] },
    { period: '高二', tasks: ['数学/英语打基础', '确定选科方向', '关注强基/综评政策'] },
    { period: '高三冲刺', tasks: ['一轮复习、二轮复习、三轮冲刺', '强基计划报名（如适用）', '综合评价报名（如适用）', '高考', '志愿填报+录取'] }
  ];
}

// ====== 未来趋势 ======
function getFutureOutlook(profile) {
  var goal = (profile.interests || '') + (profile.life_direction || '');
  var family = profile.family_background || '';
  var isTech = goal.indexOf('AI') >= 0 || goal.indexOf('计算机') >= 0 || goal.indexOf('编程') >= 0 || goal.indexOf('技术') >= 0 || goal.indexOf('创业') >= 0;
  var isTeacher = goal.indexOf('老师') >= 0 || goal.indexOf('师范') >= 0;
  var isWealthy = family.indexOf('A8') >= 0 || family.indexOf('开公司') >= 0;
  
  var advice = [];
  advice.push('AI工具使用能力是2030年后的生存底线，无论什么专业都必须掌握');
  advice.push('没有一劳永逸的专业，持续学习能力比专业本身更重要');
  advice.push('城市大于学校大于专业：深圳/广州的实习机会碾压内陆城市');
  advice.push('本科打基础、硕士定方向——学历通胀下硕士已是标配');
  advice.push('技术+管理/技术+产品的复合型人才最抗周期波动');
  
  if (isWealthy) advice.unshift('A8-A9家庭优先考虑技术+管理路径，本科STEM+硕士商科');
  else advice.unshift('普通家庭选确定性高的赛道（计算机/电子/电气），第一份工作必须能养活自己');
  
  return {
    top_industries_10y: ['人工智能全产业链（国产AI芯片、大模型、人形机器人）', '新能源与储能（光伏/风电/固态电池/氢能）', '半导体与先进制造（国产替代主线）', '生物医药与生命科技（老龄化+基因技术）', '低空经济（无人机+eVTOL飞行器）'],
    geo_impact: isTech ? '中美科技脱钩=国产替代红利10年。你选技术方向正好踩在国家战略上' : (isTeacher ? '教师行业受地缘影响小，稳定性高。注意深圳教师编制在收紧' : '中美博弈长期化，选专业应优先考虑国家重点扶持产业方向'),
    career_advice_10y: advice,
    risk_warning: isTeacher && (profile.estimated_score || 600) > 640 ? '你这分数段当老师性价比偏低，AI+技术赛道长线收益更高' : '你的选择方向目前风险可控'
  };
}

// ====== 生成完整报告 ======
function generateFullReport(profile) {
  loadRecommendDB();
  var score = profile.estimated_score || 600;
  var scoreMin = profile.estimated_score_min || (score - 15);
  var scoreMax = profile.estimated_score_max || (score + 15);
  
  var cwb = getChongWenBao(profile);
  var qj = getQiangji(profile);
  var zp = getZongping(profile);
  var majors = getMajorRecommendations(profile);
  var timeline = getTimeline(profile);
  var outlook = getFutureOutlook(profile);
  
  // 省排名估算
  var rankMin = 0, rankMax = 0;
  if (score > 670) { rankMin = 100; rankMax = 1500; }
  else if (score > 640) { rankMin = 1500; rankMax = 5000; }
  else if (score > 610) { rankMin = 5000; rankMax = 15000; }
  else if (score > 580) { rankMin = 15000; rankMax = 35000; }
  else { rankMin = 35000; rankMax = 80000; }
  
  // 家庭背景解读
  var fam = profile.family_background || '';
  var family_implication = '';
  if (fam.indexOf('A8') >= 0 || fam.indexOf('开公司') >= 0 || fam.indexOf('高净值') >= 0 || fam.indexOf('富裕') >= 0) {
    family_implication = '家庭条件优越，可选择空间大。建议先拿硬技能打底（计算机/电子），再结合家庭资源发挥。';
  } else if (fam.indexOf('中产') >= 0 || fam.indexOf('做生意') >= 0) {
    family_implication = '中产家庭有一定抗风险能力。建议选确定性强但天花板也高的赛道。';
  } else {
    family_implication = '普通家庭没有试错资本。第一份工作必须能养活自己。建议选确定性最高的专业（计算机/电子/电气），先站稳再求发展。';
  }
  
  // 成绩
  var exam_scores = profile.exam_scores || {};
  var exams = {};
  for (var k in exam_scores) { if (exam_scores[k] > 0) exams[k] = exam_scores[k]; }
  
  // top3
  var top3_unis = [];
  var seen = {};
  var levels = ['chong','wen','bao'];
  for (var li = 0; li < levels.length; li++) {
    var list = cwb[levels[li]] || [];
    for (var i = 0; i < list.length; i++) {
      var name = list[i].name;
      if (name && !seen[name] && top3_unis.length < 3) {
        seen[name] = true;
        top3_unis.push({name: name, level: levels[li], source: '冲稳保', stars: 3 - top3_unis.length});
      }
    }
  }
  
  return {
    user_name: profile.name || '同学',
    user_school: profile.school || '',
    school_tier: score >= 640 ? '高分' : (score >= 580 ? '中高' : '中等'),
    school_size: profile.school_size || 500,
    estimated_province_rank_min: rankMin,
    estimated_province_rank_max: rankMax,
    estimated_score_min: scoreMin,
    estimated_score_max: scoreMax,
    family_background: fam,
    family_implication: family_implication,
    exam_scores: exams,
    exam_ranks: profile.exam_ranks || {},
    interests: profile.interests || '',
    weak_analysis: [],
    segment: { level: scoreToSegment(score), description: segmentDesc(score) },
    chong_wen_bao: cwb,
    qiangji: qj,
    zongping: zp,
    majors: majors,
    timeline: timeline,
    future_outlook: outlook,
    top3_unis: top3_unis
  };
}
