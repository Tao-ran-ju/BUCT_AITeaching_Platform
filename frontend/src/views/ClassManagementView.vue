<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import ClassTasksPanel from '../components/class/ClassTasksPanel.vue'
import ClassNoticesPanel from '../components/class/ClassNoticesPanel.vue'
import ClassQaPanel from '../components/class/ClassQaPanel.vue'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 2000
const DEMO = reactive({
  classes: [
    { id: 1, name: '计科 2401 班', course: '算法设计与分析', private: 0, student_count: 3, created_at: '2024-09-01' },
    { id: 2, name: '软件 2402 班', course: '数据结构', private: 0, student_count: 2, created_at: '2024-09-01' },
    { id: 3, name: '计科 2301 班', course: '', private: 0, student_count: 1, created_at: '2023-09-01' }
  ],
  students: {
    1: [
      { id: 101, uid: '20240001', name: '张伟', registered: true, college: '计算机科学与技术', major: '计算机科学与技术' },
      { id: 102, uid: '20240002', name: '李娜', registered: true, college: '计算机科学与技术', major: '计算机科学与技术' },
      { id: 103, uid: '20240003', name: '王强', registered: false, college: '', major: '' }
    ],
    2: [
      { id: 201, uid: '20240010', name: '赵敏', registered: true, college: '软件工程', major: '软件工程' },
      { id: 202, uid: '20240011', name: '刘洋', registered: true, college: '软件工程', major: '软件工程' }
    ],
    3: [
      { id: 301, uid: '20230001', name: '陈晨', registered: false, college: '', major: '' }
    ]
  }
})

const state = reactive({ classId: null, activeTab: 'students' })

const currentStudents = computed(() => (state.classId && DEMO.students[state.classId]) || [])

function className(id) {
  const c = DEMO.classes.find((x) => x.id === id)
  return c ? c.name : ''
}

function syncDemoCount(classId) {
  const c = DEMO.classes.find((x) => x.id === classId)
  if (c) c.student_count = (DEMO.students[classId] || []).length
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

const classDialog = reactive({ visible: false, mode: 'create', id: null, form: { name: '', private: 0 } })

function openClassModal(id) {
  const editing = id ? DEMO.classes.find((c) => c.id === id) : null
  classDialog.mode = editing ? 'edit' : 'create'
  classDialog.id = id || null
  classDialog.form = {
    name: editing ? editing.name : '',
    private: editing ? editing.private : 0
  }
  classDialog.visible = true
}

function submitClass() {
  const name = classDialog.form.name.trim()
  if (!name) {
    ElMessage.error('班级名称不能为空')
    return
  }
  const payload = { name, private: classDialog.form.private }
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
      DEMO.classes.push(Object.assign({ id: ++demoId, course: '', student_count: 0, created_at: '' }, payload))
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
  DEMO.students[classId] = Array.isArray(data) ? data : []
  syncDemoCount(classId)
}

function refreshStudents() {
  if (!state.classId) {
    ElMessage.error('请先选择班级')
    return
  }
  loadStudents(state.classId).then(() => {
    ElMessage.success('已刷新后端注册记录查询')
  })
}

// 手动添加单个学生
const addStudentDialog = reactive({ visible: false, form: { uid: '', name: '' } })

function openAddStudentModal() {
  if (!state.classId) {
    ElMessage.error('请先选择班级')
    return
  }
  addStudentDialog.form = { uid: '', name: '' }
  addStudentDialog.visible = true
}

function submitAddStudent() {
  if (!state.classId) return
  const uid = Number(String(addStudentDialog.form.uid).trim())
  if (!Number.isFinite(uid) || uid <= 0) {
    ElMessage.error('请输入有效的学号')
    return
  }
  const name = addStudentDialog.form.name.trim() || null
  api.request(api.addClassStudents(state.classId, [{ uid, name }])).then((res) => {
    const added = (res && res.added) || []
    ElMessage.success('成功添加 ' + added.length + ' 名学生')
    loadStudents(state.classId)
  }).catch(() => {
    const existing = DEMO.students[state.classId] || []
    if (!existing.some((s) => String(s.uid) === String(uid))) {
      existing.push({ id: null, uid: String(uid), name: name || String(uid), registered: false, college: '', major: '' })
    }
    DEMO.students[state.classId] = existing
    syncDemoCount(state.classId)
    ElMessage.success('演示模式：已本地添加该学生')
  })
  addStudentDialog.visible = false
}

// 批量导入
const importDialog = reactive({ visible: false })
const importFile = ref(null)

function openImportModal() {
  if (!state.classId) {
    ElMessage.error('请先选择班级')
    return
  }
  importFile.value = null
  importDialog.visible = true
}

function onImportFileChange(e) {
  importFile.value = e.target.files && e.target.files[0]
  e.target.value = '' // 允许再次选择同一文件
}

async function downloadTemplate() {
  try {
    const blob = await api.downloadImportTemplate()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '学生导入模板.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    ElMessage.success('模板已开始下载')
  } catch (e) {
    ElMessage.error('下载模板失败：请确认后端已连接')
  }
}

async function submitImport() {
  if (!importFile.value) {
    ElMessage.error('请选择要上传的 Excel 文件')
    return
  }
  const fd = new FormData()
  fd.append('file', importFile.value)
  api.request(api.importClassStudents(state.classId, fd)).then((res) => {
    const added = (res && res.added) || 0
    const matched = (res && res.matched) || 0
    const notFound = (res && res.not_found) || 0
    ElMessage.success(`导入完成：新增 ${added} 人（已注册 ${matched}，未注册 ${notFound}）`)
    importDialog.visible = false
    loadStudents(state.classId)
  }).catch((e) => {
    ElMessage.error('批量导入失败：' + ((e && e.message) || '请确认文件为 .xlsx 且后端已连接'))
  })
}

async function removeStudent(row) {
  if (!state.classId) return
  const uid = Number(row.uid)
  try {
    await ElMessageBox.confirm('确定从班级移除该学生？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.removeClassStudent(state.classId, uid)
    ElMessage.success('已移除该学生')
  } catch (e) {
    DEMO.students[state.classId] = (DEMO.students[state.classId] || []).filter((s) => String(s.uid) !== String(uid))
    syncDemoCount(state.classId)
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
      <p>建班、维护班级信息；管理学生名单（含注册状态、Excel 批量导入），并在此布置任务、发布通知、回答学生提问。</p>
    </div>

    <!-- 班级列表 -->
    <section class="panel">
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
          <el-table-column label="班级" min-width="200">
            <template #default="{ row }"><span class="class-name">{{ row.name }}</span></template>
          </el-table-column>
          <el-table-column label="关联课程" min-width="180">
            <template #default="{ row }">{{ row.course || '-' }}</template>
          </el-table-column>
          <el-table-column label="学生数" width="90">
            <template #default="{ row }">{{ row.student_count != null ? row.student_count : '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140">
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

    <!-- 选中班级后的功能标签 -->
    <div v-if="state.classId">
      <el-tabs v-model="state.activeTab">
        <!-- 学生 -->
        <el-tab-pane label="学生" name="students">
          <div class="student-toolbar">
            <el-button size="small" type="primary" @click="openAddStudentModal">+ 手动添加</el-button>
            <el-button size="small" @click="openImportModal">批量导入</el-button>
            <el-button size="small" @click="refreshStudents">刷新后端记录查询</el-button>
            <span class="muted">当前班级：{{ className(state.classId) }}</span>
          </div>

          <div v-if="!currentStudents.length" class="empty-tip">暂无学生，点击上方「手动添加」或「批量导入」</div>
          <el-table v-else :data="currentStudents" size="small">
            <el-table-column label="学号" min-width="120">
              <template #default="{ row }">{{ row.uid || row.username || '-' }}</template>
            </el-table-column>
            <el-table-column label="姓名" min-width="100">
              <template #default="{ row }">{{ row.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="注册状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.registered ? 'success' : 'info'" size="small">
                  {{ row.registered ? '已注册' : '未注册' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="院系 / 专业" min-width="160">
              <template #default="{ row }">{{ row.college || row.department || row.major || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="removeStudent(row)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 任务 -->
        <el-tab-pane label="任务" name="tasks" lazy>
          <ClassTasksPanel :class-id="state.classId" />
        </el-tab-pane>

        <!-- 通知 -->
        <el-tab-pane label="通知" name="notices" lazy>
          <ClassNoticesPanel :class-id="state.classId" :classes="DEMO.classes" />
        </el-tab-pane>

        <!-- 学生提问 -->
        <el-tab-pane label="学生提问" name="qa" lazy>
          <ClassQaPanel />
        </el-tab-pane>
      </el-tabs>
    </div>
    <div v-else class="empty-tip">请先选择班级</div>

    <!-- 班级对话框 -->
    <el-dialog v-model="classDialog.visible" :title="classDialog.mode === 'create' ? '新建班级' : '编辑班级'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="班级名称" required>
          <el-input v-model="classDialog.form.name" placeholder="如：计科 2401 班" />
        </el-form-item>
        <el-form-item label="可见性">
          <el-select v-model="classDialog.form.private" style="width: 100%">
            <el-option :value="0" label="公开" />
            <el-option :value="1" label="私有" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitClass">确定</el-button>
      </template>
    </el-dialog>

    <!-- 手动添加学生对话框 -->
    <el-dialog v-model="addStudentDialog.visible" title="手动添加学生" width="460px">
      <el-form label-width="80px">
        <el-form-item label="学号" required>
          <el-input v-model="addStudentDialog.form.uid" placeholder="如：20240004" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="addStudentDialog.form.name" placeholder="选填，未注册时可留空" />
        </el-form-item>
      </el-form>
      <div class="form-hint">添加后系统会按学号到数据库查找该学生是否已注册学生端，未注册将标记为「未注册」。</div>
      <template #footer>
        <el-button @click="addStudentDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAddStudent">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入学生对话框 -->
    <el-dialog v-model="importDialog.visible" title="批量导入学生" width="480px">
      <div class="import-tip">
        <p>请先下载 Excel 模板，按「学号 / 姓名」两列填写后上传。后端将按学号到数据库查找学生，未找到的会标记为「未注册」。</p>
        <el-button size="small" @click="downloadTemplate">下载 Excel 模板</el-button>
      </div>
      <el-form label-width="80px" style="margin-top: 14px;">
        <el-form-item label="选择文件">
          <input type="file" accept=".xlsx,.xls" class="file-input" @change="onImportFileChange">
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitImport">上传导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
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

.student-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.import-tip {
  font-size: 13px;
  color: #666;
  line-height: 1.7;
  background: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  padding: 12px 14px;
}
.import-tip p {
  margin: 0 0 10px;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.6;
}

.file-input {
  width: 100%;
}
</style>
