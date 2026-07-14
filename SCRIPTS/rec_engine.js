// ═════════════════════════════════════════════════════════════════
// 雪峰人AI - 前端推荐引擎（离线版）
// 移植自 recommend.py，可在浏览器中独立运行
// 数据来源：knowledge_base.db (软科2026排名)
// ═════════════════════════════════════════════════════════════════

// ====== 嵌入式数据库（12KB）======
var GAOKAO_DB = null;

function loadRecommendDB() {
  if (GAOKAO_DB) return;
  
  // 从嵌入的 <script id="recDB"> 标签中读取数据
  var el = document.getElementById('recDB');
  if (!el) { console.error('推荐数据库未加载'); return; }
  
  try {
    GAOKAO_DB = JSON.parse(el.textContent);
  } catch(e) {
    console.error('数据库解析失败:', e);
  }
}

// ====== 分数段判断 ======
function scoreToSegment(score) {
  if (score >= 680) return 'S段';
  if (score >= 660) return 'A+段';
  if (score >= 640) return 'A段';
  if (score >= 610) return 'B+段';
  if (score >= 580) return 'B段';
  if (score >= 500) return 'C段';
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

// ====== 分数等级标签 ======
function scoreTag(score) {
  if (score >= 660) return '冲刺C9';
  if (score >= 610) return '冲击211';
  if (score >= 550) return '冲击一本';
  return '冲击本科';
}

// ====== 查找匹配高校 ======
function findSchools(subject, score) {
  if (!GAOKAO_DB || !GAOKAO_DB.universities) return [];
  
  var unis = GAOKAO_DB.universities.filter(function(u) { return u.name; });
  var scores = GAOKAO_DB.scores || [];
  var qjUnis = GAOKAO_DB.qj_unis || [];
  var zpUnis = GAOKAO_DB.zp_unis || [];
  
  var result = [];
  for (var i = 0; i < unis.length; i++) {
    var u = unis[i];
    var s = score;
    
    // 找录取分
    var matchedScore = null;
    for (var j = 0; j < scores.length; j++) {
      if (scores[j].name === u.name) {
        matchedScore = scores[j].score;
        break;
      }
    }
    
    // 判断匹配程度
    var diff = matchedScore ? s - matchedScore : 0;
    var match = '';
    if (matchedScore) {
      if (diff >= 5) match = 'chong';
      else if (diff >= -5) match = 'wen';
      else if (diff >= -20) match = 'bao';
      else match = 'diwen';
    } else {
      match = 'wen'; // 无分数数据默认稳妥
    }
    
    // 是否强基
    var hasQJ = qjUnis.indexOf(u.name) >= 0;
    var hasZP = zpUnis.indexOf(u.name) >= 0;
    
    result.push({
      name: u.name,
      level: u.level,
      city: u.city,
      score: matchedScore,
      match: match,
      diff: diff,
      hasQJ: hasQJ,
      hasZP: hasZP
    });
  }
  
  // 排序：按匹配程度+排名
  result.sort(function(a, b) {
    var order = { 'chong': 0, 'wen': 1, 'bao': 2, 'diwen': 3 };
    var oa = order[a.match] || 99;
    var ob = order[b.match] || 99;
    if (oa !== ob) return oa - ob;
    return Math.abs(a.diff) - Math.abs(b.diff);
  });
  
  return result;
}

// ====== 冲稳保分析 ======
function getChongWenBao(profile) {
  var score = profile.estimated_score || 600;
  var all = findSchools('', score);
  
  var chong = all.filter(function(u) { return u.match === 'chong'; }).slice(0, 4);
  var wen = all.filter(function(u) { return u.match === 'wen'; }).slice(0, 4);
  var bao = all.filter(function(u) { return u.match === 'bao'; }).slice(0, 3);
  
  return { chong: chong, wen: wen, bao: bao };
}

// ====== 强基分析 ======
function getQiangji(profile) {
  var score = profile.estimated_score || 600;
  var all = findSchools('', score);
  var qj = all.filter(function(u) { return u.hasQJ && u.match !== 'diwen'; }).slice(0, 5);
  
  if (qj.length === 0) return [];
  return qj.map(function(u) {
    return { school: u.name, type: '强基计划', match: u.match === 'chong' ? '冲刺' : (u.match === 'wen' ? '稳妥' : '保底') };
  });
}

// ====== 综评分析 ======
function getZongping(profile) {
  var score = profile.estimated_score || 600;
  var scoreMin = (profile.estimated_score_min || score - 15);
  var scoreMax = (profile.estimated_score_max || score + 15);
  
  var zpUnis = GAOKAO_DB ? (GAOKAO_DB.zp_unis || []) : [];
  
  var result = [];
  for (var i = 0; i < zpUnis.length; i++) {
    var name = zpUnis[i];
    result.push({ school: name, type: '综合评价' });
  }
  return result.slice(0, 5);
}

// ====== 专业推荐 ======
function getMajorRecommendations(profile) {
  var score = profile.estimated_score || 600;
  var family = profile.family_background || '';
  var goal = profile.interests || '';
  var isWealthy = family.indexOf('A8') >= 0 || family.indexOf('开公司') >= 0 || family.indexOf('高净值') >= 0;
  var isTeacher = goal.indexOf('老师') >= 0 || goal.indexOf('师范') >= 0 || goal.indexOf('教书') >= 0;
  var isTech = goal.indexOf('技术') >= 0 || goal.indexOf('编程') >= 0 || goal.indexOf('AI') >= 0 || goal.indexOf('计算机') >= 0;
  var isStartup = goal.indexOf('创业') >= 0 || goal.indexOf('开公司') >= 0;
  
  var allUnis = findSchools('', score);
  
  function pickTop(major, filterFn) {
    var picks = allUnis.filter(filterFn).slice(0, 3);
    return picks.map(function(u) { return [u.name, u.level]; });
  }
  
  var majors = [];
  
  // CS
  majors.push({
    major: '计算机科学与技术', priority: 'strong',
    reason: '未来十年最抗打的硬通货专业，2026年AI岗薪资涨18%',
    note: '大一大二死磕算法和数学，低端饱和高端缺人',
    schools: pickTop('计算机', function(u) { return u.match !== 'diwen'; })
  });
  
  // AI
  if (score >= 620) {
    majors.push({
      major: '人工智能', priority: score >= 640 ? 'strong' : 'recommend',
      reason: '未来十年最热赛道，核心研发人才供需比1:15',
      note: '想搞AI算法得读到硕博',
      schools: pickTop('AI', function(u) { return u.match !== 'diwen'; })
    });
  }
  
  // 集成电路
  if (score >= 580) {
    majors.push({
      major: '集成电路/电子科学与技术', priority: 'strong',
      reason: '国家战略方向，大基金3440亿投入，人才缺口30万',
      note: '唯一能靠国家战略吃饭的专业',
      schools: pickTop('集成电路', function(u) { return u.match !== 'diwen'; })
    });
  }
  
  // 机器人工程
  if (score >= 580) {
    majors.push({
      major: '机器人工程', priority: 'recommend',
      reason: '制造业升级+老龄化，机器人需求只增不减',
      note: '具身智能时代核心专业',
      schools: pickTop('机器人', function(u) { return u.match !== 'diwen'; })
    });
  }
  
  // 师范
  if (score >= 500) {
    majors.push({
      major: '师范（公费师范生/信息技术方向）', priority: isTeacher ? 'strong' : 'recommend',
      reason: '深圳教师年薪25-40万，编制铁饭碗',
      note: '公费师范生免学费包分配，适合求稳',
      schools: pickTop('师范', function(u) { return u.name.indexOf('师范') >= 0 && u.match !== 'diwen'; })
    });
  }
  
  // 电气工程
  if (score >= 580) {
    majors.push({
      major: '新能源/电气工程', priority: 'recommend',
      reason: '新能源转型核心赛道，年复合增速30-50%',
      note: '比亚迪扩招迅猛，国企民企双通路',
      schools: pickTop('电气', function(u) { return u.match !== 'diwen'; })
    });
  }
  
  return majors;
}

// ====== 时间线 ======
function getTimeline(profile) {
  var now = new Date();
  var y = now.getFullYear();
  var m = now.getMonth() + 1;
  
  // 判断当前学期
  var semester = '';
  if (y === 2026 && m === 7) semester = '高一升高二暑假';
  else if (y === 2026 && m >= 9) semester = '高二上学期';
  else if (y === 2027 && m <= 1) semester = '高二上学期';
  else if (y === 2027 && m >= 2 && m <= 6) semester = '高二下学期';
  else if (y === 2027 && m >= 7 && m <= 8) semester = '高二升高三暑假';
  else if (y === 2027 && m >= 9) semester = '高三上学期';
  else if (y === 2028 && m <= 6) semester = '高三下学期';
  else semester = '当前学期';
  
  return [
    { period: semester, events: ['稳固年级排名，保持优势科目', '补齐短板科目（弱科优先）', '建立错题本和知识框架'] },
    { period: '高二', events: ['数学/英语打基础', '确定选科方向', '关注强基/综评政策'] },
    { period: '高三冲刺', events: ['一轮复习、二轮复习、三轮冲刺', '强基计划报名（如适用）', '综合评价报名', '高考', '志愿填报+录取'] }
  ];
}

// ====== 未来趋势 ======
function getFutureOutlook(profile) {
  var goal = (profile.interests || '') + (profile.life_direction || '');
  var family = profile.family_background || '';
  var isTech = goal.indexOf('AI') >= 0 || goal.indexOf('计算机') >= 0 || goal.indexOf('编程') >= 0 || goal.indexOf('技术') >= 0 || goal.indexOf('创业') >= 0;
  var isTeacher = goal.indexOf('老师') >= 0 || goal.indexOf('师范') >= 0;
  var isWealthy = family.indexOf('A8') >= 0 || family.indexOf('开公司') >= 0 || family.indexOf('高净值') >= 0;
  
  var advice = [];
  advice.push('AI工具使用能力是2030年后的生存底线，无论什么专业都必须掌握');
  advice.push('没有一劳永逸的专业，持续学习能力比专业本身更重要');
  if (isWealthy) advice.unshift('A8-A9家庭：优先考虑技术+管理路径，本科STEM+硕士商科');
  else advice.unshift('普通家庭：选确定性高的赛道（计算机/电子/电气），第一份工作必须能养活自己');
  
  return {
    topIndustries: ['人工智能全产业链', '新能源与储能', '半导体与先进制造', '生物医药', '低空经济'],
    geoAdvice: isTech ? '中美科技脱钩=国产替代红利10年，选技术方向正好踩在国家战略上' : '中美博弈长期化，选专业优先考虑国家重点扶持产业方向',
    advice: advice,
    riskWarning: isTeacher && profile.estimated_score > 640 ? '你这分数段当老师性价比偏低' : '你的选择方向目前风险可控'
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
  var rankMin = profile.estimated_province_rank_min || 0;
  var rankMax = profile.estimated_province_rank_max || 0;
  if (score > 670) { rankMin = 100; rankMax = 1500; }
  else if (score > 640) { rankMin = 1500; rankMax = 5000; }
  else if (score > 610) { rankMin = 5000; rankMax = 15000; }
  else if (score > 580) { rankMin = 15000; rankMax = 35000; }
  else { rankMin = 35000; rankMax = 80000; }
  
  return {
    user_name: profile.name || '同学',
    user_school: profile.school || '',
    estimated_score_min: scoreMin,
    estimated_score_max: scoreMax,
    estimated_province_rank_min: rankMin,
    estimated_province_rank_max: rankMax,
    family_background: profile.family_background || '',
    interests: profile.interests || '',
    segment: { level: scoreToSegment(score), description: segmentDesc(score) },
    chong_wen_bao: cwb,
    qiangji: qj,
    zongping: zp,
    majors: majors,
    timeline: timeline,
    future_outlook: outlook
  };
}
