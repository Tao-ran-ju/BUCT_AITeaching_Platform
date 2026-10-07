/**
 * api/index.js —— 统一后端请求封装（混合模式：真实 API + 演示回退）
 *
 * 约定：后端统一响应 { code, message, data }；code === 0 视为成功。
 *
 * 说明：
 *  - 线上同源部署（nginx 反代 /api）、本地 dev server（vite proxy /api）时默认走
 *    相对路径 /api/v1；直接以 file:// 打开构建产物时回退本机 FastAPI。
 *  - 登录 token 存于 localStorage（key: buct_access_token），请求时自动注入。
 *  - 所有方法都返回 Promise<data>；请求失败（未登录 / 后端未启动 / 网络错误）
 *    时，调用方可使用 api.request(promise, fallback) 优雅回退到演示数据。
 *  - 可用 localStorage 覆盖：
 *      apiBaseUrl       —— 后端前缀地址
 *      buct_access_token —— 登录令牌（手动登录后写入）
 */
import axios from 'axios'

const DEFAULT_BASE_URL =
  location.protocol === 'http:' || location.protocol === 'https:'
    ? '/api/v1'
    : 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'buct_access_token'

const BASE_URL = localStorage.getItem('apiBaseUrl') || DEFAULT_BASE_URL

// 浏览器可能以 file:// 方式直接打开页面，此时无法注入 token，全部回退演示数据
const http = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// ---------- 请求拦截：注入 token ----------
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = 'Bearer ' + token
  }
  return config
})

// ---------- 错误类型 ----------
export class ApiError extends Error {
  constructor(code, message) {
    super(message || '请求失败')
    this.name = 'ApiError'
    this.code = code
  }
}

// ---------- 响应拦截：统一解包 ----------
http.interceptors.response.use(
  (resp) => {
    const body = resp.data
    if (body && typeof body === 'object' && Object.prototype.hasOwnProperty.call(body, 'code')) {
      if (body.code === 0) {
        return body.data
      }
      return Promise.reject(new ApiError(body.code, body.message))
    }
    return body
  },
  (err) => {
    const resp = err.response
    if (resp && resp.data) {
      const d = resp.data
      return Promise.reject(new ApiError(resp.status, (d && d.message) || err.message))
    }
    return Promise.reject(new ApiError(0, err.message || '网络错误'))
  }
)

// ---------- 兜底请求：失败时返回 fallback ----------
function request(promise, fallback) {
  return Promise.resolve(promise).catch(() => {
    if (fallback !== undefined) {
      return fallback
    }
    return Promise.reject(new ApiError(0, '请求失败'))
  })
}

// ---------- 接口清单 ----------
export const api = {
  http,
  ApiError,
  request,
  BASE_URL,

  // 认证
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),

  // 用户
  getMe: () => http.get('/users/me'),
  updateMe: (data) => http.put('/users/me', data),
  uploadAvatar: (formData) => http.post('/users/me/avatar', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  changePassword: (data) => http.post('/users/me/password', data),
  listUsers: (params) => http.get('/users', { params }),

  // 课程
  listCourses: (params) => http.get('/courses', { params }),
  getCourse: (id) => http.get('/courses/' + id),
  createCourse: (data) => http.post('/courses', data),
  updateCourse: (id, data) => http.put('/courses/' + id, data),
  deleteCourse: (id) => http.delete('/courses/' + id),
  cloneCourse: (id) => http.post('/courses/' + id + '/clone'),
  archiveCourse: (id) => http.post('/courses/' + id + '/archive'),
  publishCourse: (id) => http.post('/courses/' + id + '/publish'),
  uploadCourseCover: (id, formData) => http.post('/courses/' + id + '/cover', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  listChapters: (courseId) => http.get('/courses/' + courseId + '/chapters'),
  createChapter: (courseId, data) => http.post('/courses/' + courseId + '/chapters', data),
  updateChapter: (chapterId, data) => http.put('/courses/chapters/' + chapterId, data),
  deleteChapter: (chapterId) => http.delete('/courses/chapters/' + chapterId),
  listKnowledgePoints: (chapterId) => http.get('/courses/chapters/' + chapterId + '/knowledge-points'),
  createKnowledgePoint: (chapterId, data) => http.post('/courses/chapters/' + chapterId + '/knowledge-points', data),
  updateKnowledgePoint: (chapterId, kpId, data) => http.put('/courses/chapters/' + chapterId + '/knowledge-points/' + kpId, data),
  deleteKnowledgePoint: (chapterId, kpId) => http.delete('/courses/chapters/' + chapterId + '/knowledge-points/' + kpId),

  // 班级
  listClasses: (params) => http.get('/classes', { params }),
  createClass: (data) => http.post('/classes', data),
  updateClass: (id, data) => http.put('/classes/' + id, data),
  deleteClass: (id) => http.delete('/classes/' + id),
  listClassStudents: (id) => http.get('/classes/' + id + '/students'),
  addClassStudents: (id, studentIds) => http.post('/classes/' + id + '/students', { student_ids: studentIds }),
  removeClassStudent: (id, studentId) => http.delete('/classes/' + id + '/students/' + studentId),

  // 教学资源
  uploadResource: (formData) => http.post('/resources', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  listResources: (params) => http.get('/resources', { params }),
  setResourceVisibility: (id, visibility) => http.patch('/resources/' + id + '/visibility', { visibility }),
  deleteResource: (id) => http.delete('/resources/' + id),
  getResourceFile: (id, kind) => http.get('/resources/' + id + '/file', { params: { kind } }),
  getResourcePreview: (id) => http.get('/resources/' + id + '/preview'),

  // 作业
  listAssignments: (courseId) => http.get('/assignments', { params: { course_id: courseId } }),
  createAssignment: (data) => http.post('/assignments', data),
  listSubmissions: (id) => http.get('/assignments/' + id + '/submissions'),
  judgeAssignment: (id) => http.post('/assignments/' + id + '/judge'),
  checkPlagiarism: (id) => http.post('/assignments/' + id + '/plagiarism'),

  // 消息通知（教师端发布通知 / 作业，与学生端消息系统对接）
  listSentMessages: () => http.get('/messages/sent'),
  sendMessage: (formData) => http.post('/messages', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),

  // AI 问答助手（学生提问 -> 自动分流 -> 教师人工回复）
  askQuestion: (data) => http.post('/qa/ask', data),
  listQaQuestions: () => http.get('/qa/questions'),
  answerQuestion: (id, data) => http.post('/qa/' + id + '/answer', data),

  // AI 备课中心
  generatePlan: (data) => http.post('/teaching/plan', data),
  generateOutline: (data) => http.post('/teaching/outline', data),
  generatePpt: (data) => http.post('/teaching/ppt', data),
  generateQuiz: (data) => http.post('/teaching/quiz', data),
  generateExamPaper: (data) => http.post('/teaching/exam-paper', data),
  reviewQuestion: (question) => http.post('/teaching/question-review', { question }),
  designProject: (data) => http.post('/teaching/project', data),
  generateReport: (data) => http.post('/teaching/report', data),
  summarizeResource: (content) => http.post('/teaching/summarize', { content }),

  // 主题讨论区
  listPosts: (courseId) => http.get('/discussions', { params: { course_id: courseId } }),
  createPost: (data) => http.post('/discussions', data),
  setPostFlags: (postId, data) => http.patch('/discussions/' + postId, data),
  deletePost: (postId) => http.delete('/discussions/' + postId),
  listReplies: (postId) => http.get('/discussions/' + postId + '/replies'),
  createReply: (postId, data) => http.post('/discussions/' + postId + '/replies', data),

  // 学习小组
  listTeams: (params) => http.get('/teams', { params }),
  createTeam: (data) => http.post('/teams', data),
  updateTeam: (id, data) => http.put('/teams/' + id, data),
  deleteTeam: (id) => http.delete('/teams/' + id),
  addTeamMembers: (id, studentIds) => http.post('/teams/' + id + '/members', { student_ids: studentIds }),
  removeTeamMember: (id, studentId) => http.delete('/teams/' + id + '/members/' + studentId),

  // 学习任务
  listTasks: (params) => http.get('/tasks', { params }),
  createTask: (data) => http.post('/tasks', data),
  updateTask: (id, data) => http.put('/tasks/' + id, data),
  deleteTask: (id) => http.delete('/tasks/' + id),
  completeTask: (id) => http.post('/tasks/' + id + '/complete'),

  // 学情预警
  scanWarnings: () => http.post('/warnings/scan'),
  listWarnings: (params) => http.get('/warnings', { params }),
  aiSuggestion: (id) => http.post('/warnings/' + id + '/suggestion'),
  resolveWarning: (id, intervention) => http.post('/warnings/' + id + '/resolve', { intervention }),

  // 数据驾驶舱
  dashboardOverview: () => http.get('/dashboard/overview'),
  dashboardHeatmap: (courseId) => http.get('/dashboard/heatmap', { params: courseId ? { course_id: courseId } : {} }),
  taskProgress: () => http.get('/dashboard/task-progress'),
  scoreDistribution: () => http.get('/dashboard/score-distribution'),
  effectCompare: () => http.get('/dashboard/effect-compare')
}

export default api
