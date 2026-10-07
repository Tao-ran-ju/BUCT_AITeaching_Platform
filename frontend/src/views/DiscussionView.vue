<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 1000
const DEMO = reactive({
  courses: [
    { id: 1, name: '算法设计与分析' },
    { id: 2, name: '数据结构' }
  ],
  posts: [
    {
      id: 1, course_id: 1, author_id: 1, author_name: '张老师',
      title: '分治法 vs 动态规划，如何给学生讲清楚区别？',
      content: '学生在做「最长公共子序列」时总把分治和 DP 搞混，有没有好的类比或例题建议？',
      is_top: true, is_essence: true, created_at: '2024-09-20 10:00'
    },
    {
      id: 2, course_id: 1, author_id: 2, author_name: '李老师',
      title: '关于归并排序复杂度的疑问',
      content: '归并排序的辅助数组空间复杂度如何向学生解释为 O(n)？',
      is_top: false, is_essence: false, created_at: '2024-09-19 09:30'
    }
  ],
  replies: {
    1: [
      { id: 1, post_id: 1, author_id: 3, author_name: '王老师', content: '可以用「重叠子问题」作为切入点：DP 有重叠子问题，分治没有。', created_at: '2024-09-20 11:00' }
    ]
  }
})

const state = reactive({ courseId: null, expanded: null })

// 发帖表单
const postCourse = ref('')
const postTitle = ref('')
const postContent = ref('')
// 每个帖子的内联回复草稿（按 postId 索引）
const replyDrafts = reactive({})

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}

function courseName(id) {
  const c = DEMO.courses.find((x) => x.id === id)
  return c ? c.name : ''
}

// ---------- 课程 ----------
async function loadCourses() {
  const data = await api.request(
    api.listCourses({ page: 1, page_size: 100 }),
    { items: DEMO.courses, total: DEMO.courses.length }
  )
  DEMO.courses = (data && data.items) || []
  if (DEMO.courses.length) {
    state.courseId = DEMO.courses[0].id
    postCourse.value = String(state.courseId)
    loadPosts()
  }
}

function onCourseChange() {
  state.courseId = Number(postCourse.value)
  state.expanded = null
  loadPosts()
}

// ---------- 帖子 ----------
async function loadPosts() {
  if (!state.courseId) return
  const fallback = DEMO.posts.filter((p) => p.course_id === state.courseId)
  const data = await api.request(api.listPosts(state.courseId), fallback)
  DEMO.posts = Array.isArray(data) ? data : ((data && data.items) || [])
}

const posts = computed(() => {
  return DEMO.posts
    .filter((p) => p.course_id === state.courseId)
    .slice()
    .sort((a, b) => {
      if (!!b.is_top !== !!a.is_top) return b.is_top ? 1 : -1
      return String(b.created_at || '').localeCompare(String(a.created_at || ''))
    })
})

function toggleFlag(id, key) {
  const p = DEMO.posts.find((x) => x.id === id)
  if (!p) return
  const payload = { [key]: !p[key] }
  api.request(api.setPostFlags(id, payload)).then(() => {
    ElMessage.success('已更新')
    loadPosts()
  }).catch(() => {
    p[key] = !p[key]
    ElMessage.success('演示模式：已本地更新')
  })
}

async function deletePost(id) {
  try {
    await ElMessageBox.confirm('确定删除该帖子？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  api.request(api.deletePost(id)).then(() => {
    ElMessage.success('帖子已删除')
    loadPosts()
  }).catch(() => {
    DEMO.posts = DEMO.posts.filter((x) => x.id !== id)
    ElMessage.success('演示模式：帖子已本地删除')
  })
}

// ---------- 回复 ----------
function toggleReplies(id) {
  state.expanded = (state.expanded === id) ? null : id
  if (state.expanded === id) loadReplies(id)
}

function repliesOf(postId) {
  return DEMO.replies[postId] || []
}

async function loadReplies(postId) {
  const fallback = DEMO.replies[postId] || []
  const data = await api.request(api.listReplies(postId), fallback)
  DEMO.replies[postId] = Array.isArray(data) ? data : []
}

function submitReply(postId) {
  const content = (replyDrafts[postId] || '').trim()
  if (!content) { ElMessage.error('回复内容不能为空'); return }
  api.request(api.createReply(postId, { content })).then(() => {
    ElMessage.success('回复成功')
    replyDrafts[postId] = ''
    loadReplies(postId)
  }).catch(() => {
    (DEMO.replies[postId] = DEMO.replies[postId] || []).push({
      id: ++demoId, post_id: postId, author_id: 1, author_name: '我',
      content, created_at: new Date().toISOString()
    })
    ElMessage.success('演示模式：回复已本地添加')
    replyDrafts[postId] = ''
    loadReplies(postId)
  })
}

// ---------- 发帖 ----------
function submitPost() {
  const courseId = Number(postCourse.value)
  const title = postTitle.value.trim()
  const content = postContent.value.trim()
  if (!title) { ElMessage.error('请填写标题'); return }
  if (!content) { ElMessage.error('请填写内容'); return }

  api.request(api.createPost({ course_id: courseId, title, content })).then(() => {
    ElMessage.success('帖子发布成功')
    postTitle.value = ''
    postContent.value = ''
    loadPosts()
  }).catch(() => {
    DEMO.posts.unshift({
      id: ++demoId, course_id: courseId, author_id: 1, author_name: '我',
      title, content, is_top: false, is_essence: false,
      created_at: new Date().toISOString()
    })
    ElMessage.success('演示模式：帖子已本地发布')
    postTitle.value = ''
    postContent.value = ''
  })
}

onMounted(loadCourses)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>主题讨论区</h2>
      <p>围绕课程发起主题讨论，支持置顶与精华帖标记，沉淀高质量问答。</p>
    </div>

    <div class="disc-layout">
      <!-- 左栏：发帖 -->
      <section class="panel disc-left">
        <div class="panel-head"><h3>发起新帖</h3></div>
        <div class="panel-body">
          <el-form label-position="top" @submit.prevent="submitPost">
            <el-form-item label="所属课程">
              <el-select v-model="postCourse" style="width: 100%" @change="onCourseChange">
                <el-option v-for="c in DEMO.courses" :key="c.id" :value="String(c.id)" :label="c.name" />
              </el-select>
            </el-form-item>
            <el-form-item label="标题">
              <el-input v-model="postTitle" placeholder="请输入讨论主题" />
            </el-form-item>
            <el-form-item label="内容">
              <el-input v-model="postContent" type="textarea" :rows="5" placeholder="描述你的问题或观点…" />
            </el-form-item>
            <el-button type="primary" native-type="submit">发布帖子</el-button>
          </el-form>
        </div>
      </section>

      <!-- 右栏：帖子列表 -->
      <section class="panel disc-right">
        <div class="panel-head">
          <h3>帖子列表 <span class="muted">（{{ courseName(state.courseId) }}）</span></h3>
        </div>
        <div class="panel-body">
          <div v-if="!posts.length" class="empty-tip">暂无帖子，左侧发起第一个讨论吧</div>
          <ul v-else class="post-list">
            <li v-for="p in posts" :key="p.id" class="post-item" :class="{ essence: p.is_essence }">
              <div class="post-head">
                <span class="post-title">{{ p.title }}</span>
                <el-tag v-if="p.is_top" size="small" type="warning">置顶</el-tag>
                <el-tag v-if="p.is_essence" size="small" type="success">精华</el-tag>
              </div>
              <div class="post-meta">{{ p.author_name || ('教师#' + p.author_id) }} · {{ fmtTime(p.created_at) }}</div>
              <div class="post-content">{{ p.content }}</div>
              <div class="post-actions">
                <el-button size="small" @click="toggleFlag(p.id, 'is_essence')">{{ p.is_essence ? '取消精华' : '设精华' }}</el-button>
                <el-button size="small" @click="toggleFlag(p.id, 'is_top')">{{ p.is_top ? '取消置顶' : '置顶' }}</el-button>
                <el-button size="small" @click="toggleReplies(p.id)">回复</el-button>
                <el-button size="small" type="danger" @click="deletePost(p.id)">删除</el-button>
              </div>

              <div v-if="state.expanded === p.id" class="reply-area">
                <div v-if="!repliesOf(p.id).length" class="empty-tip">暂无回复</div>
                <div v-for="r in repliesOf(p.id)" :key="r.id" class="reply-item">
                  <span class="reply-author">{{ r.author_name || ('教师#' + r.author_id) }}</span>
                  <span class="reply-time">{{ fmtTime(r.created_at) }}</span>
                  <div class="reply-content">{{ r.content }}</div>
                </div>
                <div class="reply-form">
                  <el-input v-model="replyDrafts[p.id]" size="small" placeholder="写下你的回复…" @keyup.enter="submitReply(p.id)" />
                  <el-button size="small" type="primary" @click="submitReply(p.id)">回复</el-button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.disc-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.disc-left {
  flex: 1 1 32%;
  min-width: 0;
}

.disc-right {
  flex: 1 1 68%;
  min-width: 0;
}

/* 帖子列表 */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 40px;
}

.post-item {
  border: 1px solid #e5e5e5;
  border-radius: 5px;
  padding: 12px 14px;
  background: #fff;
}

.post-item.essence {
  border-left: 3px solid #2e7d32;
}

.post-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.post-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.post-meta {
  font-size: 12px;
  color: #999;
  margin: 4px 0 8px;
}

.post-content {
  font-size: 14px;
  color: #444;
  line-height: 1.6;
  margin-bottom: 10px;
  white-space: pre-wrap;
}

.post-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 回复区 */
.reply-area {
  margin-top: 12px;
  border-top: 1px dashed #e5e5e5;
  padding-top: 10px;
}

.reply-item {
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.reply-author {
  font-weight: 600;
  font-size: 13px;
  color: var(--brand-primary);
  margin-right: 8px;
}

.reply-time {
  font-size: 12px;
  color: #bbb;
}

.reply-content {
  font-size: 13px;
  color: #444;
  line-height: 1.6;
  margin-top: 2px;
}

.reply-form {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
</style>
