<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api/index.js'

const props = defineProps({
  classId: { type: Number, required: true }
})

let demoId = 100
const DEMO_TASKS = [
  {
    id: 1, class_id: 1, title: '完成「动态规划」知识点学习',
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
]

const TASK_TYPE_LABEL = { knowledge_point: '知识点', oj: 'OJ 题目', acdc: 'ACDC 任务', other: '其他' }
const TASK_TYPE_OPTIONS = [
  { value: 'knowledge_point', label: '知识点学习' },
  { value: 'oj', label: 'OJ 题目' },
  { value: 'acdc', label: 'ACDC 任务' },
  { value: 'other', label: '其他' }
]

const tasks = ref([])

function nowStr() {
  const d = new Date()
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}
function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}
function taskTypeLabel(t) {
  return TASK_TYPE_LABEL[t] || '其他'
}
function taskTitle(t) {
  return t.title || t.content || ''
}
function taskStatus(t) {
  if (t.deadline && fmtTime(t.deadline) < nowStr()) return { label: '已截止', type: 'danger' }
  if ((t.completed_count || 0) >= (t.student_count || 0) && (t.student_count || 0) > 0) return { label: '已全部完成', type: 'success' }
  return { label: '进行中', type: 'warning' }
}
function taskPct(t) {
  const done = t.completed_count || 0
  const total = t.student_count || 0
  return total ? Math.round(done / total * 100) : 0
}
function pendingNames(t) {
  const s = (t.assignments || []).filter((a) => a.status !== 'completed').map((a) => a.name).join('、')
  return s.length > 30 ? s.slice(0, 30) + '…' : s
}

const sortedTasks = computed(() =>
  tasks.value
    .filter((t) => Number(t.class_id) === Number(props.classId))
    .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
)
const taskHint = computed(() => '共 ' + sortedTasks.value.length + ' 项')

async function loadTasks() {
  const data = await api.request(api.listTasks(), DEMO_TASKS)
  tasks.value = Array.isArray(data) ? data : ((data && data.items) || [])
}

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

const taskDialog = reactive({ visible: false, form: { title: '', task_type: 'knowledge_point', deadline: '', description: '' } })

function openTaskModal() {
  taskDialog.form = { title: '', task_type: 'knowledge_point', deadline: '', description: '' }
  taskDialog.visible = true
}

function submitTask() {
  const title = taskDialog.form.title.trim()
  const desc = taskDialog.form.description.trim()
  if (!title) {
    ElMessage.error('请填写任务标题')
    return
  }
  // 学校 class_tasks 为班级级任务：全班学生均需完成，按班级下发即可
  const content = title + (desc ? '\n' + desc : '')
  const payload = {
    class_id: Number(props.classId),
    task_type: taskDialog.form.task_type,
    content,
    deadline: taskDialog.form.deadline || null
  }
  api.request(api.createTask(payload)).then(() => {
    ElMessage.success('学习任务已发布')
    loadTasks()
  }).catch(() => {
    tasks.value.unshift({
      id: ++demoId, class_id: Number(props.classId), title,
      description: desc, task_type: payload.task_type,
      deadline: payload.deadline, created_by: 1, created_at: nowStr(),
      student_count: 0, completed_count: 0, assignments: []
    })
    ElMessage.success('演示模式：任务已本地发布')
  })
  taskDialog.visible = false
}

onMounted(loadTasks)
watch(() => props.classId, loadTasks)
</script>

<template>
  <div>
    <div class="task-toolbar">
      <el-button size="small" type="primary" @click="openTaskModal">+ 发布学习任务</el-button>
      <span class="muted">{{ taskHint }}</span>
    </div>

    <ul class="task-list">
      <li v-if="!sortedTasks.length" class="empty-tip">暂无学习任务，点击「发布学习任务」</li>
      <li v-for="t in sortedTasks" :key="t.id" class="task-item">
        <div class="task-info">
          <div class="task-title">
            {{ taskTitle(t) }}
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

    <el-dialog v-model="taskDialog.visible" title="发布学习任务" width="520px">
      <el-form label-width="90px">
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
        <el-form-item label="任务描述">
          <el-input v-model="taskDialog.form.description" type="textarea" :rows="2" placeholder="任务要求、目标…" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.task-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

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

.task-receivers {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.task-type-tag {
  vertical-align: 1px;
  margin-left: 4px;
}
</style>
