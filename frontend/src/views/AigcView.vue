<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示内容模板（无后端时回退，文本与原始实现一致） ----------
const DEMO = {
  planDemo(kp, goal) {
    const g = goal || '理解' + kp + '的核心概念与典型应用'
    return '【教案】' + kp + '\n' +
      '一、教学目标\n' +
      '  1. 知识与技能：' + g + '；\n' +
      '  2. 过程与方法：通过例题引导、代码演示与上机练习，掌握解题思路；\n' +
      '  3. 情感态度：培养算法思维与解决实际问题的兴趣。\n\n' +
      '二、教学重难点\n' +
      '  · 重点：核心概念的理解与经典模板的运用；\n' +
      '  · 难点：状态/递推关系的抽象与边界条件处理。\n\n' +
      '三、教学过程\n' +
      '  1. 导入（5 分钟）：由一个贴近竞赛的实例引入；\n' +
      '  2. 讲解（30 分钟）：概念推导 + 例题精讲；\n' +
      '  3. 练习（20 分钟）：2-3 道上机题分层训练；\n' +
      '  4. 小结（5 分钟）：梳理知识脉络与易错点。\n\n' +
      '四、课后作业\n' +
      '  · 基础题 2 道、提高题 1 道，附参考答案与解析。\n\n' +
      '（演示内容，接入大模型后将返回更完整的教案）'
  },

  quizDemo(kp, count, difficulty) {
    const lines = ['【智能题库】知识点：' + kp + '（难度 ' + difficulty + '/5）\n']
    const level = difficulty <= 2 ? '基础' : (difficulty <= 4 ? '进阶' : '困难')
    for (let i = 1; i <= count; i++) {
      lines.push(
        '第 ' + i + ' 题（' + level + '）\n' +
        '  题干：请设计一个与「' + kp + '」相关的' + level + '问题，并描述其输入输出格式。\n' +
        '  参考答案：（略，示例参考答案）\n' +
        '  解析：本题考察' + kp + '的基本思想与模板运用，注意边界条件与复杂度。\n'
      )
    }
    lines.push('（演示内容，接入大模型后将返回真实题目）')
    return lines.join('\n')
  },

  summarizeDemo(text) {
    const snippet = text.length > 40 ? text.slice(0, 40) + '…' : text
    return '【内容摘要】\n' +
      '  原文要点：' + snippet + '\n\n' +
      '  摘要：本文围绕所提供材料展开，主要阐述了相关概念、方法与应用场景，' +
      '强调理解核心思想并通过实例加以巩固。全文结构清晰、重点突出，适合作为' +
      '教学素材或自学材料使用。\n\n' +
      '  · 关键词：核心概念、方法、实例、应用\n' +
      '  （演示内容，接入大模型后将返回精准摘要）'
  },

  outlineDemo(course, goal) {
    const g = goal || '掌握该课程核心知识与实践能力'
    return '【课程大纲】' + course + '\n' +
      '一、课程简介\n' +
      '  本课程系统讲授' + course + '的核心理论、经典方法与典型应用，注重算法思维与工程实践能力的培养。\n\n' +
      '二、教学目标\n' +
      '  ' + g + '。\n\n' +
      '三、章节安排\n' +
      '  第 1 章 绪论与基础（4 学时）——基本概念、复杂度分析；\n' +
      '  第 2 章 核心专题（12 学时）——重点方法与模板；\n' +
      '  第 3 章 进阶与综合（8 学时）——综合应用与竞赛真题；\n' +
      '  第 4 章 实践项目（8 学时）——小组项目开发。\n\n' +
      '四、实践环节\n' +
      '  上机练习 + 课程项目 + 竞赛训练。\n\n' +
      '五、考核方式\n' +
      '  平时作业 20% + 实验 20% + 项目 20% + 期末 40%。\n\n' +
      '（演示内容，接入大模型后将返回更贴合课程的大纲）'
  },

  pptDemo(topic, objective) {
    return '【PPT 大纲】' + topic + '\n\n' +
      '第 1 页  封面：' + topic + '（' + (objective || '教学目标') + '）\n' +
      '第 2 页  导入：一个贴近竞赛/工程的实际问题\n' +
      '第 3 页  学习目标：明确本节要达成的能力\n' +
      '第 4 页  概念讲解：核心定义与直观理解\n' +
      '第 5 页  算法思想：流程 / 递推关系图解\n' +
      '第 6 页  例题演示 1：逐步推导\n' +
      '第 7 页  例题演示 2：边界与易错点\n' +
      '第 8 页  互动练习：课堂小测 1-2 题\n' +
      '第 9 页  小结：知识脉络与模板\n' +
      '第 10 页 课后作业与下节预告\n\n' +
      '（演示内容，接入大模型后将返回逐页详细要点）'
  },

  examDemo(kp, count, diff) {
    const lines = ['【智能组卷】考核知识点：' + kp + '（共 ' + count + ' 题，难度 ' + diff + '/5）\n\n一、试卷说明\n  满分 100 分，考试时间 120 分钟。\n\n二、试题\n']
    for (let i = 1; i <= count; i++) {
      const type = i % 4 === 0 ? '编程题' : (i % 3 === 0 ? '简答题' : (i % 2 === 0 ? '填空题' : '选择题'))
      lines.push('第 ' + i + ' 题（' + type + '，' + Math.round(100 / count) + ' 分）\n  围绕「' + kp + '」设问，考察基本概念与典型应用。\n')
    }
    lines.push('三、参考答案与评分标准（略，示例）\n四、难度分布：基础 / 进阶 / 综合 约为 4 : 4 : 2\n\n（演示内容，接入大模型后将返回真实试卷）')
    return lines.join('\n')
  },

  reviewDemo(question) {
    const snippet = question.length > 30 ? question.slice(0, 30) + '…' : question
    return '【题目质量评估】\n\n  题目：' + snippet + '\n\n' +
      '  1. 科学性：题意明确、结论正确，无歧义。\n' +
      '  2. 难度与区分度：难度适中，能较好区分不同水平学生。\n' +
      '  3. 表述清晰度：语言通顺、输入输出约定清楚。\n' +
      '  4. 答案正确性：参考答案逻辑自洽，边界考虑完整。\n' +
      '  5. 改进建议：可补充样例说明与复杂度要求。\n\n' +
      '  总体评分：8 / 10\n\n' +
      '（演示内容，接入大模型后将返回针对性评估）'
  },

  projectDemo(topic, diff, goal) {
    return '【实践项目方案】' + topic + '\n\n' +
      '一、项目背景与目标\n' +
      '  ' + (goal || '通过动手实践巩固核心知识并完成一个小型系统') + '（难度 ' + diff + '/5）。\n\n' +
      '二、功能需求\n' +
      '  · 核心功能模块 2-3 个；· 数据输入 / 输出与可视化。\n\n' +
      '三、技术路线\n' +
      '  · 关键数据结构 / 算法选型；· 开发语言与框架建议。\n\n' +
      '四、分阶段任务拆解\n' +
      '  阶段 1（需求与设计）→ 阶段 2（核心实现）→ 阶段 3（测试与优化）→ 阶段 4（答辩与报告）。\n\n' +
      '五、验收标准与评分细则\n' +
      '  功能完整 40% + 代码质量 20% + 创新性 20% + 答辩 20%。\n\n' +
      '（演示内容，接入大模型后将返回定制化方案）'
  },

  reportDemo(course, data) {
    return '【教学报告】' + course + '\n\n' +
      '一、教学基本情况\n' +
      '  本课程按大纲完成既定教学任务' + (data ? '，并结合所提供数据进行了分析。' : '。') + '\n\n' +
      '二、教学成效\n' +
      '  多数学生掌握核心知识点，作业完成率与到课率保持稳定。\n\n' +
      '三、存在问题与原因分析\n' +
      '  部分学生基础薄弱、练习投入不足，导致成绩分化明显。\n\n' +
      '四、改进措施与下学期计划\n' +
      '  加强分层教学、增加过程性评价与学情预警干预。\n\n' +
      '（演示内容，接入大模型后将结合真实数据生成总结）'
  }
}

// ---------- 页面状态 ----------
const activeTool = ref('plan')
const output = ref('请在左侧填写内容并点击生成。')
const loading = ref(false)

// 教案生成
const planKp = ref('')
const planGoal = ref('')
// 课程大纲
const outlineCourse = ref('')
const outlineGoal = ref('')
// PPT 生成
const pptTopic = ref('')
const pptObjective = ref('')
const pptOutline = ref('')
// 智能题库
const quizKp = ref('')
const quizCount = ref(5)
const quizDifficulty = ref(3)
// 智能组卷
const examKp = ref('')
const examCount = ref(10)
const examDifficulty = ref(3)
const examTypes = ref('')
// 题目评估
const reviewQuestion = ref('')
// 项目助手
const projectTopic = ref('')
const projectDifficulty = ref(3)
const projectGoal = ref('')
// 教学报告
const reportCourse = ref('')
const reportData = ref('')
// 资源摘要
const sumText = ref('')

// ---------- 通用生成 ----------
function setLoading() {
  output.value = '正在生成，请稍候…'
  loading.value = true
}

async function run(apiCall, demoText) {
  setLoading()
  const data = await api.request(apiCall, { content: demoText })
  output.value = (data && data.content) || '（无内容）'
  loading.value = false
}

// ---------- 提交事件 ----------
function submitPlan() {
  const kp = planKp.value.trim()
  if (!kp) { ElMessage.error('请填写知识点'); return }
  const goal = planGoal.value.trim()
  run(api.generatePlan({ knowledge_point: kp, goal: goal || undefined }), DEMO.planDemo(kp, goal))
}

function submitOutline() {
  const course = outlineCourse.value.trim()
  if (!course) { ElMessage.error('请填写课程名称'); return }
  const goal = outlineGoal.value.trim()
  run(api.generateOutline({ course_name: course, goal: goal || undefined }), DEMO.outlineDemo(course, goal))
}

function submitPpt() {
  const topic = pptTopic.value.trim()
  if (!topic) { ElMessage.error('请填写授课主题'); return }
  const objective = pptObjective.value.trim()
  const outline = pptOutline.value.trim()
  run(api.generatePpt({ topic: topic, objective: objective || undefined, outline: outline || undefined }), DEMO.pptDemo(topic, objective))
}

function submitQuiz() {
  const kp = quizKp.value.trim()
  if (!kp) { ElMessage.error('请填写知识点'); return }
  const count = Math.min(20, Math.max(1, Number(quizCount.value) || 5))
  const difficulty = Math.min(5, Math.max(1, Number(quizDifficulty.value) || 3))
  run(api.generateQuiz({ knowledge_point: kp, count: count, difficulty: difficulty }), DEMO.quizDemo(kp, count, difficulty))
}

function submitExam() {
  const kp = examKp.value.trim()
  if (!kp) { ElMessage.error('请填写考核知识点'); return }
  const count = Math.min(30, Math.max(1, Number(examCount.value) || 10))
  const difficulty = Math.min(5, Math.max(1, Number(examDifficulty.value) || 3))
  const types = examTypes.value.trim()
  run(api.generateExamPaper({ knowledge_point: kp, count: count, difficulty: difficulty, question_types: types || undefined }), DEMO.examDemo(kp, count, difficulty))
}

function submitReview() {
  const text = reviewQuestion.value.trim()
  if (text.length < 10) { ElMessage.error('请粘贴至少 10 字的题目'); return }
  run(api.reviewQuestion(text), DEMO.reviewDemo(text))
}

function submitProject() {
  const topic = projectTopic.value.trim()
  if (!topic) { ElMessage.error('请填写项目主题'); return }
  const difficulty = Math.min(5, Math.max(1, Number(projectDifficulty.value) || 3))
  const goal = projectGoal.value.trim()
  run(api.designProject({ topic: topic, difficulty: difficulty, goal: goal || undefined }), DEMO.projectDemo(topic, difficulty, goal))
}

function submitReport() {
  const course = reportCourse.value.trim()
  if (!course) { ElMessage.error('请填写课程名称'); return }
  const data = reportData.value.trim()
  run(api.generateReport({ course_name: course, semester_data: data || undefined }), DEMO.reportDemo(course, data))
}

function submitSummarize() {
  const text = sumText.value.trim()
  if (text.length < 10) { ElMessage.error('请粘贴至少 10 字的原文'); return }
  run(api.summarizeResource(text), DEMO.summarizeDemo(text))
}

// ---------- 复制结果 ----------
function copyResult() {
  const text = output.value
  if (!text || loading.value) { ElMessage.error('暂无可复制内容'); return }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success('已复制')
    }).catch(() => {
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
  ElMessage.success('已复制')
}
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>AI 教研与备课中心</h2>
      <p>基于大模型统一封装，覆盖备课、出题、项目设计与教学总结全流程。</p>
    </div>

    <!-- 工具切换 -->
    <el-tabs v-model="activeTool" class="tool-tabs">
      <!-- 教案生成 -->
      <el-tab-pane label="教案生成" name="plan">
        <el-form label-position="top">
          <el-form-item label="知识点">
            <el-input v-model="planKp" placeholder="如：动态规划 - 01 背包" />
          </el-form-item>
          <el-form-item label="教学目标（选填）">
            <el-input v-model="planGoal" type="textarea" :rows="3" placeholder="如：让学生掌握状态转移方程的设计思路" />
          </el-form-item>
          <el-button type="primary" @click="submitPlan">生成教案</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 课程大纲 -->
      <el-tab-pane label="课程大纲" name="outline">
        <el-form label-position="top">
          <el-form-item label="课程名称 / 主题">
            <el-input v-model="outlineCourse" placeholder="如：算法设计与分析" />
          </el-form-item>
          <el-form-item label="教学目标（选填）">
            <el-input v-model="outlineGoal" type="textarea" :rows="3" placeholder="如：掌握经典算法设计范式并能用于竞赛解题" />
          </el-form-item>
          <el-button type="primary" @click="submitOutline">生成课程大纲</el-button>
        </el-form>
      </el-tab-pane>

      <!-- PPT 生成 -->
      <el-tab-pane label="PPT 生成" name="ppt">
        <el-form label-position="top">
          <el-form-item label="授课主题">
            <el-input v-model="pptTopic" placeholder="如：动态规划 - 最长公共子序列" />
          </el-form-item>
          <el-form-item label="教学目标（选填）">
            <el-input v-model="pptObjective" type="textarea" :rows="3" placeholder="如：理解状态定义与转移方程的推导" />
          </el-form-item>
          <el-form-item label="参考大纲 / 内容（选填）">
            <el-input v-model="pptOutline" type="textarea" :rows="3" placeholder="粘贴已有教案或大纲要点，帮助 PPT 更贴合你的授课安排" />
          </el-form-item>
          <el-button type="primary" @click="submitPpt">生成 PPT 大纲</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 智能题库 -->
      <el-tab-pane label="智能题库" name="quiz">
        <el-form label-position="top">
          <el-form-item label="知识点">
            <el-input v-model="quizKp" placeholder="如：图的最短路径" />
          </el-form-item>
          <div class="quiz-row">
            <el-form-item label="题目数量">
              <el-input v-model="quizCount" type="number" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="难度（1-5）">
              <el-input v-model="quizDifficulty" type="number" :min="1" :max="5" />
            </el-form-item>
          </div>
          <el-button type="primary" @click="submitQuiz">生成题库</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 智能组卷 -->
      <el-tab-pane label="智能组卷" name="exam">
        <el-form label-position="top">
          <el-form-item label="考核知识点">
            <el-input v-model="examKp" placeholder="如：图论与搜索" />
          </el-form-item>
          <div class="quiz-row">
            <el-form-item label="题量">
              <el-input v-model="examCount" type="number" :min="1" :max="30" />
            </el-form-item>
            <el-form-item label="难度（1-5）">
              <el-input v-model="examDifficulty" type="number" :min="1" :max="5" />
            </el-form-item>
          </div>
          <el-form-item label="题型分布（选填）">
            <el-input v-model="examTypes" placeholder="如：选择题、填空题、简答题、编程题" />
          </el-form-item>
          <el-button type="primary" @click="submitExam">智能组卷</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 题目质量评估 -->
      <el-tab-pane label="题目评估" name="review">
        <el-form label-position="top">
          <el-form-item label="待评估题目">
            <el-input v-model="reviewQuestion" type="textarea" :rows="6" placeholder="粘贴需要评估的题目（题干 + 参考答案 + 解析，至少 10 字）" />
          </el-form-item>
          <el-button type="primary" @click="submitReview">评估题目质量</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 项目助手 -->
      <el-tab-pane label="项目助手" name="project">
        <el-form label-position="top">
          <el-form-item label="项目主题">
            <el-input v-model="projectTopic" placeholder="如：校园导航系统（图的最短路应用）" />
          </el-form-item>
          <div class="quiz-row">
            <el-form-item label="难度（1-5）">
              <el-input v-model="projectDifficulty" type="number" :min="1" :max="5" />
            </el-form-item>
            <el-form-item label="项目目标（选填）">
              <el-input v-model="projectGoal" placeholder="如：掌握图算法并完成系统集成" />
            </el-form-item>
          </div>
          <el-button type="primary" @click="submitProject">生成项目方案</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 教学报告 -->
      <el-tab-pane label="教学报告" name="report">
        <el-form label-position="top">
          <el-form-item label="课程名称">
            <el-input v-model="reportCourse" placeholder="如：数据结构" />
          </el-form-item>
          <el-form-item label="学期数据（选填）">
            <el-input v-model="reportData" type="textarea" :rows="6" placeholder="粘贴成绩分布、作业完成率、到课率等数据，报告将结合数据给出分析" />
          </el-form-item>
          <el-button type="primary" @click="submitReport">生成教学报告</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 资源摘要 -->
      <el-tab-pane label="资源摘要" name="summarize">
        <el-form label-position="top">
          <el-form-item label="资源原文 / 内容">
            <el-input v-model="sumText" type="textarea" :rows="6" placeholder="粘贴需要摘要的文本内容（至少 10 字）" />
          </el-form-item>
          <el-button type="primary" @click="submitSummarize">生成摘要</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 输出区 -->
    <section class="panel output-panel">
      <div class="panel-head">
        <h3>生成结果</h3>
        <el-button size="small" @click="copyResult">复制</el-button>
      </div>
      <div class="panel-body">
        <pre class="output" :class="{ loading: loading }">{{ output }}</pre>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* 工具切换标签 */
.tool-tabs {
  margin-bottom: 20px;
}
.tool-tabs :deep(.el-tabs__item.is-active) {
  color: var(--brand-primary);
}
.tool-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--brand-primary);
}

/* 并排数字输入行 */
.quiz-row {
  display: flex;
  gap: 16px;
}
.quiz-row :deep(.el-form-item) {
  flex: 1;
}

/* 输出区 */
.output-panel {
  margin-bottom: 0;
}

.output {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: "Microsoft Yahei", monospace;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  min-height: 120px;
  margin: 0;
}

.output.loading {
  color: #999;
}
</style>
