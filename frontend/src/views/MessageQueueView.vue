<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
const STORE_KEY = 'buct_msg_sent_demo'
let demoId = 100

const DEMO = reactive({
  classes: [
    { id: 1, name: '计科 2401 班' },
    { id: 2, name: '软件 2402 班' }
  ],
  students: {
    1: [
      { id: 101, username: '20240001', name: '张伟' },
      { id: 102, username: '20240002', name: '李娜' },
      { id: 103, username: '20240003', name: '王强' }
    ],
    2: [
      { id: 201, username: '20240010', name: '赵敏' },
      { id: 202, username: '20240011', name: '刘洋' }
    ]
  },
  messages: [
    {
      id: 1, title: '关于算法竞赛校内选拔的通知',
      content: '2024 年算法竞赛校内选拔将于 10 月中旬举行，请各班级组织学生报名，并于 10 月 10 日前提交报名表。',
      message_type: 'notice', created_at: '2024-09-12 10:00',
      deadline: null, attachment_url: null, attachment_name: null,
      receiver_ids: [20240001, 20240002], receiver_count: 2, unread_count: 1
    },
    {
      id: 2, title: '数据结构实验三任务发布',
      content: '请完成「二叉树遍历」实验报告，包含代码实现与运行截图，截止前提交至作业系统。',
      message_type: 'assignment', created_at: '2024-09-15 09:00',
      deadline: '2024-09-25 23:59', attachment_url: null, attachment_name: null,
      receiver_ids: [20240010, 20240011], receiver_count: 2, unread_count: 2
    }
  ],
  courses: [
    { id: 1, name: '算法设计与分析' },
    { id: 2, name: '数据结构' }
  ],
  tasks: [
    {
      id: 1, course_id: 1, title: '完成「动态规划」知识点学习',
      description: '观看第三章动态规划视频并完成配套练习',
      task_type: 'knowledge_point', deadline: '2024-09-28 23:59',
      created_by: 1, created_at: '2024-09-16 09:00',
      student_count: 3, completed_count: 1,
      assignments: [
        { student_id: 101, name: '张伟', username: '20240001', status: 'completed', completed_at: '2024-09-18 10:00' },
        { student_id: 102, name: '李娜', username: '20240002', status: 'pending', completed_at: null },
        { student_id: 103, name: '王强', username: '20240003', status: 'pending', completed_at: null }
      ]
    }
  ],
  qa: {
    pending: [
      { id: 1, student_id: 101, student_name: '张伟', content: '我在做动态规划作业时，01 背包的递推公式总是推不出来，能帮我看看思路吗？', classification: 'complex', created_at: '2024-09-20 14:30' },
      { id: 2, student_id: 102, student_name: '李娜', content: '运行归并排序代码时报了段错误，不知道哪里越界了，代码在作业里。', classification: 'complex', created_at: '2024-09-20 15:10' }
    ],
    stats: { pending: 2, auto_answered: 5, answered: 1 }
  }
})

const messages = ref([])
const tasks = ref([])
const qaData = reactive({ pending: [], stats: { pending: 0, auto_answered: 0, answered: 0 } })

const TASK_TYPE_LABEL = { knowledge_point: '知识点', oj: 'OJ 题目', acdc: 'ACDC 任务', other: '其他' }
const TASK_TYPE_OPTIONS = [
  { value: 'knowledge_point', label: '知识点学习' },
  { value: 'oj', label: 'OJ 题目' },
  { value: 'acdc', label: 'ACDC 任务' },
  { value: 'other', label: '其他' }
]

// ---------- 发布表单 ----------
const msgType = ref('notice')
const msgTitle = ref('')
const msgContent = ref('')
const msgDeadline = ref('')
const classSelect = ref('')
const msgReceivers = ref('')
const msgFile = ref(null)

// ---------- 工具函数 ----------
function nowStr() {
  const d = new Date()
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

// 兼容后端 ISO 格式（2024-09-15T09:00:00）与演示格式（2024-09-15 09:00）
function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}

// 附件的绝对访问地址（后端 /uploads 静态目录）
function attachmentHref(url) {
  if (!url) return ''
  if (/^https?:/i.test(url)) return url
  const origin = String(api.BASE_URL).replace(/\/api\/v\d+$/, '')
  return origin + (url.charAt(0) === '/' ? '' : '/') + url
}

function parseReceivers(raw) {
  return (raw || '').split(/[\s,，;；]+/)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n) && n > 0)
}

function truncateText(s, n) {
  s = s || ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

function taskTypeLabel(t) {
  return TASK_TYPE_LABEL[t] || '其他'
}

function taskStatus(t) {
  if (t.deadline && fmtTime(t.deadline) < nowStr()) {
    return { label: '已截止', type: 'danger' }
  }
  if ((t.completed_count || 0) >= (t.student_count || 0) && (t.student_count || 0) > 0) {
    return { label: '已全部完成', type: 'success' }
  }
  return { label: '进行中', type: 'warning' }
}

function taskPct(t) {
  const done = t.completed_count || 0
  const total = t.student_count || 0
  return total ? Math.round(done / total * 100) : 0
}

function pendingNames(t) {
  return truncateText(
    (t.assignments || []).filter((a) => a.status !== 'completed').map((a) => a.name).join('、'),
    30
  )
}

// ---------- 计算属性 ----------
const notices = computed(() => {
  return messages.value
    .filter((m) => m.message_type === 'notice' || m.message_type === 'system')
    .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
})

const sortedTasks = computed(() => {
  return [...tasks.value].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
})

const taskHint = computed(() => '共 ' + tasks.value.length + ' 项')

// ---------- 演示持久化 ----------
function loadDemoStore() {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (raw) {
      const arr = JSON.parse(raw)
      if (Array.isArray(arr) && arr.length) DEMO.messages = arr
    }
  } catch (e) { /* ignore */ }
}

function saveDemo() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(DEMO.messages)) } catch (e) { /* ignore */ }
}

// ---------- 加载 ----------
async function loadMessages() {
  const data = await api.request(api.listSentMessages(), DEMO.messages)
  messages.value = Array.isArray(data) ? data : ((data && data.items) || [])
}

async function loadClasses() {
  const data = await api.request(
    api.listClasses({ page: 1, page_size: 100 }),
    { items: DEMO.classes, total: DEMO.classes.length }
  )
  DEMO.classes = (data && data.items) || []
}

async function getClassStudents(classId) {
  const students = await api.request(api.listClassStudents(classId), DEMO.students[classId] || [])
  DEMO.students[classId] = students || []
  return DEMO.students[classId]
}

async function loadClassStudents(classId) {
  const students = await getClassStudents(classId)
  msgReceivers.value = students.map((s) => s.username).join(', ')
}

async function loadTasks() {
  const data = await api.request(api.listTasks(), DEMO.tasks)
  tasks.value = Array.isArray(data) ? data : []
}

async function loadQaQuestions() {
  const data = await api.request(api.listQaQuestions(), DEMO.qa)
  const d = data || { pending: [], stats: { pending: 0, auto_answered: 0, answered: 0 } }
  qaData.pending = Array.isArray(d.pending) ? d.pending : []
  qaData.stats = d.stats || { pending: 0, auto_answered: 0, answered: 0 }
}

// ---------- 发布 ----------
function onMsgFileChange(e) {
  msgFile.value = e.target.files && e.target.files[0]
}

function onClassChange() {
  const cid = Number(classSelect.value)
  if (!cid) {
    msgReceivers.value = ''
    return
  }
  loadClassStudents(cid)
}

function resetForm() {
  msgType.value = 'notice'
  msgTitle.value = ''
  msgContent.value = ''
  msgDeadline.value = ''
  classSelect.value = ''
  msgReceivers.value = ''
  msgFile.value = null
}

function submitMessage() {
  const type = msgType.value
  const title = msgTitle.value.trim()
  const content = msgContent.value.trim()
  const deadline = msgDeadline.value ? String(msgDeadline.value).trim() : ''

  if (!title) { ElMessage.error('请填写标题'); return }
  if (!content) { ElMessage.error('请填写内容'); return }
  const receiverIds = parseReceivers(msgReceivers.value)
  if (!receiverIds.length) { ElMessage.error('请填写接收学生学号'); return }

  const fd = new FormData()
  fd.append('title', title)
  fd.append('content', content)
  fd.append('message_type', type)
  fd.append('receiver_ids', JSON.stringify(receiverIds))
  if (type === 'assignment' && deadline) {
    fd.append('deadline', deadline)
  }
  if (msgFile.value) {
    fd.append('file', msgFile.value)
  }

  api.request(api.sendMessage(fd)).then(() => {
    ElMessage.success('发布成功')
    resetForm()
    loadMessages()
  }).catch(() => {
    // 演示模式：本地追加
    DEMO.messages.unshift({
      id: ++demoId, title, content,
      message_type: type, created_at: nowStr(),
      deadline: (type === 'assignment' && deadline) ? deadline : null,
      attachment_url: null,
      attachment_name: msgFile.value ? msgFile.value.name : null,
      receiver_ids: receiverIds, receiver_count: receiverIds.length, unread_count: receiverIds.length
    })
    saveDemo()
    ElMessage.success('演示模式：消息已本地发布')
    resetForm()
    loadMessages()
  })
}

// ---------- 任务看板 ----------
async function deleteTask(id) {
  try {
    await ElMessageBox.confirm('确定删除该学习任务？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.deleteTask(id)).then(() => {
    ElMessage.success('任务已删除')
    loadTasks()
  }).catch(() => {
    tasks.value = tasks.value.filter((t) => t.id !== id)
    ElMessage.success('演示模式：任务已本地删除')
  })
}

// ---------- 发布学习任务（模态框） ----------
const taskDialog = reactive({
  visible: false,
  form: { title: '', task_type: 'knowledge_point', deadline: '', course_id: '', description: '', class_id: '' },
  students: [],
  selectedIds: []
})

function openTaskModal() {
  taskDialog.form = { title: '', task_type: 'knowledge_point', deadline: '', course_id: '', description: '', class_id: '' }
  taskDialog.students = []
  taskDialog.selectedIds = []
  taskDialog.visible = true
}

function onTaskClassChange() {
  const cid = Number(taskDialog.form.class_id)
  if (!cid) {
    taskDialog.students = []
    taskDialog.selectedIds = []
    return
  }
  getClassStudents(cid).then((list) => {
    taskDialog.students = list || []
    taskDialog.selectedIds = []
  })
}

function submitTask() {
  const title = taskDialog.form.title.trim()
  const classId = Number(taskDialog.form.class_id)
  const desc = taskDialog.form.description.trim()
  if (!title) { ElMessage.error('请填写任务标题'); return }
  if (!classId) { ElMessage.error('请选择班级'); return }
  // 学校 class_tasks 为班级级任务：全班学生均需完成，按班级下发即可
  const content = title + (desc ? '\n' + desc : '')
  const payload = {
    class_id: classId,
    task_type: taskDialog.form.task_type,
    content,
    deadline: taskDialog.form.deadline || null
  }
  api.request(api.createTask(payload)).then(() => {
    ElMessage.success('学习任务已发布')
    loadTasks()
  }).catch(() => {
    const memberList = DEMO.students[classId] || []
    tasks.value.unshift({
      id: ++demoId, class_id: classId, title,
      description: desc, task_type: payload.task_type,
      deadline: payload.deadline, created_by: 1, created_at: nowStr(),
      student_count: memberList.length, completed_count: 0,
      assignments: memberList.map((s) => ({
        student_id: s.id, name: s.name, username: s.username, status: 'pending', completed_at: null
      }))
    })
    ElMessage.success('演示模式：任务已本地发布')
  })
  taskDialog.visible = false
}

// ---------- AI 问答助手 ----------
const answerDialog = reactive({ visible: false, id: null, question: null, answer: '' })

function openAnswerModal(id) {
  const q = (qaData.pending || []).find((x) => x.id === id)
  if (!q) return
  answerDialog.id = id
  answerDialog.question = q
  answerDialog.answer = ''
  answerDialog.visible = true
}

function submitAnswer() {
  const answer = answerDialog.answer.trim()
  if (!answer) {
    ElMessage.error('请填写回答内容')
    return
  }
  const id = answerDialog.id
  api.request(api.answerQuestion(id, { answer })).then(() => {
    ElMessage.success('已回复学生')
    loadQaQuestions()
  }).catch(() => {
    qaData.pending = (qaData.pending || []).filter((x) => x.id !== id)
    if (qaData.stats) {
      qaData.stats.pending = Math.max(0, (qaData.stats.pending || 0) - 1)
      qaData.stats.answered = (qaData.stats.answered || 0) + 1
    }
    ElMessage.success('演示模式：已本地回复')
  })
  answerDialog.visible = false
}

onMounted(() => {
  loadDemoStore()
  loadMessages()
  loadTasks()
  loadClasses()
  loadQaQuestions()
})
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>通知公告与任务发布</h2>
      <p>向学生批量发布通知与作业任务，支持 Word 附件；发布后写入消息中心，学生端实时可见。</p>
    </div>

    <div class="mq-layout">
      <!-- 左栏：通知公告 -->
      <section class="panel mq-left">
        <div class="panel-head">
          <h3>通知公告</h3>
        </div>
        <div class="panel-body">
          <ul class="notice-list">
            <li v-if="!notices.length" class="empty-tip">暂无通知公告</li>
            <li v-for="m in notices" :key="m.id" class="notice-item">
              <div class="notice-head">
                <el-tag :type="m.message_type === 'system' ? 'warning' : 'success'" size="small">
                  {{ m.message_type === 'system' ? '系统' : '公告' }}
                </el-tag>
                <span class="notice-title">{{ m.title }}</span>
                <span class="notice-time">{{ fmtTime(m.created_at) }}</span>
              </div>
              <div class="notice-content">{{ m.content }}</div>
              <a
                v-if="m.attachment_url"
                class="attachment-link"
                :href="attachmentHref(m.attachment_url)"
                target="_blank"
              >📎 {{ m.attachment_name || '附件' }}</a>
              <div class="notice-meta">已发送给 {{ m.receiver_count || 0 }} 人 · {{ m.unread_count || 0 }} 人未读</div>
            </li>
          </ul>
        </div>
      </section>

      <!-- 右栏：发布 + 任务看板 -->
      <div class="mq-right">
        <section class="panel">
          <div class="panel-head">
            <h3>发布通知 / 任务</h3>
          </div>
          <div class="panel-body">
            <el-form label-width="110px" label-position="left" @submit.prevent="submitMessage">
              <el-form-item label="类型">
                <el-select v-model="msgType" style="width: 100%">
                  <el-option value="notice" label="通知公告" />
                  <el-option value="assignment" label="作业任务" />
                  <el-option value="system" label="系统消息" />
                </el-select>
              </el-form-item>
              <el-form-item label="标题">
                <el-input v-model="msgTitle" placeholder="请输入标题" />
              </el-form-item>
              <el-form-item label="内容">
                <el-input v-model="msgContent" type="textarea" :rows="3" placeholder="请输入通知 / 任务内容" />
              </el-form-item>
              <el-form-item v-if="msgType === 'assignment'" label="截止时间">
                <el-date-picker
                  v-model="msgDeadline"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm"
                  placeholder="选择截止时间"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="接收班级">
                <el-select v-model="classSelect" clearable placeholder="手动填写学号" style="width: 100%" @change="onClassChange">
                  <el-option v-for="c in DEMO.classes" :key="c.id" :value="String(c.id)" :label="c.name" />
                </el-select>
              </el-form-item>
              <el-form-item label="接收学生学号">
                <el-input
                  v-model="msgReceivers"
                  type="textarea"
                  :rows="3"
                  placeholder="学号，逗号或换行分隔，如：2022040152, 2022040153"
                />
                <div class="form-hint">选择班级后自动填充该班学生学号，也可手动修改。</div>
              </el-form-item>
              <el-form-item label="Word 附件">
                <input type="file" accept=".doc,.docx" class="file-input" @change="onMsgFileChange">
                <div class="form-hint">仅支持 .doc / .docx，单个不超过 10MB。</div>
              </el-form-item>
              <el-button type="primary" native-type="submit">发布</el-button>
            </el-form>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>任务看板 <span class="muted">{{ taskHint }}</span></h3>
            <el-button size="small" type="primary" @click="openTaskModal">+ 发布学习任务</el-button>
          </div>
          <div class="panel-body">
            <ul class="task-list">
              <li v-if="!tasks.length" class="empty-tip">暂无学习任务，点击右上角「发布学习任务」</li>
              <li v-for="t in sortedTasks" :key="t.id" class="task-item">
                <div class="task-info">
                  <div class="task-title">
                    {{ t.title }}
                    <el-tag class="task-type-tag" type="primary" size="small">{{ taskTypeLabel(t.task_type) }}</el-tag>
                  </div>
                  <div class="task-deadline">截止：{{ t.deadline ? fmtTime(t.deadline) : '不限' }}</div>
                  <div class="task-progress"><div class="task-progress-bar" :style="{ width: taskPct(t) + '%' }"></div></div>
                  <div class="task-receivers">
                    完成进度：{{ t.completed_count || 0 }} / {{ t.student_count || 0 }} 人
                    <span v-if="pendingNames(t)"> · 待完成：{{ pendingNames(t) }}</span>
                  </div>
                </div>
                <el-tag :type="taskStatus(t).type" size="small">{{ taskStatus(t).label }}</el-tag>
                <el-button size="small" type="danger" @click="deleteTask(t.id)">删除</el-button>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>

    <!-- AI 问答助手分区 -->
    <section class="panel qa-panel">
      <div class="panel-head">
        <h3>AI 问答助手</h3>
        <span class="muted">学生提问自动分流：简单问题 AI 直接回复，复杂问题留待你人工处理</span>
      </div>
      <div class="panel-body">
        <div class="qa-stats">
          <div class="qa-stat">
            <span class="qa-stat-num high">{{ qaData.stats.pending || 0 }}</span>
            <span class="qa-stat-label">待处理</span>
          </div>
          <div class="qa-stat">
            <span class="qa-stat-num low">{{ qaData.stats.auto_answered || 0 }}</span>
            <span class="qa-stat-label">已自动回复</span>
          </div>
          <div class="qa-stat">
            <span class="qa-stat-num medium">{{ qaData.stats.answered || 0 }}</span>
            <span class="qa-stat-label">已人工回复</span>
          </div>
        </div>
        <ul class="qa-list">
          <li v-if="!qaData.pending.length" class="empty-tip">暂无待处理问题 🎉</li>
          <li v-for="q in qaData.pending" :key="q.id" class="qa-item">
            <div class="qa-item-head">
              <span class="qa-student">{{ q.student_name || ('学生#' + q.student_id) }}</span>
              <span class="qa-time">{{ fmtTime(q.created_at) }}</span>
            </div>
            <div class="qa-content">{{ q.content }}</div>
            <div class="qa-item-foot">
              <el-tag type="danger" size="small">待处理</el-tag>
              <el-button size="small" @click="openAnswerModal(q.id)">回答</el-button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- 发布学习任务对话框 -->
    <el-dialog v-model="taskDialog.visible" title="发布学习任务" width="560px">
      <el-form label-width="100px">
        <el-form-item label="任务标题" required>
          <el-input v-model="taskDialog.form.title" placeholder="如：完成动态规划知识点学习" />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="taskDialog.form.task_type" style="width: 100%">
            <el-option v-for="o in TASK_TYPE_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="taskDialog.form.deadline"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm"
            placeholder="选择截止时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="所属课程">
          <el-select v-model="taskDialog.form.course_id" clearable placeholder="（不归属课程）" style="width: 100%">
            <el-option v-for="c in DEMO.courses" :key="c.id" :value="String(c.id)" :label="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskDialog.form.description" type="textarea" :rows="2" placeholder="任务要求、目标…" />
        </el-form-item>
        <el-form-item label="选择班级" required>
          <el-select v-model="taskDialog.form.class_id" placeholder="请选择班级" style="width: 100%" @change="onTaskClassChange">
            <el-option v-for="c in DEMO.classes" :key="c.id" :value="String(c.id)" :label="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="勾选指派学生">
          <div class="member-picker">
            <template v-if="!taskDialog.form.class_id">请先选择班级</template>
            <el-checkbox-group v-else v-model="taskDialog.selectedIds" class="member-checkbox-group">
              <el-checkbox v-for="s in taskDialog.students" :key="s.id" :value="s.id">
                {{ s.name }}（{{ s.username }}）
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">发布</el-button>
      </template>
    </el-dialog>

    <!-- 回答学生提问对话框 -->
    <el-dialog v-model="answerDialog.visible" title="回答学生提问" width="520px">
      <div v-if="answerDialog.question" class="qa-question-box">
        <div class="qa-question-meta">
          {{ answerDialog.question.student_name || ('学生#' + answerDialog.question.student_id) }} · {{ fmtTime(answerDialog.question.created_at) }}
        </div>
        <div class="qa-question-text">{{ answerDialog.question.content }}</div>
      </div>
      <el-form label-width="80px">
        <el-form-item label="你的回答">
          <el-input v-model="answerDialog.answer" type="textarea" :rows="4" placeholder="输入解答内容，将直接回复给学生" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="answerDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAnswer">回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.mq-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.mq-left {
  flex: 1 1 58%;
  min-width: 0;
}

.mq-right {
  flex: 1 1 42%;
  min-width: 0;
}

/* 通知列表 */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notice-item {
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 12px 14px;
  background-color: #fefefe;
  transition: border-color 0.2s;
}

.notice-item:hover {
  border-color: var(--brand-primary);
}

.notice-item.pinned {
  border-left: 4px solid var(--brand-primary);
  background-color: #fbf7ff;
}

.notice-item .notice-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.notice-item .notice-title {
  font-weight: 600;
  color: #333;
  flex: 1;
}

.notice-item .notice-time {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.notice-item .notice-content {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  word-break: break-word;
}

/* 任务看板 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-item .task-info {
  flex: 1;
  min-width: 0;
}

.task-item .task-title {
  font-weight: 600;
  color: #333;
}

.task-item .task-deadline {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* 表单提示 */
.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  width: 100%;
  line-height: 1.5;
}

.file-input {
  padding: 6px;
}

/* 附件链接 */
.attachment-link {
  font-size: 13px;
  color: #6a0dad;
  text-decoration: none;
  display: inline-block;
  margin-top: 6px;
}

.attachment-link:hover {
  text-decoration: underline;
}

/* 通知 / 任务元信息 */
.notice-meta {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.task-receivers {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* 任务完成进度条 */
.task-progress {
  height: 6px;
  border-radius: 3px;
  background: #eee;
  margin-top: 6px;
  overflow: hidden;
}

.task-progress-bar {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #6a0dad, #9b59b6);
  transition: width 0.3s;
}

/* 任务类型标签 */
.task-type-tag {
  vertical-align: 1px;
  margin-left: 4px;
}

/* 模态框内学生勾选 */
.member-picker {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #555;
  width: 100%;
}

.member-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ---------- AI 问答助手分区 ---------- */
.qa-panel {
  margin-top: 20px;
}

.qa-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.qa-stat {
  flex: 1 1 120px;
  min-width: 120px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 12px;
  text-align: center;
  background-color: #fefefe;
}

.qa-stat-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.qa-stat-num.high {
  color: #e74c3c;
}

.qa-stat-num.low {
  color: #27ae60;
}

.qa-stat-num.medium {
  color: #f39c12;
}

.qa-stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.qa-item {
  border: 1px solid #e5e5e5;
  border-left: 4px solid #f39c12;
  border-radius: 4px;
  padding: 12px 14px;
  background-color: #fefefe;
}

.qa-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.qa-student {
  font-weight: 600;
  color: #333;
}

.qa-time {
  font-size: 12px;
  color: #999;
  margin-left: auto;
}

.qa-content {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  word-break: break-word;
}

.qa-item-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

/* 回答模态框内的原问题展示 */
.qa-question-box {
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  background: #fafafa;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.qa-question-meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}

.qa-question-text {
  font-size: 14px;
  color: #444;
  line-height: 1.7;
  word-break: break-word;
}
</style>
