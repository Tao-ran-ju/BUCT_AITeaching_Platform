<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 1000
const DEMO = reactive({
  courses: [
    { id: 1, name: '算法设计与分析' },
    { id: 2, name: '数据结构' }
  ],
  classes: [
    { id: 1, name: '计科 2401 班' },
    { id: 2, name: '软件 2402 班' }
  ],
  students: {
    1: [
      { id: 101, username: '2022040101', name: '张伟' },
      { id: 102, username: '2022040102', name: '李娜' },
      { id: 103, username: '2022040103', name: '王强' }
    ],
    2: [
      { id: 201, username: '2022040104', name: '赵敏' },
      { id: 202, username: '2022040105', name: '刘洋' }
    ]
  },
  teams: [
    {
      id: 1, name: 'DP 攻坚组', course_id: 1, leader_id: 101,
      description: '围绕动态规划专题互助学习',
      created_at: '2024-09-10 10:00',
      members: [
        { student_id: 101, name: '张伟', username: '2022040101' },
        { student_id: 102, name: '李娜', username: '2022040102' }
      ]
    }
  ],
  tasks: [
    { id: 1, team_id: 1, title: '完成动态规划专题练习', description: '整理 DP 模板并互相批改', deadline: '2024-09-28 23:59', status: 'pending', created_at: '2024-09-16 09:00' },
    { id: 2, team_id: 1, title: '提交小组汇报 PPT', description: '', deadline: '2024-09-25 23:59', status: 'completed', created_at: '2024-09-15 09:00' }
  ]
})

const teams = ref([])
const tasks = ref([])
const studentsCache = reactive({}) // classId -> [{ id, username, name }]
const pickerStudents = ref([])

const teamForm = reactive({ name: '', courseId: '', classId: '', leaderId: '', description: '' })
const leaderOptions = computed(() => (teamForm.classId && studentsCache[Number(teamForm.classId)]) || [])

// ---------- 加载 ----------
async function loadCourses() {
  const data = await api.request(
    api.listCourses({ page: 1, page_size: 100 }),
    { items: DEMO.courses, total: DEMO.courses.length }
  )
  DEMO.courses = (data && data.items) || []
}

async function loadClasses() {
  const data = await api.request(
    api.listClasses({ page: 1, page_size: 100 }),
    { items: DEMO.classes, total: DEMO.classes.length }
  )
  DEMO.classes = (data && data.items) || []
}

async function loadClassStudents(classId) {
  const cid = Number(classId)
  if (!cid) return []
  const fallback = DEMO.students[cid] || []
  const students = await api.request(api.listClassStudents(cid), fallback)
  studentsCache[cid] = students || []
  return studentsCache[cid]
}

async function loadTeams() {
  const data = await api.request(api.listTeams(), DEMO.teams)
  teams.value = Array.isArray(data) ? data : []
}

async function loadTasks() {
  const data = await api.request(api.listTasks(), DEMO.tasks)
  tasks.value = Array.isArray(data) ? data : []
}

function courseName(id) {
  if (!id) return '通用'
  const c = DEMO.courses.find((x) => x.id === id)
  return c ? c.name : '课程#' + id
}

function teamName(id) {
  if (!id) return '通用'
  const t = teams.value.find((x) => x.id === id) || DEMO.teams.find((x) => x.id === id)
  return t ? t.name : '小组#' + id
}

function findStudent(sid) {
  for (const cid in studentsCache) {
    const s = (studentsCache[cid] || []).find((x) => x.id === sid)
    if (s) return s
  }
  return null
}

function leaderName(leaderId) {
  const s = findStudent(leaderId)
  return s ? s.name : '组长'
}

function leaderOf(t) {
  const m = (t.members || []).find((x) => x.student_id === t.leader_id)
  return m ? m.name : '成员#' + t.leader_id
}

function studentLabel(s) {
  return s.name + '（' + s.username + '）'
}

// ---------- 创建小组 ----------
watch(
  () => teamForm.classId,
  async (classId) => {
    teamForm.leaderId = ''
    if (classId) {
      await loadClassStudents(classId)
    }
  }
)

function resetTeamForm() {
  teamForm.name = ''
  teamForm.courseId = ''
  teamForm.classId = ''
  teamForm.leaderId = ''
  teamForm.description = ''
}

function submitTeam() {
  const name = teamForm.name.trim()
  const courseId = teamForm.courseId ? Number(teamForm.courseId) : null
  const leaderId = teamForm.leaderId ? Number(teamForm.leaderId) : null
  const desc = teamForm.description.trim()
  if (!name) {
    ElMessage.error('请填写小组名称')
    return
  }
  if (!leaderId) {
    ElMessage.error('请选择组长')
    return
  }
  api.request(api.createTeam({ name, course_id: courseId, leader_id: leaderId, description: desc })).then(() => {
    ElMessage.success('小组创建成功')
    resetTeamForm()
    loadTeams()
  }).catch(() => {
    teams.value.push({
      id: ++demoId, name, course_id: courseId, leader_id: leaderId,
      description: desc, created_at: new Date().toISOString(),
      members: [{ student_id: leaderId, name: leaderName(leaderId), username: '' }]
    })
    ElMessage.success('演示模式：小组已本地创建')
    resetTeamForm()
  })
}

// ---------- 编辑小组 ----------
const teamDialog = reactive({ visible: false, id: null, form: { name: '', description: '' } })

function openEditTeam(id) {
  const t = teams.value.find((x) => x.id === id)
  if (!t) return
  teamDialog.id = id
  teamDialog.form = { name: t.name || '', description: t.description || '' }
  teamDialog.visible = true
}

function submitEditTeam() {
  const name = teamDialog.form.name.trim()
  if (!name) {
    ElMessage.error('小组名称不能为空')
    return
  }
  const payload = { name, description: teamDialog.form.description.trim() }
  const id = teamDialog.id
  api.request(api.updateTeam(id, payload)).then(() => {
    ElMessage.success('小组已更新')
    loadTeams()
  }).catch(() => {
    const t = teams.value.find((x) => x.id === id)
    if (t) {
      t.name = payload.name
      t.description = payload.description
    }
    ElMessage.success('演示模式：小组已本地更新')
  })
  teamDialog.visible = false
}

async function deleteTeam(id) {
  try {
    await ElMessageBox.confirm('确定删除该学习小组？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.deleteTeam(id)).then(() => {
    ElMessage.success('小组已删除')
    loadTeams()
  }).catch(() => {
    teams.value = teams.value.filter((x) => x.id !== id)
    ElMessage.success('演示模式：小组已本地删除')
  })
}

// ---------- 添加成员 ----------
const addMemberDialog = reactive({ visible: false, teamId: null, classId: null, selectedIds: [] })

watch(
  () => addMemberDialog.classId,
  async (classId) => {
    addMemberDialog.selectedIds = []
    if (classId) {
      pickerStudents.value = await loadClassStudents(classId)
    } else {
      pickerStudents.value = []
    }
  }
)

function openAddMember(id) {
  addMemberDialog.teamId = id
  addMemberDialog.classId = null
  addMemberDialog.selectedIds = []
  pickerStudents.value = []
  addMemberDialog.visible = true
}

function submitAddMember() {
  const id = addMemberDialog.teamId
  const ids = addMemberDialog.selectedIds.map(Number)
  if (!ids.length) {
    ElMessage.error('请勾选要添加的学生')
    return
  }
  api.request(api.addTeamMembers(id, ids)).then((res) => {
    ElMessage.success('已添加 ' + ((res && res.added) || ids.length) + ' 名成员')
    loadTeams()
  }).catch(() => {
    const t = teams.value.find((x) => x.id === id)
    if (t) {
      ids.forEach((sid) => {
        const s = findStudent(sid)
        t.members = t.members || []
        if (!t.members.some((m) => m.student_id === sid)) {
          t.members.push({ student_id: sid, name: s ? s.name : '学生', username: s ? s.username : '' })
        }
      })
    }
    ElMessage.success('演示模式：成员已本地添加')
  })
  addMemberDialog.visible = false
}

async function removeMember(teamId, studentId) {
  try {
    await ElMessageBox.confirm('确定从小组移除该成员？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.removeTeamMember(teamId, studentId)).then(() => {
    ElMessage.success('已移除该成员')
    loadTeams()
  }).catch(() => {
    const t = teams.value.find((x) => x.id === teamId)
    if (t) t.members = (t.members || []).filter((m) => m.student_id !== studentId)
    ElMessage.success('演示模式：已本地移除该成员')
  })
}

// ---------- 团队任务管理 ----------
const taskHint = computed(() => '共 ' + tasks.value.length + ' 项')
const sortedTasks = computed(() =>
  [...tasks.value].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
)

function nowStr() {
  const d = new Date()
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

function fmtTime(t) {
  if (!t) return '不限'
  return String(t).replace('T', ' ').slice(0, 16)
}

function toLocalInput(v) {
  if (!v) return ''
  return String(v).replace(' ', 'T').slice(0, 16)
}

function taskTagType(t) {
  if (t.status === 'completed') return 'success'
  if (t.deadline && fmtTime(t.deadline) < nowStr()) return 'danger'
  return 'warning'
}

function taskStatusLabel(t) {
  if (t.status === 'completed') return '已完成'
  if (t.deadline && fmtTime(t.deadline) < nowStr()) return '已截止'
  return '进行中'
}

const taskDialog = reactive({ visible: false, mode: 'create', id: null, form: { teamId: '', title: '', description: '', deadline: '' } })

function openTaskModal() {
  taskDialog.mode = 'create'
  taskDialog.id = null
  taskDialog.form = { teamId: '', title: '', description: '', deadline: '' }
  taskDialog.visible = true
}

function openEditTaskModal(id) {
  const t = tasks.value.find((x) => x.id === id)
  if (!t) return
  taskDialog.mode = 'edit'
  taskDialog.id = id
  taskDialog.form = {
    teamId: t.team_id ? String(t.team_id) : '',
    title: t.title || '',
    description: t.description || '',
    deadline: toLocalInput(t.deadline)
  }
  taskDialog.visible = true
}

function submitTask() {
  const title = taskDialog.form.title.trim()
  if (!title) {
    ElMessage.error('请填写任务标题')
    return
  }
  const payload = {
    team_id: taskDialog.form.teamId ? Number(taskDialog.form.teamId) : null,
    title,
    description: taskDialog.form.description.trim(),
    deadline: taskDialog.form.deadline ? taskDialog.form.deadline + ':00' : null
  }
  if (taskDialog.mode === 'edit') {
    const id = taskDialog.id
    api.request(api.updateTask(id, payload)).then(() => {
      ElMessage.success('任务已更新')
      loadTasks()
    }).catch(() => {
      const t = tasks.value.find((x) => x.id === id)
      if (t) Object.assign(t, payload)
      ElMessage.success('演示模式：任务已本地更新')
    })
  } else {
    api.request(api.createTask(payload)).then(() => {
      ElMessage.success('学习任务已发布')
      loadTasks()
    }).catch(() => {
      tasks.value.unshift({ id: ++demoId, ...payload, status: 'pending', created_at: nowStr() })
      ElMessage.success('演示模式：任务已本地发布')
    })
  }
  taskDialog.visible = false
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

function completeTask(id) {
  api.request(api.completeTask(id)).then(() => {
    ElMessage.success('任务已完成')
    loadTasks()
  }).catch(() => {
    const t = tasks.value.find((x) => x.id === id)
    if (t) t.status = 'completed'
    ElMessage.success('演示模式：任务已标记完成')
  })
}

onMounted(() => {
  loadCourses()
  loadClasses()
  loadTeams()
  loadTasks()
})
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>学习小组管理</h2>
      <p>组建学习小组 / 竞赛队伍，指定组长，管理成员构成。</p>
    </div>

    <div class="team-layout">
      <!-- 左栏：新建小组 -->
      <section class="panel team-left">
        <div class="panel-head"><h3>新建学习小组</h3></div>
        <div class="panel-body">
          <el-form label-position="top" @submit.prevent="submitTeam">
            <el-form-item label="小组名称">
              <el-input v-model="teamForm.name" placeholder="如：DP 攻坚组" />
            </el-form-item>
            <el-form-item label="所属课程（选填）">
              <el-select v-model="teamForm.courseId" placeholder="（不归属课程）" clearable style="width: 100%">
                <el-option v-for="c in DEMO.courses" :key="c.id" :value="String(c.id)" :label="c.name" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择班级">
              <el-select v-model="teamForm.classId" placeholder="请选择班级" style="width: 100%">
                <el-option v-for="c in DEMO.classes" :key="c.id" :value="String(c.id)" :label="c.name" />
              </el-select>
            </el-form-item>
            <el-form-item label="组长">
              <el-select v-model="teamForm.leaderId" placeholder="请选择组长" style="width: 100%">
                <el-option v-for="s in leaderOptions" :key="s.id" :value="String(s.id)" :label="studentLabel(s)" />
              </el-select>
            </el-form-item>
            <el-form-item label="简介（选填）">
              <el-input v-model="teamForm.description" type="textarea" placeholder="小组目标、分工说明…" />
            </el-form-item>
            <el-button type="primary" native-type="submit">创建小组</el-button>
          </el-form>
        </div>
      </section>

      <!-- 右栏：小组列表 -->
      <section class="panel team-right">
        <div class="panel-head"><h3>小组列表</h3></div>
        <div class="panel-body">
          <div v-if="!teams.length" class="empty-tip">暂无学习小组，左侧创建第一个</div>
          <ul v-else class="team-list">
            <li v-for="t in teams" :key="t.id" class="team-card">
              <div class="team-head">
                <span class="team-name">{{ t.name }}</span>
                <el-tag size="small" type="info">{{ courseName(t.course_id) }}</el-tag>
              </div>
              <div class="team-meta">组长：{{ leaderOf(t) }} · {{ t.member_count || (t.members || []).length }} 人</div>
              <div v-if="t.description" class="team-desc">{{ t.description }}</div>
              <div class="team-members">
                <span v-for="m in t.members" :key="m.student_id" class="member-chip" :title="m.username">
                  {{ m.name }}
                  <el-tag v-if="m.student_id === t.leader_id" size="small" type="warning" class="chip-leader">组长</el-tag>
                  <span class="chip-remove" title="移除成员" @click.stop="removeMember(t.id, m.student_id)">×</span>
                </span>
              </div>
              <div class="team-actions">
                <el-button size="small" @click="openAddMember(t.id)">添加成员</el-button>
                <el-button size="small" @click="openEditTeam(t.id)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteTeam(t.id)">删除</el-button>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </div>

    <!-- 团队任务管理 -->
    <section class="panel">
      <div class="panel-head">
        <h3>团队任务管理 <span class="muted">{{ taskHint }}</span></h3>
        <el-button size="small" type="primary" @click="openTaskModal">+ 新建任务</el-button>
      </div>
      <div class="panel-body">
        <div v-if="!tasks.length" class="empty-tip">暂无团队任务，点击右上角「新建任务」</div>
        <el-table v-else :data="sortedTasks" size="small">
          <el-table-column label="任务" min-width="220">
            <template #default="{ row }">
              <div class="task-title">{{ row.title }}</div>
              <div v-if="row.description" class="task-desc">{{ row.description }}</div>
            </template>
          </el-table-column>
          <el-table-column label="所属小组" width="140">
            <template #default="{ row }">{{ teamName(row.team_id) }}</template>
          </el-table-column>
          <el-table-column label="截止时间" width="150">
            <template #default="{ row }">{{ fmtTime(row.deadline) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="taskTagType(row)" size="small">{{ taskStatusLabel(row) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190">
            <template #default="{ row }">
              <div class="row-actions">
                <el-button v-if="row.status !== 'completed'" size="small" type="success" @click="completeTask(row.id)">完成</el-button>
                <el-button size="small" @click="openEditTaskModal(row.id)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteTask(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <!-- 编辑小组对话框 -->
    <el-dialog v-model="teamDialog.visible" title="编辑小组" width="460px">
      <el-form label-width="80px">
        <el-form-item label="小组名称" required>
          <el-input v-model="teamDialog.form.name" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="teamDialog.form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="teamDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitEditTeam">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog v-model="addMemberDialog.visible" title="添加成员" width="480px">
      <el-form label-width="80px">
        <el-form-item label="选择班级">
          <el-select v-model="addMemberDialog.classId" placeholder="请选择班级" style="width: 100%">
            <el-option v-for="c in DEMO.classes" :key="c.id" :value="String(c.id)" :label="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="勾选学生">
          <div v-if="!addMemberDialog.classId" class="member-picker muted-picker">请先选择班级</div>
          <div v-else-if="!pickerStudents.length" class="member-picker muted-picker">该班级暂无学生</div>
          <div v-else class="member-picker">
            <el-checkbox-group v-model="addMemberDialog.selectedIds">
              <el-checkbox v-for="s in pickerStudents" :key="s.id" :value="String(s.id)">
                {{ studentLabel(s) }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMemberDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAddMember">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新建 / 编辑任务对话框 -->
    <el-dialog v-model="taskDialog.visible" :title="taskDialog.mode === 'create' ? '新建团队任务' : '编辑团队任务'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="所属小组">
          <el-select v-model="taskDialog.form.teamId" placeholder="（不归属小组）" clearable style="width: 100%">
            <el-option v-for="t in teams" :key="t.id" :value="String(t.id)" :label="t.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务标题" required>
          <el-input v-model="taskDialog.form.title" placeholder="如：完成动态规划专题练习" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskDialog.form.description" type="textarea" placeholder="任务要求、目标…" />
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
      </el-form>
      <template #footer>
        <el-button @click="taskDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.team-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.team-left {
  flex: 1 1 34%;
  min-width: 0;
}
.team-right {
  flex: 1 1 66%;
  min-width: 0;
}

/* 小组卡片 */
.team-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 40px;
}
.team-card {
  border: 1px solid #e5e5e5;
  border-radius: 5px;
  padding: 12px 14px;
  background: #fff;
}
.team-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.team-name {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}
.team-meta {
  font-size: 12px;
  color: #999;
  margin: 4px 0;
}
.team-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 8px;
}
.team-members {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.team-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 成员 chip 内的组长标注与移除按钮 */
.chip-leader {
  margin-left: 4px;
}
.chip-remove {
  margin-left: 6px;
  cursor: pointer;
  color: #999;
  font-weight: 700;
  line-height: 1;
}
.chip-remove:hover {
  color: var(--brand-danger);
}

/* 成员选择 */
.member-picker {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}
.muted-picker {
  color: #999;
  font-size: 13px;
  justify-content: center;
}
.member-picker :deep(.el-checkbox) {
  width: 100%;
  margin-right: 0;
  height: auto;
}

/* 任务表格 */
.task-title {
  font-weight: 600;
  color: #333;
}
.task-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
  line-height: 1.5;
}
</style>
