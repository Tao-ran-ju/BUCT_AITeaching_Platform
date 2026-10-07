<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 3000
const DEMO = reactive({
  courses: [
    { id: 1, name: '算法设计与分析' },
    { id: 2, name: '数据结构' }
  ],
  names: { 101: '张伟', 102: '李娜', 103: '王强', 201: '赵敏', 202: '刘洋' },
  assignments: {
    1: [
      { id: 1, title: '第一次作业：分治法', description: '完成归并排序与快速排序的实现', deadline: '2024-09-20 23:59', status: 'published' },
      { id: 2, title: '第二次作业：动态规划', description: '01 背包与最长公共子序列', deadline: '2024-10-10 23:59', status: 'published' }
    ],
    2: [
      { id: 3, title: '第一次作业：链表操作', description: '实现单链表的增删查改', deadline: '2024-09-25 23:59', status: 'published' }
    ]
  },
  submissions: {
    1: [
      { id: 1, student_id: 101, submit_time: '2024-09-19 20:15', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null },
      { id: 2, student_id: 102, submit_time: '2024-09-19 21:30', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null },
      { id: 3, student_id: 103, submit_time: '2024-09-19 22:05', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null }
    ],
    2: [
      { id: 4, student_id: 101, submit_time: '2024-10-08 19:10', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null }
    ],
    3: [
      { id: 5, student_id: 201, submit_time: '2024-09-24 18:40', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null },
      { id: 6, student_id: 202, submit_time: '2024-09-24 19:55', judge_status: 'pending', score: null, plagiarism_rate: null, feedback: null, ai_comment: null }
    ]
  }
})

const state = reactive({ courseId: null, assignmentId: null })

const STATUS_LABEL = { pending: '待评测', judging: '评测中', accepted: '通过', failed: '未通过' }
const STATUS_TAG = { pending: 'warning', judging: 'warning', accepted: 'success', failed: 'danger' }

const OJ_LANG_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'cpp', label: 'C++' },
  { value: 'c', label: 'C' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'sql', label: 'SQL' }
]

const judging = ref(false)
const plagiarizing = ref(false)

// ---------- 工具函数 ----------
function fmtTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').slice(0, 16)
}

function studentName(id) {
  return DEMO.names[id] || ('学生 #' + id)
}

function assignmentTitle(id) {
  const items = (state.courseId && DEMO.assignments[state.courseId]) || []
  const a = items.find((x) => x.id === id)
  return a ? a.title : ''
}

function assignmentStatusLabel(status) {
  if (status === 'published') return '已发布'
  if (status === 'closed') return '已关闭'
  return '草稿'
}

function assignmentStatusTag(status) {
  return status === 'published' ? 'success' : 'warning'
}

function plagiarismText(rate) {
  return rate != null ? Math.round(rate * 100) + '%' : '-'
}

// ---------- 计算属性 ----------
const currentAssignments = computed(() => (state.courseId && DEMO.assignments[state.courseId]) || [])
const currentSubmissions = computed(() => (state.assignmentId && DEMO.submissions[state.assignmentId]) || [])
const submissionHint = computed(() => (state.assignmentId ? '（' + assignmentTitle(state.assignmentId) + '）' : ''))

// ---------- 课程 ----------
async function loadCourses() {
  const data = await api.request(
    api.listCourses({ page: 1, page_size: 100 }),
    { items: DEMO.courses, total: DEMO.courses.length }
  )
  DEMO.courses = (data && data.items) || []
  if (DEMO.courses.length) {
    state.courseId = DEMO.courses[0].id
    loadAssignments(state.courseId)
  }
}

function onCourseChange() {
  state.assignmentId = null
  loadAssignments(state.courseId)
}

// ---------- 作业 ----------
async function loadAssignments(courseId) {
  const data = await api.request(
    api.listAssignments(courseId),
    { items: DEMO.assignments[courseId] || [], total: (DEMO.assignments[courseId] || []).length }
  )
  DEMO.assignments[courseId] = data.items || []
  if (!state.assignmentId && (data.items || []).length) {
    selectAssignment(data.items[0].id)
  }
}

function selectAssignment(id) {
  state.assignmentId = id
  loadSubmissions(id)
}

function assignmentRowClass({ row }) {
  return row.id === state.assignmentId ? 'assignment-row active' : 'assignment-row'
}

// ---------- 发布作业（模态框） ----------
const asgDialog = reactive({
  visible: false,
  classes: [],
  form: { title: '', description: '', class_id: '', oj_problem_id: '', oj_language: 'python', deadline: '' }
})

async function openAssignmentModal() {
  if (!state.courseId) {
    ElMessage.error('请先选择课程')
    return
  }
  const classData = await api.request(
    api.listClasses({ page: 1, page_size: 100 }),
    { items: [], total: 0 }
  )
  asgDialog.classes = (classData && classData.items) || []
  asgDialog.form = { title: '', description: '', class_id: '', oj_problem_id: '', oj_language: 'python', deadline: '' }
  asgDialog.visible = true
}

function submitAssignment() {
  const title = asgDialog.form.title.trim()
  if (!title) {
    ElMessage.error('作业标题不能为空')
    return
  }
  const ojProblem = String(asgDialog.form.oj_problem_id || '').trim()
  const classId = asgDialog.form.class_id ? Number(asgDialog.form.class_id) : null
  const payload = {
    course_id: state.courseId,
    class_id: classId,
    title,
    description: asgDialog.form.description.trim(),
    oj_problem_id: ojProblem ? Number(ojProblem) : null,
    oj_language: asgDialog.form.oj_language,
    deadline: asgDialog.form.deadline || null
  }
  api.request(api.createAssignment(payload)).then(() => {
    ElMessage.success('作业发布成功')
    loadAssignments(state.courseId)
  }).catch(() => {
    ;(DEMO.assignments[state.courseId] = DEMO.assignments[state.courseId] || [])
      .push(Object.assign({ id: ++demoId, status: 'published' }, payload))
    ElMessage.success('演示模式：作业已本地发布')
  })
  asgDialog.visible = false
}

// ---------- 提交 ----------
async function loadSubmissions(assignmentId) {
  const data = await api.request(api.listSubmissions(assignmentId), DEMO.submissions[assignmentId] || [])
  DEMO.submissions[assignmentId] = data
}

async function triggerJudge() {
  if (!state.assignmentId) {
    ElMessage.error('请先选择作业')
    return
  }
  const items = DEMO.submissions[state.assignmentId] || []
  if (!items.length) {
    ElMessage.error('暂无提交可评测')
    return
  }
  judging.value = true
  try {
    const results = await api.request(api.judgeAssignment(state.assignmentId), null)
    if (results) {
      DEMO.submissions[state.assignmentId] = results
      ElMessage.success('评测完成（后端）')
    } else {
      // 演示模式：本地模拟评测结果
      items.forEach((s, idx) => {
        const ok = idx % 4 !== 3 // 每第 4 个模拟一次未通过
        s.judge_status = ok ? 'accepted' : 'failed'
        s.score = ok ? Math.min(100, 82 + idx * 4) : 55
        s.plagiarism_rate = Math.min(0.3, 0.02 + idx * 0.03)
        s.feedback = ok
          ? '测试用例全部通过，代码评测通过。'
          : '存在未通过的测试用例，请检查边界条件。'
        s.ai_comment = ok
          ? '代码结构清晰，思路正确，时间复杂度符合要求。建议进一步优化边界条件的处理，并补充必要的注释。'
          : '部分测试用例未通过，存在数组越界风险，请检查边界条件后重新提交。'
      })
      DEMO.submissions[state.assignmentId] = items
      ElMessage.success('演示模式：已完成本地模拟评测')
    }
  } finally {
    judging.value = false
  }
}

async function triggerPlagiarism() {
  if (!state.assignmentId) {
    ElMessage.error('请先选择作业')
    return
  }
  const items = DEMO.submissions[state.assignmentId] || []
  if (items.length < 2) {
    ElMessage.error('提交少于 2 份，无法比对查重')
    return
  }
  plagiarizing.value = true
  try {
    const results = await api.request(api.checkPlagiarism(state.assignmentId), null)
    if (results) {
      DEMO.submissions[state.assignmentId] = results
      ElMessage.success('查重完成（后端 simhash）')
    } else {
      items.forEach((s, idx) => {
        s.plagiarism_rate = idx === 0 ? 0.02 : Math.min(0.85, 0.15 + idx * 0.2)
      })
      DEMO.submissions[state.assignmentId] = items
      ElMessage.success('演示模式：已完成本地查重')
    }
  } finally {
    plagiarizing.value = false
  }
}

// ---------- 提交详情 ----------
const subDetail = reactive({ visible: false, row: null })

function openSubDetail(row) {
  subDetail.row = row
  subDetail.visible = true
}

onMounted(loadCourses)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>作业批改与智能评测</h2>
      <p>发布作业、查看学生提交，触发 OJ 自动判题与 AI 个性化评语。</p>
    </div>

    <!-- 作业列表 -->
    <section class="panel">
      <div class="panel-head">
        <h3>作业列表</h3>
        <div class="head-actions">
          <el-select v-model="state.courseId" placeholder="选择课程" style="width: 200px" @change="onCourseChange">
            <el-option v-for="c in DEMO.courses" :key="c.id" :value="c.id" :label="c.name" />
          </el-select>
          <el-button size="small" type="primary" @click="openAssignmentModal">+ 发布作业</el-button>
        </div>
      </div>
      <div class="panel-body">
        <el-table
          :data="currentAssignments"
          :row-class-name="assignmentRowClass"
          size="small"
          @row-click="(row) => selectAssignment(row.id)"
        >
          <el-table-column label="作业标题" min-width="280">
            <template #default="{ row }">
              <div class="asg-title">{{ row.title }}</div>
              <div v-if="row.description" class="asg-desc">{{ row.description }}</div>
            </template>
          </el-table-column>
          <el-table-column label="截止时间" width="160">
            <template #default="{ row }">{{ fmtTime(row.deadline) || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="assignmentStatusTag(row.status)" size="small">{{ assignmentStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click.stop="selectAssignment(row.id)">查看提交</el-button>
            </template>
          </el-table-column>
          <template #empty>暂无作业，点击右上角「发布作业」</template>
        </el-table>
      </div>
    </section>

    <!-- 提交记录 -->
    <section class="panel">
      <div class="panel-head">
        <h3>提交记录 <span class="muted">{{ submissionHint }}</span></h3>
        <div class="panel-actions">
          <el-button size="small" :loading="plagiarizing" :disabled="plagiarizing" @click="triggerPlagiarism">
            {{ plagiarizing ? '查重中…' : '代码查重（simhash）' }}
          </el-button>
          <el-button size="small" type="primary" :loading="judging" :disabled="judging" @click="triggerJudge">
            {{ judging ? '评测中…' : '触发评测（OJ + AI 评语）' }}
          </el-button>
        </div>
      </div>
      <div class="panel-body">
        <el-table :data="currentSubmissions" size="small">
          <el-table-column label="学生" min-width="100">
            <template #default="{ row }">{{ row.student_name || studentName(row.student_id) }}</template>
          </el-table-column>
          <el-table-column label="提交时间" width="160">
            <template #default="{ row }">{{ fmtTime(row.submit_time) || '-' }}</template>
          </el-table-column>
          <el-table-column label="判题状态" width="100">
            <template #default="{ row }">
              <el-tag :type="STATUS_TAG[row.judge_status] || 'warning'" size="small">
                {{ STATUS_LABEL[row.judge_status] || row.judge_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="得分" width="80">
            <template #default="{ row }">{{ row.score != null ? row.score : '-' }}</template>
          </el-table-column>
          <el-table-column label="查重率" width="90">
            <template #default="{ row }">{{ plagiarismText(row.plagiarism_rate) }}</template>
          </el-table-column>
          <el-table-column label="AI 评语" min-width="220">
            <template #default="{ row }">
              <div v-if="row.ai_comment" class="ai-comment">{{ row.ai_comment }}</div>
              <span v-else class="pending-tip">待评测</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" @click="openSubDetail(row)">详情</el-button>
            </template>
          </el-table-column>
          <template #empty>{{ state.assignmentId ? '暂无提交记录' : '请选择作业' }}</template>
        </el-table>
      </div>
    </section>

    <!-- 发布作业对话框 -->
    <el-dialog v-model="asgDialog.visible" title="发布作业" width="560px">
      <el-form label-width="100px">
        <el-form-item label="作业标题" required>
          <el-input v-model="asgDialog.form.title" placeholder="如：第一次作业：分治法" />
        </el-form-item>
        <el-form-item label="作业说明">
          <el-input v-model="asgDialog.form.description" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        <el-form-item label="布置班级">
          <el-select v-model="asgDialog.form.class_id" clearable placeholder="（不指定班级）" style="width: 100%">
            <el-option
              v-for="c in asgDialog.classes"
              :key="c.id"
              :value="String(c.id)"
              :label="c.name || ('班级 #' + c.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="OJ 题目 ID">
          <el-input v-model="asgDialog.form.oj_problem_id" type="number" placeholder="如：1000（A+B Problem）" />
          <div class="form-hint">选填，关联 buctcoder 题目后自动判题</div>
        </el-form-item>
        <el-form-item label="判题语言">
          <el-select v-model="asgDialog.form.oj_language" style="width: 100%">
            <el-option v-for="o in OJ_LANG_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="asgDialog.form.deadline"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm"
            placeholder="选择截止时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="asgDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAssignment">确定</el-button>
      </template>
    </el-dialog>

    <!-- 提交详情对话框 -->
    <el-dialog v-model="subDetail.visible" title="提交详情" width="520px">
      <template v-if="subDetail.row">
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">学生</span>{{ subDetail.row.student_name || studentName(subDetail.row.student_id) }}</div>
          <div class="detail-item"><span class="detail-label">提交时间</span>{{ fmtTime(subDetail.row.submit_time) || '-' }}</div>
          <div class="detail-item">
            <span class="detail-label">判题状态</span>
            <el-tag :type="STATUS_TAG[subDetail.row.judge_status] || 'warning'" size="small">
              {{ STATUS_LABEL[subDetail.row.judge_status] || subDetail.row.judge_status }}
            </el-tag>
          </div>
          <div class="detail-item"><span class="detail-label">得分</span>{{ subDetail.row.score != null ? subDetail.row.score : '-' }}</div>
          <div class="detail-item"><span class="detail-label">查重率</span>{{ plagiarismText(subDetail.row.plagiarism_rate) }}</div>
        </div>
        <div class="detail-block">
          <div class="detail-label">评测反馈</div>
          <div v-if="subDetail.row.feedback" class="detail-text">{{ subDetail.row.feedback }}</div>
          <div v-else class="pending-tip">暂无反馈</div>
        </div>
        <div class="detail-block">
          <div class="detail-label">AI 评语</div>
          <div v-if="subDetail.row.ai_comment" class="detail-text">{{ subDetail.row.ai_comment }}</div>
          <div v-else class="pending-tip">待评测</div>
        </div>
      </template>
      <template #footer>
        <el-button type="primary" @click="subDetail.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.panel-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 作业行选中态 */
:deep(.assignment-row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

:deep(.assignment-row.active) {
  background-color: #f3e8ff;
}

.asg-title {
  font-weight: 600;
  color: #333;
}

.asg-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* AI 评语单元格 */
.ai-comment {
  max-width: 320px;
  color: #555;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.pending-tip {
  color: #bbb;
  font-style: italic;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  width: 100%;
}

/* 提交详情 */
.detail-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  margin-bottom: 14px;
}

.detail-item {
  font-size: 14px;
  color: #444;
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-label {
  color: #999;
  font-size: 13px;
}

.detail-block {
  margin-top: 12px;
}

.detail-block .detail-label {
  display: block;
  margin-bottom: 4px;
}

.detail-text {
  font-size: 14px;
  color: #444;
  line-height: 1.7;
  white-space: pre-wrap;
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 10px 12px;
}
</style>
