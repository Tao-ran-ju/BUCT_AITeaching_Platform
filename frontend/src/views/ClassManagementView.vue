<script setup>
import { computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 2000
const DEMO = reactive({
  classes: [
    { id: 1, name: '计科 2401 班', grade: '2024', major: '计算机科学与技术', description: '算法竞赛重点班', created_at: '2024-09-01' },
    { id: 2, name: '软件 2402 班', grade: '2024', major: '软件工程', description: '', created_at: '2024-09-01' },
    { id: 3, name: '计科 2301 班', grade: '2023', major: '计算机科学与技术', description: '', created_at: '2023-09-01' }
  ],
  students: {
    1: [
      { id: 101, username: '20240001', name: '张伟', department: '计算机科学与技术', phone: '13800000001' },
      { id: 102, username: '20240002', name: '李娜', department: '计算机科学与技术', phone: '13800000002' },
      { id: 103, username: '20240003', name: '王强', department: '计算机科学与技术', phone: '13800000003' }
    ],
    2: [
      { id: 201, username: '20240010', name: '赵敏', department: '软件工程', phone: '13800000010' },
      { id: 202, username: '20240011', name: '刘洋', department: '软件工程', phone: '13800000011' }
    ],
    3: [
      { id: 301, username: '20230001', name: '陈晨', department: '计算机科学与技术', phone: '13800000020' }
    ]
  }
})

const state = reactive({ classId: null })

const currentStudents = computed(() => (state.classId && DEMO.students[state.classId]) || [])
const studentClassHint = computed(() => (state.classId ? '（' + className(state.classId) + '）' : ''))

function className(id) {
  const c = DEMO.classes.find((x) => x.id === id)
  return c ? c.name : ''
}

// ---------- 班级 ----------
async function loadClasses() {
  const data = await api.request(
    api.listClasses({ page: 1, page_size: 100 }),
    { items: DEMO.classes, total: DEMO.classes.length }
  )
  DEMO.classes = (data && data.items) || []
  if (!state.classId && DEMO.classes.length) {
    selectClass(DEMO.classes[0].id)
  }
}

function selectClass(id) {
  state.classId = id
  loadStudents(id)
}

const classDialog = reactive({ visible: false, mode: 'create', id: null, form: { name: '', grade: '', major: '', description: '' } })

function openClassModal(id) {
  const editing = id ? DEMO.classes.find((c) => c.id === id) : null
  classDialog.mode = editing ? 'edit' : 'create'
  classDialog.id = id || null
  classDialog.form = {
    name: editing ? editing.name : '',
    grade: editing ? editing.grade : '',
    major: editing ? editing.major : '',
    description: editing ? editing.description : ''
  }
  classDialog.visible = true
}

function submitClass() {
  const name = classDialog.form.name.trim()
  if (!name) {
    ElMessage.error('班级名称不能为空')
    return
  }
  const payload = {
    name,
    grade: classDialog.form.grade.trim(),
    major: classDialog.form.major.trim(),
    description: classDialog.form.description.trim()
  }
  if (classDialog.mode === 'edit') {
    const id = classDialog.id
    api.request(api.updateClass(id, payload)).then(() => {
      ElMessage.success('班级已更新')
      loadClasses()
    }).catch(() => {
      const c = DEMO.classes.find((x) => x.id === id)
      if (c) Object.assign(c, payload)
      ElMessage.success('演示模式：班级已本地更新')
    })
  } else {
    api.request(api.createClass(payload)).then(() => {
      ElMessage.success('班级创建成功')
      loadClasses()
    }).catch(() => {
      DEMO.classes.push(Object.assign({ id: ++demoId, created_at: '' }, payload))
      ElMessage.success('演示模式：班级已本地创建')
    })
  }
  classDialog.visible = false
}

async function deleteClass(id) {
  try {
    await ElMessageBox.confirm('确定删除该班级？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.deleteClass(id)
    ElMessage.success('班级已删除')
  } catch (e) {
    DEMO.classes = DEMO.classes.filter((c) => c.id !== id)
    delete DEMO.students[id]
    ElMessage.success('演示模式：班级已本地删除')
  }
  if (state.classId === id) {
    state.classId = null
  }
  loadClasses()
}

// ---------- 学生 ----------
async function loadStudents(classId) {
  const data = await api.request(api.listClassStudents(classId), DEMO.students[classId] || [])
  DEMO.students[classId] = data
}

const addStudentsDialog = reactive({ visible: false, idsText: '' })

function openAddStudentsModal() {
  if (!state.classId) {
    ElMessage.error('请先选择班级')
    return
  }
  addStudentsDialog.idsText = ''
  addStudentsDialog.visible = true
}

function submitAddStudents() {
  const raw = addStudentsDialog.idsText.trim()
  const ids = raw.split(/[\s,，;；]+/).map((s) => Number(s)).filter((n) => Number.isFinite(n) && n > 0)
  if (!ids.length) {
    ElMessage.error('请输入有效的学生 ID')
    return
  }
  api.request(api.addClassStudents(state.classId, ids), { added: 0 }).then((res) => {
    ElMessage.success('成功添加 ' + (res.added != null ? res.added : ids.length) + ' 名学生')
    loadStudents(state.classId)
  }).catch(() => {
    const existing = DEMO.students[state.classId] || []
    const existIds = existing.map((s) => s.id)
    ids.forEach((sid) => {
      if (existIds.indexOf(sid) < 0) {
        existing.push({ id: sid, username: String(sid), name: '学生' + sid, department: '', phone: '' })
        existIds.push(sid)
      }
    })
    DEMO.students[state.classId] = existing
    ElMessage.success('演示模式：已本地添加 ' + ids.length + ' 名学生')
  })
  addStudentsDialog.visible = false
}

async function removeStudent(studentId) {
  try {
    await ElMessageBox.confirm('确定从班级移除该学生？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.removeClassStudent(state.classId, studentId)
    ElMessage.success('已移除该学生')
  } catch (e) {
    DEMO.students[state.classId] = (DEMO.students[state.classId] || []).filter((s) => s.id !== studentId)
    ElMessage.success('演示模式：已本地移除该学生')
  }
  loadStudents(state.classId)
}

function classRowClass({ row }) {
  return row.id === state.classId ? 'active-row' : ''
}

onMounted(loadClasses)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>班级与学生管理</h2>
      <p>建班、维护班级信息，批量导入学生名单，管理班级学生构成。</p>
    </div>

    <div class="cm-layout">
      <!-- 左栏：班级列表 -->
      <section class="panel cm-left">
        <div class="panel-head">
          <h3>班级列表</h3>
          <el-button size="small" type="primary" @click="openClassModal(null)">+ 新建班级</el-button>
        </div>
        <div class="panel-body">
          <div v-if="!DEMO.classes.length" class="empty-tip">暂无班级</div>
          <el-table
            v-else
            class="class-table"
            :data="DEMO.classes"
            size="small"
            :row-class-name="classRowClass"
            @row-click="(row) => selectClass(row.id)"
          >
            <el-table-column label="班级" min-width="180">
              <template #default="{ row }">
                <div class="class-name">{{ row.name }}</div>
                <div v-if="row.description" class="class-desc">{{ row.description }}</div>
              </template>
            </el-table-column>
            <el-table-column label="年级" width="90">
              <template #default="{ row }">{{ row.grade || '-' }}</template>
            </el-table-column>
            <el-table-column label="专业" min-width="140">
              <template #default="{ row }">{{ row.major || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="130">
              <template #default="{ row }">
                <div class="row-actions" @click.stop>
                  <el-button size="small" @click="openClassModal(row.id)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteClass(row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <!-- 右栏：学生构成 -->
      <section class="panel cm-right">
        <div class="panel-head">
          <h3>学生构成 <span class="muted">{{ studentClassHint }}</span></h3>
          <el-button size="small" type="primary" @click="openAddStudentsModal">+ 批量添加学生</el-button>
        </div>
        <div class="panel-body">
          <div v-if="!state.classId" class="empty-tip">请选择班级</div>
          <div v-else-if="!currentStudents.length" class="empty-tip">暂无学生，点击右上角「批量添加学生」</div>
          <el-table v-else :data="currentStudents" size="small">
            <el-table-column label="学号" min-width="110">
              <template #default="{ row }">{{ row.username || '-' }}</template>
            </el-table-column>
            <el-table-column label="姓名" min-width="100">
              <template #default="{ row }">{{ row.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="专业" min-width="150">
              <template #default="{ row }">{{ row.department || '-' }}</template>
            </el-table-column>
            <el-table-column label="联系方式" min-width="120">
              <template #default="{ row }">{{ row.phone || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="removeStudent(row.id)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </div>

    <!-- 班级对话框 -->
    <el-dialog v-model="classDialog.visible" :title="classDialog.mode === 'create' ? '新建班级' : '编辑班级'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="班级名称" required>
          <el-input v-model="classDialog.form.name" placeholder="如：计科 2401 班" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="classDialog.form.grade" placeholder="如：2024" />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="classDialog.form.major" placeholder="如：计算机科学与技术" />
        </el-form-item>
        <el-form-item label="班级简介">
          <el-input v-model="classDialog.form.description" type="textarea" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitClass">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加学生对话框 -->
    <el-dialog v-model="addStudentsDialog.visible" title="批量添加学生" width="480px">
      <el-form label-width="120px">
        <el-form-item label="学生学号 / 用户ID">
          <el-input
            v-model="addStudentsDialog.idsText"
            type="textarea"
            :rows="5"
            placeholder="20240004, 20240005&#10;20240006"
          />
        </el-form-item>
        <div class="form-hint" style="padding-left: 120px;">可粘贴多个学号，系统将自动去重并跳过已在班学生。</div>
      </el-form>
      <template #footer>
        <el-button @click="addStudentsDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAddStudents">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.cm-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.cm-left {
  flex: 1 1 46%;
  min-width: 0;
}
.cm-right {
  flex: 1 1 54%;
  min-width: 0;
}

/* 班级行点击高亮 */
.class-table :deep(.el-table__row) {
  cursor: pointer;
}
.class-table :deep(.el-table__row.active-row > td.el-table__cell) {
  background-color: #f3e8ff !important;
}

.class-name {
  font-weight: 600;
  color: #333;
}
.class-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
</style>
