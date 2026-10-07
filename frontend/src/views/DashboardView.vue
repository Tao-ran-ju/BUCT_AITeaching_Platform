<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'
import { useECharts } from '../composables/useECharts.js'

// ---------- 演示数据 ----------
const DEMO = reactive({
  metrics: [
    { key: 'total_users', label: '教师与学生总数', value: 128, unit: '', trend: null },
    { key: 'total_resources', label: '教学资源数', value: 46, unit: '', trend: null },
    { key: 'pass_rate', label: '作业通过率', value: 82.5, unit: '%', trend: null },
    { key: 'avg_score', label: '平均分', value: 78.3, unit: '分', trend: null }
  ],
  courses: [
    { id: 1, name: '算法设计与分析' },
    { id: 2, name: '数据结构' }
  ],
  heatmap: [
    { knowledge_point: '线性表', value: 0.91 },
    { knowledge_point: '分治法', value: 0.86 },
    { knowledge_point: '树与二叉树', value: 0.80 },
    { knowledge_point: '动态规划', value: 0.72 },
    { knowledge_point: '图论', value: 0.65 },
    { knowledge_point: '贪心算法', value: 0.58 },
    { knowledge_point: '排序算法', value: 0.49 }
  ],
  warnings: [
    { id: 1, student_id: 101, student_name: '张伟', course_id: 1, course_name: '算法设计与分析', risk_level: 'high', reason: '作业正确率低于 30%；近期日均登录时长 120 秒，学习不积极', suggestion: '', is_resolved: false },
    { id: 2, student_id: 102, student_name: '李娜', course_id: 1, course_name: '算法设计与分析', risk_level: 'medium', reason: '近期日均资源访问 1 次，学习不积极', suggestion: '', is_resolved: false },
    { id: 3, student_id: 103, student_name: '王强', course_id: 2, course_name: '数据结构', risk_level: 'medium', reason: '作业提交延迟 4 天', suggestion: '', is_resolved: false },
    { id: 4, student_id: 201, student_name: '赵敏', course_id: 2, course_name: '数据结构', risk_level: 'low', reason: '近期日均登录时长 540 秒，学习不积极', suggestion: '', is_resolved: false }
  ],
  taskProgress: {
    student_cols: [
      { student_id: 101, name: '张伟' },
      { student_id: 102, name: '李娜' },
      { student_id: 103, name: '王强' },
      { student_id: 201, name: '赵敏' },
      { student_id: 202, name: '刘洋' }
    ],
    tasks: [
      { task_id: 1, title: '完成「动态规划」知识点学习', course_name: '算法设计与分析', deadline: '2024-09-28 23:59', total: 3, completed: 1, rate: 0.33, cells: { 101: 'completed', 102: 'pending', 103: 'pending' } },
      { task_id: 2, title: '完成「二叉树遍历」实验', course_name: '数据结构', deadline: '2024-09-25 23:59', total: 2, completed: 2, rate: 1, cells: { 201: 'completed', 202: 'completed' } }
    ]
  },
  scoreDistribution: {
    buckets: [
      { range: '0-59', label: '不及格', count: 3 },
      { range: '60-69', label: '及格', count: 8 },
      { range: '70-79', label: '中等', count: 15 },
      { range: '80-89', label: '良好', count: 10 },
      { range: '90-100', label: '优秀', count: 4 }
    ],
    total: 40
  },
  effectCompare: [
    { course_id: 1, course_name: '算法设计与分析', avg_score: 82.4, pass_rate: 0.91, submission_count: 42 },
    { course_id: 2, course_name: '数据结构', avg_score: 74.8, pass_rate: 0.82, submission_count: 38 },
    { course_id: 3, course_name: '程序设计基础', avg_score: 68.5, pass_rate: 0.71, submission_count: 55 }
  ]
})

// 品牌紫单色顺序渐变（浅 → 深）
const RAMP = [
  { t: 0.0, c: '#eadcfb' },
  { t: 0.25, c: '#c9a9ef' },
  { t: 0.5, c: '#a478e0' },
  { t: 0.75, c: '#7d3ec4' },
  { t: 1.0, c: '#5a1a9b' }
]

const RISK_LABEL = { high: '高风险', medium: '中风险', low: '低风险' }
const RISK_CLASS = { high: 'high', medium: 'medium', low: 'low' }
const RISK_ICON = { high: '⛔', medium: '⚠', low: 'ℹ' }
const RISK_ORDER = { high: 0, medium: 1, low: 2 }
let demoId = 1000

function mix(c1, c2, t) {
  const ch = (s, o) => parseInt(s.substr(o, 2), 16)
  const r = Math.round(ch(c1, 1) + (ch(c2, 1) - ch(c1, 1)) * t)
  const g = Math.round(ch(c1, 3) + (ch(c2, 3) - ch(c1, 3)) * t)
  const b = Math.round(ch(c1, 5) + (ch(c2, 5) - ch(c1, 5)) * t)
  return 'rgb(' + r + ',' + g + ',' + b + ')'
}

function rampColor(v) {
  v = Math.max(0, Math.min(1, v))
  for (let i = 0; i < RAMP.length - 1; i++) {
    const a = RAMP[i]
    const b = RAMP[i + 1]
    if (v >= a.t && v <= b.t) return mix(a.c, b.c, (v - a.t) / (b.t - a.t))
  }
  return RAMP[RAMP.length - 1].c
}

function fmtNumber(v) {
  if (typeof v === 'number' && !Number.isInteger(v)) return v.toFixed(1)
  return String(v)
}

function nowStr() {
  const d = new Date()
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

function fmtTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').slice(0, 16)
}

function riskRank(r) {
  return Object.prototype.hasOwnProperty.call(RISK_ORDER, r) ? RISK_ORDER[r] : 2
}

// ---------- 响应式状态 ----------
const metrics = ref([])
const heatmapCells = ref([])
const taskProgress = reactive({ student_cols: [], tasks: [] })
const scoreBuckets = ref([])
const effectItems = ref([])
const warnings = ref([])
const warnCount = ref('')
const courses = ref([])
const courseFilter = ref('')
const scanning = ref(false)

// ---------- 图表 ----------
const heatmapRef = ref(null)
const scoreRef = ref(null)
const effectRef = ref(null)
const { setOption: setHeatmap } = useECharts(heatmapRef)
const { setOption: setScore } = useECharts(scoreRef)
const { setOption: setEffect } = useECharts(effectRef)

// ---------- 指标卡 ----------
async function loadMetrics() {
  const data = await api.request(api.dashboardOverview(), { metrics: DEMO.metrics, heatmap: [] })
  metrics.value = (data && data.metrics) || DEMO.metrics
}

// ---------- 能力矩阵（ECharts 横向条形） ----------
async function loadHeatmap(courseId) {
  const data = await api.request(api.dashboardHeatmap(courseId), DEMO.heatmap)
  const cells = Array.isArray(data) ? data : (data && data.items) || []
  heatmapCells.value = cells
  const sorted = cells.slice().sort((a, b) => (b.value || 0) - (a.value || 0))
  const names = sorted.map((c) => c.knowledge_point).reverse()
  const values = sorted.map((c) => Math.round((c.value || 0) * 100)).reverse()
  setHeatmap({
    grid: { left: 130, right: 56, top: 10, bottom: 10 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%', color: '#999' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 13, color: '#444' }, axisLine: { show: false }, axisTick: { show: false } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${p[0].name}：${p[0].value}%` },
    series: [{
      type: 'bar',
      data: values.map((v) => ({ value: v, itemStyle: { color: rampColor(v / 100), borderRadius: [0, 4, 4, 0] } })),
      barWidth: 16,
      label: { show: true, position: 'right', formatter: '{c}%', color: '#555' }
    }]
  })
}

// ---------- 任务进度热力图（DOM 网格） ----------
async function loadTaskProgress() {
  const data = await api.request(api.taskProgress(), DEMO.taskProgress)
  taskProgress.student_cols = (data && data.student_cols) || []
  taskProgress.tasks = (data && data.tasks) || []
}

function cellClass(status, deadline) {
  if (status === 'completed') return 'completed'
  if (deadline && fmtTime(deadline) < nowStr()) return 'overdue'
  return 'pending'
}

function cellLabel(status, cls) {
  if (status === 'completed') return '已完成'
  if (cls === 'overdue') return '已截止未完成'
  return '未完成'
}

// ---------- 成绩分布（ECharts 柱状） ----------
async function loadScoreDistribution() {
  const data = await api.request(api.scoreDistribution(), DEMO.scoreDistribution)
  const buckets = (data && data.buckets) || []
  scoreBuckets.value = buckets
  const max = Math.max.apply(null, buckets.map((b) => b.count || 0)) || 1
  setScore({
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: buckets.map((b) => b.label), axisLabel: { fontSize: 12, color: '#666' }, axisLine: { lineStyle: { color: '#d0d0d0' } } },
    yAxis: { type: 'value', axisLabel: { color: '#999' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${buckets[p[0].dataIndex].range}（${p[0].name}）：${p[0].value} 人` },
    series: [{
      type: 'bar',
      data: buckets.map((b) => ({ value: b.count, itemStyle: { color: rampColor((b.count || 0) / max), borderRadius: [4, 4, 0, 0] } })),
      barWidth: 36,
      label: { show: true, position: 'top', color: '#555' }
    }]
  })
}

// ---------- 教学效果对比（ECharts 横向条形） ----------
async function loadEffectCompare() {
  const data = await api.request(api.effectCompare(), DEMO.effectCompare)
  const items = Array.isArray(data) ? data : []
  effectItems.value = items
  setEffect({
    grid: { left: 130, right: 96, top: 10, bottom: 10 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}', color: '#999' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    yAxis: { type: 'category', data: items.map((i) => i.course_name).reverse(), axisLabel: { fontSize: 13, color: '#444' }, axisLine: { show: false }, axisTick: { show: false } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (p) => {
        const item = items[items.length - 1 - p[0].dataIndex]
        return `${item.course_name}<br/>平均分 ${item.avg_score} 分<br/>通过率 ${Math.round(item.pass_rate * 100)}%<br/>提交 ${item.submission_count} 份`
      }
    },
    series: [{
      type: 'bar',
      data: items.map((i) => ({ value: i.avg_score, itemStyle: { color: rampColor((i.avg_score || 0) / 100), borderRadius: [0, 4, 4, 0] } })).reverse(),
      barWidth: 16,
      label: { show: true, position: 'right', formatter: '{c} 分', color: '#555' }
    }]
  })
}

// ---------- 课程筛选 ----------
async function loadCourses() {
  const data = await api.request(api.listCourses({ page: 1, page_size: 100 }), { items: DEMO.courses, total: DEMO.courses.length })
  courses.value = (data && data.items) || []
}

// ---------- 学情预警 ----------
async function loadWarnings() {
  const data = await api.request(api.listWarnings({ page: 1, page_size: 100 }), { items: DEMO.warnings, total: DEMO.warnings.length })
  const items = (data && data.items) || []
  const active = items.filter((w) => !w.is_resolved)
  active.sort((a, b) => riskRank(a.risk_level) - riskRank(b.risk_level))
  warnings.value = active.slice(0, 8)
  warnCount.value = warnings.value.length ? `未处理 ${warnings.value.length} 条` : '暂无待关注学生'
}

function resolveWarning(id) {
  api.request(api.resolveWarning(id)).then(() => {
    ElMessage.success('已标记处理')
    loadWarnings()
  }).catch(() => {
    DEMO.warnings.forEach((w) => { if (w.id === id) w.is_resolved = true })
    ElMessage.success('演示模式：已本地标记处理')
    loadWarnings()
  })
}

async function scan() {
  scanning.value = true
  try {
    const res = await api.request(api.scanWarnings())
    const n = (res && res.generated != null) ? res.generated : 0
    ElMessage.success('扫描完成，生成 ' + n + ' 条新预警')
  } catch (e) {
    DEMO.warnings.unshift({
      id: ++demoId, student_id: 301, student_name: '陈晨',
      course_id: 1, course_name: '算法设计与分析',
      risk_level: 'medium', reason: '近期日均登录时长 300 秒，学习不积极',
      suggestion: '', is_resolved: false
    })
    ElMessage.success('演示模式：扫描完成')
  }
  scanning.value = false
  loadWarnings()
}

function onCourseFilterChange() {
  loadHeatmap(courseFilter.value ? Number(courseFilter.value) : null)
}

onMounted(() => {
  loadMetrics()
  loadHeatmap(null)
  loadCourses()
  loadTaskProgress()
  loadScoreDistribution()
  loadEffectCompare()
  loadWarnings()
})
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>数据驾驶舱</h2>
      <p>教学核心指标与能力矩阵热力图，帮助教师掌握整体学情。</p>
    </div>

    <div class="dash-toolbar">
      <el-select v-model="courseFilter" placeholder="全部课程" style="width: 220px" @change="onCourseFilterChange">
        <el-option label="全部课程" value="" />
        <el-option v-for="c in courses" :key="c.id" :value="String(c.id)" :label="c.name" />
      </el-select>
      <span class="muted">能力矩阵 · 按课程</span>
    </div>

    <div class="metric-grid">
      <div v-for="m in metrics" :key="m.key" class="metric-card">
        <div class="metric-label">{{ m.label }}</div>
        <div class="metric-value">{{ fmtNumber(m.value) }}<span class="metric-unit">{{ m.unit }}</span></div>
        <div v-if="m.trend != null && m.trend !== 0" class="metric-trend" :class="m.trend > 0 ? 'up' : 'down'">
          {{ m.trend > 0 ? '▲' : '▼' }} {{ Math.abs(m.trend) }}%
        </div>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3>能力矩阵</h3>
        <span class="panel-sub">知识点平均得分（0–100%）</span>
      </div>
      <div class="panel-body">
        <div v-if="!heatmapCells.length" class="empty-tip">暂无能力数据</div>
        <div v-else ref="heatmapRef" class="chart-box"></div>
        <div class="heat-legend">
          <span>0%</span>
          <div class="heat-legend-bar"></div>
          <span>100%</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h3>任务进度热力图</h3>
        <span class="panel-sub">学生 × 任务 完成情况</span>
      </div>
      <div class="panel-body">
        <div v-if="!taskProgress.tasks.length" class="empty-tip">暂无学习任务</div>
        <div v-else class="task-heat">
          <div class="task-heat-row task-heat-head">
            <div class="th-name">任务</div>
            <div v-for="s in taskProgress.student_cols" :key="s.student_id" class="th-cell">{{ s.name }}</div>
            <div class="th-rate">进度</div>
          </div>
          <div v-for="t in taskProgress.tasks" :key="t.task_id" class="task-heat-row">
            <div class="th-name" :title="t.title">{{ t.title }}</div>
            <div v-for="s in taskProgress.student_cols" :key="s.student_id" class="th-cell">
              <i
                class="cell"
                :class="cellClass((t.cells || {})[String(s.student_id)] || 'pending', t.deadline)"
                :title="s.name + ' · ' + cellLabel((t.cells || {})[String(s.student_id)] || 'pending', cellClass((t.cells || {})[String(s.student_id)] || 'pending', t.deadline))"
              ></i>
            </div>
            <div class="th-rate">{{ t.completed || 0 }}/{{ t.total || 0 }}</div>
          </div>
        </div>
        <div class="task-heat-legend">
          <span class="tl-item"><i class="tl-dot completed"></i>已完成</span>
          <span class="tl-item"><i class="tl-dot pending"></i>未完成</span>
          <span class="tl-item"><i class="tl-dot overdue"></i>已截止未完成</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h3>成绩分布</h3>
        <span class="panel-sub">作业得分区间人数</span>
      </div>
      <div class="panel-body">
        <div v-if="!scoreBuckets.length" class="empty-tip">暂无成绩数据</div>
        <div v-else ref="scoreRef" class="chart-box"></div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h3>教学效果对比</h3>
        <span class="panel-sub">各课程平均分 · 通过率</span>
      </div>
      <div class="panel-body">
        <div v-if="!effectItems.length" class="empty-tip">暂无数据</div>
        <div v-else ref="effectRef" class="chart-box"></div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div class="panel-title-group">
          <h3>学习不积极学生 · 学情预警</h3>
          <span class="panel-sub">{{ warnCount }}</span>
        </div>
        <div class="panel-actions">
          <el-button size="small" type="primary" :loading="scanning" @click="scan">{{ scanning ? '扫描中…' : '立即扫描' }}</el-button>
          <router-link to="/warning"><el-button size="small">完整预警页 →</el-button></router-link>
        </div>
      </div>
      <div class="panel-body">
        <div v-if="!warnings.length" class="empty-tip">暂无学习不积极学生，点击「立即扫描」检测</div>
        <div v-else class="dash-warning-list">
          <div v-for="w in warnings" :key="w.id" class="dash-warn-item">
            <div class="dash-warn-left">
              <el-tag :type="w.risk_level === 'high' ? 'danger' : (w.risk_level === 'medium' ? 'warning' : 'success')" size="small">
                {{ RISK_ICON[w.risk_level] }} {{ RISK_LABEL[w.risk_level] || w.risk_level }}
              </el-tag>
              <span class="dash-warn-name">{{ w.student_name || ('学生#' + w.student_id) }}</span>
              <span v-if="w.course_name" class="dash-warn-course">{{ w.course_name }}</span>
            </div>
            <div class="dash-warn-reason">{{ w.reason || '-' }}</div>
            <el-button size="small" @click="resolveWarning(w.id)">标记已处理</el-button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dash-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.metric-card {
  background: #fff;
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric-label {
  font-size: 13px;
  color: #666;
}
.metric-value {
  font-size: 30px;
  font-weight: 700;
  color: #333;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.metric-unit {
  font-size: 14px;
  font-weight: 400;
  color: #999;
  margin-left: 4px;
}
.metric-trend {
  font-size: 12px;
}
.metric-trend.up { color: #2e7d32; }
.metric-trend.down { color: #e94560; }

.chart-box {
  width: 100%;
  height: 260px;
}

.heat-legend {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  font-size: 12px;
  color: #999;
}
.heat-legend-bar {
  flex: 1;
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(to right, #eadcfb, #c9a9ef, #a478e0, #7d3ec4, #5a1a9b);
}

.panel-title-group {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.panel-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.dash-warning-list {
  display: flex;
  flex-direction: column;
}
.dash-warn-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}
.dash-warn-item:last-child {
  border-bottom: none;
}
.dash-warn-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  min-width: 230px;
}
.dash-warn-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.dash-warn-course {
  font-size: 12px;
  color: #999;
}
.dash-warn-reason {
  flex: 1;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.task-heat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-x: auto;
}
.task-heat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 660px;
  padding: 4px 0;
}
.task-heat-head .th-name {
  font-weight: 600;
  color: #333;
}
.task-heat-head .th-cell {
  font-weight: 600;
  color: #555;
}
.th-name {
  width: 260px;
  flex-shrink: 0;
  font-size: 13px;
  color: #444;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.th-cell {
  width: 60px;
  flex-shrink: 0;
  text-align: center;
  font-size: 12px;
  color: #888;
}
.th-rate {
  width: 70px;
  flex-shrink: 0;
  text-align: center;
  font-size: 12px;
  color: #555;
  font-variant-numeric: tabular-nums;
}
.cell {
  display: inline-block;
  width: 18px;
  height: 18px;
  border-radius: 4px;
}
.cell.completed { background: #43a047; }
.cell.pending { background: #d0d0d0; }
.cell.overdue { background: #e94560; }
.task-heat-legend {
  display: flex;
  gap: 18px;
  margin-top: 12px;
  font-size: 12px;
  color: #666;
}
.tl-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.tl-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}
.tl-dot.completed { background: #43a047; }
.tl-dot.pending { background: #d0d0d0; }
.tl-dot.overdue { background: #e94560; }
</style>
