<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 1000
const DEMO = reactive({
  courses: [
    { id: 1, name: '算法设计与分析', code: 'CS301', status: 'published', description: '面向算法竞赛的核心课程，覆盖分治、动态规划、图论等' },
    { id: 2, name: '数据结构', code: 'CS201', status: 'published', description: '线性表、树、图等基础数据结构' },
    { id: 3, name: '程序设计基础', code: 'CS101', status: 'draft', description: 'C 语言入门与程序设计' }
  ],
  chapters: {
    1: [
      { id: 1, title: '第一章 绪论', sort_order: 1, description: '算法与复杂度' },
      { id: 2, title: '第二章 分治法', sort_order: 2, description: '归并/快排' },
      { id: 3, title: '第三章 动态规划', sort_order: 3, description: '状态转移' }
    ],
    2: [
      { id: 4, title: '第一章 线性表', sort_order: 1, description: '' },
      { id: 5, title: '第二章 树与图', sort_order: 2, description: '' }
    ],
    3: [
      { id: 6, title: '第一章 C 语言基础', sort_order: 1, description: '' }
    ]
  },
  kps: {
    1: [{ id: 1, name: '算法复杂度分析', description: '时间/空间复杂度' }, { id: 2, name: '递归与主定理', description: '' }],
    2: [{ id: 3, name: '归并排序', description: '' }, { id: 4, name: '快速排序', description: '' }],
    3: [{ id: 5, name: '01 背包', description: '' }, { id: 6, name: '最长公共子序列', description: '' }],
    4: [{ id: 7, name: '顺序表', description: '' }, { id: 8, name: '链表', description: '' }],
    5: [{ id: 9, name: '二叉树遍历', description: '' }],
    6: [{ id: 10, name: '变量与数据类型', description: '' }]
  },
  resources: [
    { id: 1, title: '算法导论课件.pdf', resource_type: 'document', file_size: 2048000, visibility: 'course', course_id: 1, summary: '介绍算法复杂度分析、分治与动态规划等核心思想', keywords: '算法复杂度，分治，动态规划', created_at: '2024-09-01' },
    { id: 2, title: '动态规划讲解视频.mp4', resource_type: 'video', file_size: 52428800, visibility: 'course', course_id: 1, created_at: '2024-09-05' },
    { id: 3, title: '链表实现示例代码.zip', resource_type: 'code', file_size: 102400, visibility: 'private', course_id: 2, summary: '单链表与双链表的插入、删除、遍历实现', keywords: '链表，指针', created_at: '2024-09-10' },
    { id: 4, title: 'C 语言语法速查表.png', resource_type: 'image', file_size: 512000, visibility: 'public', course_id: 3, created_at: '2024-08-20' }
  ]
})

const state = reactive({ courseId: null, chapterId: null, resources: [] })

const TYPE_LABEL = { document: '文档', video: '视频', audio: '音频', image: '图片', code: '代码', other: '其他' }
const VIS_LABEL = { public: '公开', course: '课程内', private: '私有' }
const VIS_OPTIONS = [
  { value: 'public', label: '公开' },
  { value: 'course', label: '课程内' },
  { value: 'private', label: '私有' }
]

// ---------- 工具函数 ----------
function formatSize(bytes) {
  if (bytes === null || bytes === undefined) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function formatDuration(sec) {
  if (sec === null || sec === undefined || isNaN(sec)) return ''
  sec = Math.round(sec)
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return h > 0 ? `${h}:${p(m)}:${p(s)}` : `${m}:${p(s)}`
}

function truncate(s, n) {
  s = s || ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

function typeOfFilename(name) {
  const ext = (name || '').split('.').pop().toLowerCase()
  if (['mp4', 'avi', 'mov', 'mkv'].includes(ext)) return 'video'
  if (['mp3', 'wav', 'flac'].includes(ext)) return 'audio'
  if (['png', 'jpg', 'jpeg', 'gif', 'bmp'].includes(ext)) return 'image'
  if (['c', 'cpp', 'java', 'py', 'js', 'zip', 'tar', 'rar'].includes(ext)) return 'code'
  if (['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'md'].includes(ext)) return 'document'
  return 'other'
}

function fullUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  const origin = api.BASE_URL ? api.BASE_URL.replace(/\/api\/v1\/?$/, '') : ''
  const clean = path.charAt(0) === '/' ? path : '/' + path
  return origin ? origin + clean : clean
}

function resourceFileUrl(r, kind) {
  let base = api.BASE_URL || '/api/v1'
  base = base.replace(/\/+$/, '')
  let url = base + '/resources/' + r.id + '/file?kind=' + encodeURIComponent(kind || 'original')
  const token = localStorage.getItem('buct_access_token')
  if (token) url += '&token=' + encodeURIComponent(token)
  return url
}

function canPreview(r) {
  return ['document', 'video', 'audio', 'image'].includes(r.resource_type)
}

function courseStatusLabel(status) {
  if (status === 'draft') return '草稿'
  if (status === 'archived') return '已归档'
  return '已发布'
}

function toLocalInput(v) {
  return v ? String(v).slice(0, 16) : ''
}

// ---------- 计算属性 ----------
const currentChapters = computed(() => (state.courseId && DEMO.chapters[state.courseId]) || [])
const currentKps = computed(() => (state.chapterId && DEMO.kps[state.chapterId]) || [])
const chapterCourseHint = computed(() => courseName(state.courseId))
const kpChapterHint = computed(() => chapterTitle(state.chapterId))
const resHint = computed(() => (state.courseId ? `（${courseName(state.courseId)}）` : '（全部）'))

function courseName(id) {
  return (DEMO.courses.find((c) => c.id === id) || {}).name || ''
}

function chapterTitle(id) {
  return (currentChapters.value.find((c) => c.id === id) || {}).title || ''
}

// ---------- 课程 ----------
async function loadCourses() {
  const data = await api.request(
    api.listCourses({ page: 1, page_size: 100 }),
    { items: DEMO.courses, total: DEMO.courses.length }
  )
  DEMO.courses = (data && data.items) || []
  if (!state.courseId && DEMO.courses.length) {
    selectCourse(DEMO.courses[0].id)
  }
}

function selectCourse(id) {
  state.courseId = id
  state.chapterId = null
  loadChapters(id)
  loadResources(id)
}

// 课程对话框
const courseDialog = reactive({ visible: false, mode: 'create', id: null, form: { name: '', code: '', description: '', open_time: '' } })
const courseCoverFile = ref(null)

function openCourseModal() {
  courseDialog.mode = 'create'
  courseDialog.id = null
  courseDialog.form = { name: '', code: '', description: '', open_time: '' }
  courseCoverFile.value = null
  courseDialog.visible = true
}

function openEditCourseModal(id) {
  const c = DEMO.courses.find((x) => x.id === id)
  if (!c) return
  courseDialog.mode = 'edit'
  courseDialog.id = id
  courseDialog.form = { name: c.name || '', code: c.code || '', description: c.description || '', open_time: toLocalInput(c.open_time) }
  courseCoverFile.value = null
  courseDialog.visible = true
}

function onCourseCoverChange(e) {
  courseCoverFile.value = e.target.files && e.target.files[0]
}

async function submitCourse() {
  const name = courseDialog.form.name.trim()
  if (!name) {
    ElMessage.error('课程名称不能为空')
    return
  }
  const payload = {
    name,
    code: courseDialog.form.code.trim(),
    description: courseDialog.form.description.trim(),
    open_time: courseDialog.form.open_time ? courseDialog.form.open_time + ':00' : null
  }
  if (courseDialog.mode === 'create') {
    api.request(api.createCourse(payload)).then(() => {
      ElMessage.success('课程创建成功')
      loadCourses()
    }).catch(() => {
      DEMO.courses.push({ id: ++demoId, ...payload, status: 'published' })
      ElMessage.success('演示模式：课程已本地创建')
    })
  } else {
    const id = courseDialog.id
    const coverFile = courseCoverFile.value
    api.request(api.updateCourse(id, payload)).then(() => {
      if (coverFile) {
        const fd = new FormData()
        fd.append('file', coverFile)
        api.request(api.uploadCourseCover(id, fd)).then(() => {
          ElMessage.success('课程与封面已更新')
          loadCourses()
        }).catch(() => {
          ElMessage.success('课程已更新')
          loadCourses()
        })
      } else {
        ElMessage.success('课程已更新')
        loadCourses()
      }
    }).catch(() => {
      const c = DEMO.courses.find((x) => x.id === id)
      if (c) Object.assign(c, payload)
      ElMessage.success('演示模式：课程已本地更新')
    })
  }
  courseDialog.visible = false
}

function cloneCourse(id) {
  api.request(api.cloneCourse(id)).then(() => {
    ElMessage.success('课程已克隆为草稿')
    loadCourses()
  }).catch(() => {
    const src = DEMO.courses.find((c) => c.id === id)
    if (!src) return
    DEMO.courses.push({ id: ++demoId, name: src.name + '（副本）', code: src.code, description: src.description, cover: src.cover, status: 'draft' })
    ElMessage.success('演示模式：课程已本地克隆')
  })
}

async function archiveCourse(id) {
  try {
    await ElMessageBox.confirm('确定归档该课程？归档后学生端不可见，可随时重新发布。', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.archiveCourse(id)).then(() => {
    ElMessage.success('课程已归档')
    loadCourses()
  }).catch(() => {
    DEMO.courses.forEach((c) => { if (c.id === id) c.status = 'archived' })
    ElMessage.success('演示模式：课程已本地归档')
  })
}

function publishCourse(id) {
  api.request(api.publishCourse(id)).then(() => {
    ElMessage.success('课程已发布')
    loadCourses()
  }).catch(() => {
    DEMO.courses.forEach((c) => { if (c.id === id) c.status = 'published' })
    ElMessage.success('演示模式：课程已本地发布')
  })
}

async function deleteCourse(id) {
  try {
    await ElMessageBox.confirm('确定删除该课程？其下章节、知识点与资源将一并移除。', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.deleteCourse(id)
    ElMessage.success('课程已删除')
  } catch (e) {
    DEMO.courses = DEMO.courses.filter((c) => c.id !== id)
    ElMessage.success('演示模式：课程已本地删除')
  }
  if (state.courseId === id) {
    state.courseId = null
    state.chapterId = null
    state.resources = []
  }
  loadCourses()
}

// ---------- 章节 ----------
async function loadChapters(courseId) {
  const data = await api.request(api.listChapters(courseId), DEMO.chapters[courseId] || [])
  DEMO.chapters[courseId] = data
  if (data.length && !state.chapterId) {
    state.chapterId = data[0].id
  }
  if (state.chapterId) {
    loadKps(state.chapterId)
  }
}

const chapterDialog = reactive({ visible: false, mode: 'create', id: null, form: { title: '', description: '' } })

function openChapterModal() {
  if (!state.courseId) {
    ElMessage.error('请先选择课程')
    return
  }
  chapterDialog.mode = 'create'
  chapterDialog.id = null
  chapterDialog.form = { title: '', description: '' }
  chapterDialog.visible = true
}

function openEditChapterModal(id) {
  const ch = currentChapters.value.find((x) => x.id === id)
  if (!ch) return
  chapterDialog.mode = 'edit'
  chapterDialog.id = id
  chapterDialog.form = { title: ch.title || '', description: ch.description || '' }
  chapterDialog.visible = true
}

function submitChapter() {
  const title = chapterDialog.form.title.trim()
  if (!title) {
    ElMessage.error('章节标题不能为空')
    return
  }
  const payload = { title, description: chapterDialog.form.description.trim() }
  if (chapterDialog.mode === 'create') {
    api.request(api.createChapter(state.courseId, { ...payload, sort_order: 0 })).then(() => {
      ElMessage.success('章节创建成功')
      loadChapters(state.courseId)
    }).catch(() => {
      if (!DEMO.chapters[state.courseId]) DEMO.chapters[state.courseId] = []
      DEMO.chapters[state.courseId].push({ id: ++demoId, ...payload, sort_order: 0 })
      ElMessage.success('演示模式：章节已本地创建')
    })
  } else {
    const id = chapterDialog.id
    api.request(api.updateChapter(id, payload)).then(() => {
      ElMessage.success('章节已更新')
      loadChapters(state.courseId)
    }).catch(() => {
      const ch = currentChapters.value.find((x) => x.id === id)
      if (ch) Object.assign(ch, payload)
      ElMessage.success('演示模式：章节已本地更新')
    })
  }
  chapterDialog.visible = false
}

async function deleteChapter(id) {
  try {
    await ElMessageBox.confirm('确定删除该章节？其下知识点将一并删除。', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.deleteChapter(id)).then(() => {
    ElMessage.success('章节已删除')
    if (state.chapterId === id) state.chapterId = null
    loadChapters(state.courseId)
  }).catch(() => {
    if (state.courseId) {
      DEMO.chapters[state.courseId] = (DEMO.chapters[state.courseId] || []).filter((x) => x.id !== id)
    }
    if (state.chapterId === id) state.chapterId = null
    ElMessage.success('演示模式：章节已本地删除')
  })
}

// ---------- 知识点 ----------
async function loadKps(chapterId) {
  const data = await api.request(api.listKnowledgePoints(chapterId), DEMO.kps[chapterId] || [])
  DEMO.kps[chapterId] = data
}

const kpDialog = reactive({ visible: false, mode: 'create', id: null, form: { name: '', description: '' } })

function openKpModal() {
  if (!state.chapterId) {
    ElMessage.error('请先选择章节')
    return
  }
  kpDialog.mode = 'create'
  kpDialog.id = null
  kpDialog.form = { name: '', description: '' }
  kpDialog.visible = true
}

function openEditKpModal(id) {
  const kp = currentKps.value.find((x) => x.id === id)
  if (!kp) return
  kpDialog.mode = 'edit'
  kpDialog.id = id
  kpDialog.form = { name: kp.name || '', description: kp.description || '' }
  kpDialog.visible = true
}

function submitKp() {
  const name = kpDialog.form.name.trim()
  if (!name) {
    ElMessage.error('知识点名称不能为空')
    return
  }
  const payload = { name, description: kpDialog.form.description.trim() }
  if (kpDialog.mode === 'create') {
    api.request(api.createKnowledgePoint(state.chapterId, { ...payload, sort_order: 0 })).then(() => {
      ElMessage.success('知识点创建成功')
      loadKps(state.chapterId)
    }).catch(() => {
      if (!DEMO.kps[state.chapterId]) DEMO.kps[state.chapterId] = []
      DEMO.kps[state.chapterId].push({ id: ++demoId, ...payload })
      ElMessage.success('演示模式：知识点已本地创建')
    })
  } else {
    const id = kpDialog.id
    api.request(api.updateKnowledgePoint(state.chapterId, id, payload)).then(() => {
      ElMessage.success('知识点已更新')
      loadKps(state.chapterId)
    }).catch(() => {
      const kp = currentKps.value.find((x) => x.id === id)
      if (kp) Object.assign(kp, payload)
      ElMessage.success('演示模式：知识点已本地更新')
    })
  }
  kpDialog.visible = false
}

async function deleteKp(id) {
  try {
    await ElMessageBox.confirm('确定删除该知识点？其子知识点将一并删除。', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.deleteKnowledgePoint(state.chapterId, id)).then(() => {
    ElMessage.success('知识点已删除')
    loadKps(state.chapterId)
  }).catch(() => {
    if (state.chapterId) {
      DEMO.kps[state.chapterId] = (DEMO.kps[state.chapterId] || []).filter((x) => x.id !== id)
    }
    ElMessage.success('演示模式：知识点已本地删除')
  })
}

// ---------- 资源 ----------
const resCourse = ref('')
const resTitle = ref('')
const resFile = ref(null)

async function loadResources(courseId) {
  const data = await api.request(
    api.listResources(courseId ? { course_id: courseId, page: 1, page_size: 100 } : { page: 1, page_size: 100 }),
    null
  )
  if (data && data.items) {
    state.resources = data.items
  } else {
    state.resources = DEMO.resources.filter((r) => (courseId ? r.course_id === courseId : true))
  }
}

function syncDemoResources() {
  state.resources = DEMO.resources.filter((r) => (state.courseId ? r.course_id === state.courseId : true))
}

function onResFileChange(e) {
  resFile.value = e.target.files && e.target.files[0]
}

async function handleUpload() {
  const title = resTitle.value.trim()
  const file = resFile.value
  const courseId = resCourse.value ? Number(resCourse.value) : null
  if (!file) {
    ElMessage.error('请选择要上传的文件')
    return
  }
  const formData = new FormData()
  formData.append('title', title || file.name)
  formData.append('file', file)
  if (courseId) formData.append('course_id', String(courseId))

  api.request(api.uploadResource(formData)).then(() => {
    ElMessage.success('资源上传成功')
    loadResources(state.courseId)
  }).catch(() => {
    DEMO.resources.unshift({
      id: ++demoId, title: title || file.name,
      resource_type: typeOfFilename(file.name), file_size: file.size,
      visibility: 'course', course_id: courseId
    })
    ElMessage.success('演示模式：资源已本地添加')
    syncDemoResources()
  })
  resTitle.value = ''
  resFile.value = null
  resCourse.value = state.courseId ? String(state.courseId) : ''
}

async function setVisibility(id, visibility) {
  try {
    await api.setResourceVisibility(id, visibility)
    ElMessage.success('可见性已更新')
  } catch (e) {
    DEMO.resources.forEach((r) => { if (r.id === id) r.visibility = visibility })
    ElMessage.success('演示模式：可见性已本地更新')
    syncDemoResources()
  }
}

async function deleteResource(id) {
  try {
    await ElMessageBox.confirm('确定删除该资源？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.deleteResource(id)
    ElMessage.success('资源已删除')
    loadResources(state.courseId)
  } catch (e) {
    DEMO.resources = DEMO.resources.filter((r) => r.id !== id)
    ElMessage.success('演示模式：资源已本地删除')
    syncDemoResources()
  }
}

async function previewResource(id) {
  try {
    const data = await api.getResourcePreview(id)
    const url = data && data.url
    if (!url) {
      ElMessage.error('该资源暂不支持预览')
      return
    }
    window.open(fullUrl(url), '_blank')
  } catch (e) {
    ElMessage.error('预览失败：' + ((e && e.message) || '未知错误'))
  }
}

function resourceSizeCell(r) {
  let cell = formatSize(r.file_size)
  if (r.duration !== null && r.duration !== undefined) {
    cell += ' · ' + formatDuration(r.duration)
  }
  return cell
}

onMounted(loadCourses)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>课程与资源管理</h2>
      <p>管理课程生命周期、章-节-知识点三级结构，以及多格式教学资源的上传与权限。</p>
    </div>

    <div class="cr-layout">
      <!-- 左栏：课程结构 -->
      <div class="cr-left">
        <section class="panel">
          <div class="panel-head">
            <h3>课程列表</h3>
            <el-button size="small" type="primary" @click="openCourseModal">+ 新建课程</el-button>
          </div>
          <div class="panel-body">
            <div v-if="!DEMO.courses.length" class="empty-tip">暂无课程，点击右上角「新建课程」开始</div>
            <ul v-else class="course-list">
              <li
                v-for="c in DEMO.courses"
                :key="c.id"
                class="course-item"
                :class="{ active: c.id === state.courseId }"
                @click="selectCourse(c.id)"
              >
                <img v-if="c.cover" class="course-cover" :src="fullUrl(c.cover)" alt="">
                <span v-else class="course-cover placeholder"></span>
                <div class="course-main">
                  <div class="name">{{ c.name }}</div>
                  <div class="meta">编号 {{ c.code || '-' }} · {{ courseStatusLabel(c.status) }}</div>
                </div>
                <div class="actions" @click.stop>
                  <el-button size="small" @click="openEditCourseModal(c.id)">编辑</el-button>
                  <el-button size="small" @click="cloneCourse(c.id)">克隆</el-button>
                  <el-button v-if="c.status !== 'published'" size="small" type="primary" @click="publishCourse(c.id)">发布</el-button>
                  <el-button v-if="c.status !== 'archived'" size="small" @click="archiveCourse(c.id)">归档</el-button>
                  <el-button size="small" type="danger" @click="deleteCourse(c.id)">删除</el-button>
                </div>
              </li>
            </ul>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>章节目录 <span class="muted">{{ chapterCourseHint }}</span></h3>
            <el-button size="small" type="primary" @click="openChapterModal">+ 新建章节</el-button>
          </div>
          <div class="panel-body">
            <div v-if="!currentChapters.length" class="empty-tip">暂无章节</div>
            <ul v-else class="tree-list">
              <li
                v-for="ch in currentChapters"
                :key="ch.id"
                class="tree-item"
                :class="{ active: ch.id === state.chapterId }"
                @click="state.chapterId = ch.id; loadKps(ch.id)"
              >
                <div class="tree-main">
                  {{ ch.title }}
                  <div v-if="ch.description" class="desc">{{ ch.description }}</div>
                </div>
                <div class="tree-actions" @click.stop>
                  <el-button size="small" @click="openEditChapterModal(ch.id)">改</el-button>
                  <el-button size="small" type="danger" @click="deleteChapter(ch.id)">删</el-button>
                </div>
              </li>
            </ul>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>知识点 <span class="muted">{{ kpChapterHint }}</span></h3>
            <el-button size="small" type="primary" @click="openKpModal">+ 新建知识点</el-button>
          </div>
          <div class="panel-body">
            <div v-if="!currentKps.length" class="empty-tip">暂无知识点</div>
            <ul v-else class="tree-list">
              <li v-for="kp in currentKps" :key="kp.id" class="tree-item">
                <div class="tree-main">
                  {{ kp.name }}
                  <div v-if="kp.description" class="desc">{{ kp.description }}</div>
                </div>
                <div class="tree-actions">
                  <el-button size="small" @click="openEditKpModal(kp.id)">改</el-button>
                  <el-button size="small" type="danger" @click="deleteKp(kp.id)">删</el-button>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </div>

      <!-- 右栏：教学资源 -->
      <div class="cr-right">
        <section class="panel">
          <div class="panel-head">
            <h3>上传教学资源</h3>
          </div>
          <div class="panel-body">
            <el-form label-width="80px" label-position="left" @submit.prevent="handleUpload">
              <el-form-item label="资源标题">
                <el-input v-model="resTitle" placeholder="请输入资源标题" />
              </el-form-item>
              <el-form-item label="选择文件">
                <input type="file" class="form-input file-input" @change="onResFileChange">
              </el-form-item>
              <el-form-item label="所属课程">
                <el-select v-model="resCourse" placeholder="（个人库，不归属课程）" clearable style="width: 100%">
                  <el-option v-for="c in DEMO.courses" :key="c.id" :value="String(c.id)" :label="c.name" />
                </el-select>
              </el-form-item>
              <el-button type="primary" native-type="submit">上传资源</el-button>
            </el-form>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>资源列表 <span class="muted">{{ resHint }}</span></h3>
          </div>
          <div class="panel-body">
            <el-table :data="state.resources" size="small">
              <el-table-column label="标题" min-width="200">
                <template #default="{ row }">
                  <template v-if="row.resource_type === 'video'">
                    <img v-if="row.thumbnail_path" class="res-thumb" :src="resourceFileUrl(row, 'thumbnail')" alt="">
                    <a class="res-title" :href="resourceFileUrl(row, row.transcoded_path ? 'transcoded' : 'original')" target="_blank" title="点击播放">{{ row.title }}</a>
                  </template>
                  <template v-else>{{ row.title }}</template>
                </template>
              </el-table-column>
              <el-table-column label="类型" width="70">
                <template #default="{ row }">{{ TYPE_LABEL[row.resource_type] || '其他' }}</template>
              </el-table-column>
              <el-table-column label="大小" width="110">
                <template #default="{ row }">{{ resourceSizeCell(row) }}</template>
              </el-table-column>
              <el-table-column label="可见性" width="120">
                <template #default="{ row }">
                  <el-select :model-value="row.visibility" size="small" @change="(v) => setVisibility(row.id, v)">
                    <el-option v-for="o in VIS_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="摘要 / 标签" min-width="180">
                <template #default="{ row }">
                  <div v-if="row.summary || row.keywords" class="res-annot">
                    <div v-if="row.summary" class="res-summary" :title="row.summary">{{ truncate(row.summary, 40) }}</div>
                    <div v-if="row.keywords" class="res-keywords">{{ row.keywords }}</div>
                  </div>
                  <span v-else class="pending-tip">—</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="140">
                <template #default="{ row }">
                  <div class="row-actions">
                    <el-button v-if="canPreview(row)" size="small" @click="previewResource(row.id)">预览</el-button>
                    <el-button size="small" type="danger" @click="deleteResource(row.id)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </div>
    </div>

    <!-- 课程对话框 -->
    <el-dialog v-model="courseDialog.visible" :title="courseDialog.mode === 'create' ? '新建课程' : '编辑课程'" width="520px">
      <el-form label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="courseDialog.form.name" placeholder="如：算法设计与分析" />
        </el-form-item>
        <el-form-item label="课程编号">
          <el-input v-model="courseDialog.form.code" placeholder="如：CS301" />
        </el-form-item>
        <el-form-item label="课程简介">
          <el-input v-model="courseDialog.form.description" type="textarea" placeholder="选填" />
        </el-form-item>
        <el-form-item v-if="courseDialog.mode === 'edit'" label="开放时间">
          <el-date-picker v-model="courseDialog.form.open_time" type="datetime" value-format="YYYY-MM-DDTHH:mm" placeholder="选择开放时间" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="courseDialog.mode === 'edit'" label="封面图">
          <input type="file" accept="image/*" @change="onCourseCoverChange">
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="courseDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitCourse">确定</el-button>
      </template>
    </el-dialog>

    <!-- 章节对话框 -->
    <el-dialog v-model="chapterDialog.visible" :title="chapterDialog.mode === 'create' ? '新建章节' : '编辑章节'" width="460px">
      <el-form label-width="80px">
        <el-form-item label="章节标题" required>
          <el-input v-model="chapterDialog.form.title" placeholder="如：第一章 绪论" />
        </el-form-item>
        <el-form-item label="章节简介">
          <el-input v-model="chapterDialog.form.description" type="textarea" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chapterDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitChapter">确定</el-button>
      </template>
    </el-dialog>

    <!-- 知识点对话框 -->
    <el-dialog v-model="kpDialog.visible" :title="kpDialog.mode === 'create' ? '新建知识点' : '编辑知识点'" width="460px">
      <el-form label-width="80px">
        <el-form-item label="知识点名称" required>
          <el-input v-model="kpDialog.form.name" placeholder="如：递归与主定理" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="kpDialog.form.description" type="textarea" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kpDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitKp">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.cr-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.cr-left {
  flex: 1 1 42%;
  min-width: 0;
}
.cr-right {
  flex: 1 1 58%;
  min-width: 0;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.course-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.course-item:hover {
  border-color: var(--brand-primary);
  background-color: #fafafa;
}
.course-item.active {
  border-color: var(--brand-primary);
  background-color: #f3e8ff;
}
.course-main {
  flex: 1;
  min-width: 0;
}
.course-item .name {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.course-item .meta {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.course-item .actions {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.course-cover {
  width: 44px;
  height: 44px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid #e5e5e5;
  flex-shrink: 0;
  background: #f4f4f4;
}
.course-cover.placeholder {
  display: inline-block;
  background: linear-gradient(135deg, #f3e8ff, #eadcfb);
}

.tree-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 40px;
}
.tree-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #444;
  transition: all 0.2s;
}
.tree-item:hover {
  border-color: var(--brand-primary);
  background-color: #fafafa;
}
.tree-item.active {
  border-color: var(--brand-primary);
  background-color: #f3e8ff;
  color: var(--brand-primary);
}
.tree-item .desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.tree-main {
  flex: 1;
  min-width: 0;
}
.tree-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.file-input {
  width: 100%;
}
.res-annot {
  max-width: 220px;
}
.res-summary {
  font-size: 12px;
  color: #555;
  line-height: 1.5;
}
.res-keywords {
  font-size: 12px;
  color: #6a0dad;
  margin-top: 2px;
}
.res-thumb {
  width: 56px;
  height: 32px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid #e5e5e5;
  vertical-align: middle;
  margin-right: 8px;
  background: #f4f4f4;
}
.res-title {
  color: #333;
  text-decoration: none;
  vertical-align: middle;
}
.res-title:hover {
  color: #6a0dad;
  text-decoration: underline;
}
</style>
