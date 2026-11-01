<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api/index.js'

const DEMO = reactive({
  pending: [
    { id: 1, student_id: 101, student_name: '张伟', content: '我在做动态规划作业时，01 背包的递推公式总是推不出来，能帮我看看思路吗？', classification: 'complex', created_at: '2024-09-20 14:30' },
    { id: 2, student_id: 102, student_name: '李娜', content: '运行归并排序代码时报了段错误，不知道哪里越界了，代码在作业里。', classification: 'complex', created_at: '2024-09-20 15:10' }
  ],
  stats: { pending: 2, auto_answered: 5, answered: 1 }
})

const qaData = reactive({ pending: [], stats: { pending: 0, auto_answered: 0, answered: 0 } })

function fmtTime(t) {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}

async function loadQaQuestions() {
  const data = await api.request(api.listQaQuestions(), DEMO)
  const d = data || { pending: [], stats: { pending: 0, auto_answered: 0, answered: 0 } }
  qaData.pending = Array.isArray(d.pending) ? d.pending : []
  qaData.stats = d.stats || { pending: 0, auto_answered: 0, answered: 0 }
}

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

onMounted(loadQaQuestions)
</script>

<template>
  <div>
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

    <p class="qa-tip">学生提问自动分流：简单问题 AI 直接回复，复杂问题留待你人工处理。</p>

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
.qa-tip {
  font-size: 13px;
  color: #999;
  margin: 0 0 14px;
}
.qa-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
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
.qa-stat-num.high { color: #e74c3c; }
.qa-stat-num.low { color: #27ae60; }
.qa-stat-num.medium { color: #f39c12; }
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
