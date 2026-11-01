<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api/index.js'

const props = defineProps({
  classId: { type: Number, required: true },
  classes: { type: Array, default: () => [] }
})

const STORE_KEY = 'buct_msg_sent_demo'
let demoId = 100

const DEMO = reactive({
  students: {
    1: [
      { id: 101, uid: '20240001', name: '张伟' },
      { id: 102, uid: '20240002', name: '李娜' },
      { id: 103, uid: '20240003', name: '王强' }
    ],
    2: [
      { id: 201, uid: '20240010', name: '赵敏' },
      { id: 202, uid: '20240011', name: '刘洋' }
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
  ]
})

const messages = ref([])

const msgType = ref('notice')
const msgTitle = ref('')
const msgContent = ref('')
const msgDeadline = ref('')
const classSelect = ref('')
const msgReceivers = ref('')
const msgFile = ref(null)

function nowStr() {
  const d = new Date()
  const p = (n) => (n < 10 ? '0' + n : '' + n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}

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

const notices = computed(() =>
  messages.value
    .filter((m) => m.message_type === 'notice' || m.message_type === 'system')
    .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
)

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

async function loadMessages() {
  const data = await api.request(api.listSentMessages(), DEMO.messages)
  messages.value = Array.isArray(data) ? data : ((data && data.items) || [])
}

async function getClassStudents(classId) {
  const students = await api.request(api.listClassStudents(classId), DEMO.students[classId] || [])
  DEMO.students[classId] = students || []
  return DEMO.students[classId]
}

async function fillReceivers(classId) {
  const students = await getClassStudents(classId)
  msgReceivers.value = students.map((s) => s.uid || s.username).join(', ')
}

function onMsgFileChange(e) {
  msgFile.value = e.target.files && e.target.files[0]
}

function onClassChange() {
  const cid = Number(classSelect.value)
  if (!cid) {
    msgReceivers.value = ''
    return
  }
  fillReceivers(cid)
}

function resetForm() {
  msgType.value = 'notice'
  msgTitle.value = ''
  msgContent.value = ''
  msgDeadline.value = ''
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
  if (type === 'assignment' && deadline) fd.append('deadline', deadline)
  if (msgFile.value) fd.append('file', msgFile.value)

  api.request(api.sendMessage(fd)).then(() => {
    ElMessage.success('发布成功')
    resetForm()
    loadMessages()
  }).catch(() => {
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

function syncClass() {
  classSelect.value = String(props.classId)
  fillReceivers(props.classId)
}

onMounted(() => {
  loadDemoStore()
  loadMessages()
  syncClass()
})

watch(() => props.classId, syncClass)
</script>

<template>
  <div class="mq-layout">
    <section class="panel mq-left">
      <div class="panel-head"><h3>通知公告</h3></div>
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

    <section class="panel mq-right">
      <div class="panel-head"><h3>发布通知 / 任务</h3></div>
      <div class="panel-body">
        <el-form label-width="100px" label-position="left" @submit.prevent="submitMessage">
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
              <el-option v-for="c in classes" :key="c.id" :value="String(c.id)" :label="c.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="接收学生学号">
            <el-input
              v-model="msgReceivers"
              type="textarea"
              :rows="3"
              placeholder="学号，逗号或换行分隔，如：2022040152, 2022040153"
            />
            <div class="form-hint">已默认填入当前班级学生学号，也可手动修改。</div>
          </el-form-item>
          <el-form-item label="Word 附件">
            <input type="file" accept=".doc,.docx" class="file-input" @change="onMsgFileChange">
            <div class="form-hint">仅支持 .doc / .docx，单个不超过 10MB。</div>
          </el-form-item>
          <el-button type="primary" native-type="submit">发布</el-button>
        </el-form>
      </div>
    </section>
  </div>
</template>

<style scoped>
.mq-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.mq-left {
  flex: 1 1 55%;
  min-width: 0;
}
.mq-right {
  flex: 1 1 45%;
  min-width: 0;
}

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

.notice-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.notice-title {
  font-weight: 600;
  color: #333;
  flex: 1;
}
.notice-time {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}
.notice-content {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  word-break: break-word;
}
.notice-meta {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}
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
</style>
