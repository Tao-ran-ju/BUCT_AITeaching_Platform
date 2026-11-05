<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import { tabState } from '../utils/tabState.js'
import DiscussionView from './DiscussionView.vue'
import TeamView from './TeamView.vue'

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

// ---------- 【新增统一解析响应的工具函数！核心修复点】 ----------
/**
 * 解析后端标准响应：{code, message, data}
 * @param raw 接口返回原始值
 * @returns 剥完外层后的真实data
 */
function unwrapResp(raw) {
  // 后端标准格式：{code:0, data: xxx}
  if (raw && typeof raw === 'object' && 'code' in raw) {
    return raw.data
  }
  // 如果已经是数组/分页对象（{items,total}）直接返回
  return raw
}

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

// ---------- 课程【修改loadCourses，使用unwrapResp】 ----------
async function loadCourses() {
  const raw = await api.request(
    api.listCourses({ page: 1, page_size: 100 }),
    { items: DEMO.courses, total: DEMO.courses.length }
  )
  const data = unwrapResp(raw)
  // 后端分页格式 {items:[],total}
  if (data && data.items && Array.isArray(data.items)) {
    DEMO.courses = data.items
  } else if (Array.isArray(data)) {
    DEMO.courses = data
  }
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
    api.request(api.createCourse(payload)).then((res) => {
      ElMessage.success('课程创建成功')
      loadCourses()
    }).catch(() => {
      DEMO.courses.push({ id: ++demoId, ...payload, status: 'published' })
      ElMessage.success('演示模式：课程已本地创建')
    })
  } else {
    const id = courseDialog.id
    const coverFile = courseCoverFile.value
    api.request(api.updateCourse(id, payload)).then((res) => {
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
    await ElMessageBox.confirm('确定归档该课程？归档后课程不再展示，后续可以恢复。', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await api.deleteCourse(id)
    ElMessage.success('课程已归档')
  } catch (e) {
    console.error("归档课程异常：", e)
    ElMessage.error("归档失败：" + (e?.message || "后端请求异常"))
    return
  }
  if (state.courseId === id) {
    state.courseId = null
    state.chapterId = null
    state.resources = []
  }
  loadCourses()
}


// ---------- 章节【修改loadChapters】 ----------
async function loadChapters(courseId) {
  const raw = await api.request(api.listChapters(courseId), DEMO.chapters[courseId] || [])
  const data = unwrapResp(raw)
  DEMO.chapters[courseId] = Array.isArray(data) ? data : []
  if (DEMO.chapters[courseId].length && !state.chapterId) {
    state.chapterId = DEMO.chapters[courseId][0].id
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

// ---------- 知识点【修改loadKps】 ----------
async function loadKps(chapterId) {
  const raw = await api.request(api.listKnowledgePoints(chapterId), DEMO.kps[chapterId] || [])
  const data = unwrapResp(raw)
  DEMO.kps[chapterId] = Array.isArray(data) ? data : []
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

// ---------- 资源【修改loadResources】 ----------
const resCourse = ref('')
const resTitle = ref('')
const resFile = ref(null)

async function loadResources(courseId) {
  const raw = await api.request(
    api.listResources(courseId ? { course_id: courseId, page: 1, page_size: 100 } : { page: 1, page_size: 100 }),
    null
  )
  const data = unwrapResp(raw)
  if (data && data.items && Array.isArray(data.items)) {
    state.resources = data.items
  } else if (Array.isArray(data)) {
    state.resources = data
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
    const raw = await api.getResourcePreview(id)
    const data = unwrapResp(raw)
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

