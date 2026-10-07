<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
let demoId = 1000
const DEMO = reactive({
  warnings: [
    {
      id: 1, student_id: 101, student_name: '张伟', course_id: 1, course_name: '算法设计与分析',
      risk_level: 'high', reason: '作业正确率低于 30%；作业提交延迟 5 天',
      suggestion: '', is_resolved: false, created_at: '2024-09-20 10:00'
    },
    {
      id: 2, student_id: 102, student_name: '李娜', course_id: 1, course_name: '算法设计与分析',
      risk_level: 'medium', reason: '作业提交延迟 4 天',
      suggestion: '', is_resolved: false, created_at: '2024-09-19 09:30'
    },
    {
      id: 3, student_id: 103, student_name: '王强', course_id: 2, course_name: '数据结构',
      risk_level: 'low', reason: '作业提交延迟 1 天',
      suggestion: '', is_resolved: false, created_at: '2024-09-18 14:00'
    },
    {
      id: 4, student_id: 201, student_name: '赵敏', course_id: 2, course_name: '数据结构',
      risk_level: 'medium', reason: '作业正确率低于 30%',
      suggestion: '建议课后单独辅导，巩固线性表与指针基础，并布置针对性练习。',
      is_resolved: true, created_at: '2024-09-16 11:20'
    }
  ]
})

const RISK_LABEL = { high: '高风险', medium: '中风险', low: '低风险' }
const RISK_ICON = { high: '⛔', medium: '⚠', low: 'ℹ' }
const RISK_TAG = { high: 'danger', medium: 'warning', low: 'success' }
const RISK_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'high', label: '高风险' },
  { value: 'medium', label: '中风险' },
  { value: 'low', label: '低风险' }
]

const state = reactive({
  riskLevel: '',
  warnings: [],
  scanning: false,
  scanHint: ''
})
const suggestingId = ref(null)

function nowStr() {
  const d = new Date()
  function p(n) { return n < 10 ? '0' + n : '' + n }
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

// 兼容后端 ISO 格式（2024-09-20T10:00:00）与演示格式（2024-09-20 10:00）
function fmtTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').slice(0, 16)
}

// ---------- 列表 ----------
async function loadWarnings() {
  const riskLevel = state.riskLevel || null
  const params = { page: 1, page_size: 100 }
  if (riskLevel) params.risk_level = riskLevel

  const fallbackItems = DEMO.warnings.filter((w) => (riskLevel ? w.risk_level === riskLevel : true))
  const data = await api.request(
    api.listWarnings(params),
    { items: fallbackItems, total: fallbackItems.length }
  )
  state.warnings = (data && data.items) || []
}

// ---------- AI 建议 ----------
function generateSuggestion(id) {
  suggestingId.value = id
  function done() {
    suggestingId.value = null
    loadWarnings()
  }
  api.request(api.aiSuggestion(id)).then((res) => {
    if (res && res.suggestion) {
      ElMessage.success('干预建议已生成')
    } else {
      ElMessage.error('后端未配置大模型，建议生成失败')
    }
    done()
  }).catch(() => {
    DEMO.warnings.forEach((w) => {
      if (w.id === id && !w.suggestion) {
        w.suggestion = '建议：课后安排一次 1 对 1 辅导，针对薄弱知识点布置针对性练习，并在一周后复查掌握情况。'
      }
    })
    ElMessage.success('演示模式：已本地生成建议')
    done()
  })
}

// ---------- 标记已处理（记录干预措施） ----------
const resolveDialog = reactive({ visible: false, id: null, form: { intervention: '' } })

function openResolveDialog(w) {
  resolveDialog.id = w.id
  resolveDialog.form.intervention = w.suggestion || ''
  resolveDialog.visible = true
}

function submitResolve() {
  const id = resolveDialog.id
  const intervention = resolveDialog.form.intervention.trim()
  api.request(api.resolveWarning(id, intervention)).then(() => {
    ElMessage.success(intervention ? '已标记处理并记录干预措施' : '已标记处理')
    loadWarnings()
  }).catch(() => {
    DEMO.warnings.forEach((x) => {
      if (x.id === id) {
        x.is_resolved = true
        x.intervention = intervention || x.suggestion || ''
        x.resolved_at = nowStr()
      }
    })
    ElMessage.success('演示模式：已本地标记处理')
    loadWarnings()
  })
  resolveDialog.visible = false
}

// ---------- 扫描 ----------
function scanWarnings() {
  state.scanning = true
  function done() {
    state.scanning = false
    loadWarnings()
  }
  api.request(api.scanWarnings()).then((res) => {
    const n = (res && res.generated != null) ? res.generated : 0
    state.scanHint = '本次生成 ' + n + ' 条新预警'
    ElMessage.success('扫描完成')
    done()
  }).catch(() => {
    DEMO.warnings.unshift({
      id: ++demoId, student_id: 301, student_name: '陈晨',
      course_id: 1, course_name: '算法设计与分析',
      risk_level: 'medium', reason: '作业提交延迟 3 天',
      suggestion: '', is_resolved: false, created_at: nowStr()
    })
    state.scanHint = '演示模式：模拟生成 1 条新预警'
    ElMessage.success('演示模式：扫描完成')
    done()
  })
}

// ---------- 初始化 ----------
onMounted(loadWarnings)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>学情预警与干预</h2>
      <p>基于学习行为规则引擎自动扫描潜在风险，支持 AI 生成个性化干预建议。</p>
    </div>

    <div class="warn-toolbar">
      <el-button type="primary" :loading="state.scanning" @click="scanWarnings">
        {{ state.scanning ? '扫描中…' : '立即扫描' }}
      </el-button>
      <div class="form-row inline">
        <label class="form-label">风险等级</label>
        <el-select v-model="state.riskLevel" class="risk-select" @change="loadWarnings">
          <el-option v-for="o in RISK_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
        </el-select>
      </div>
      <span class="warn-hint">{{ state.scanHint }}</span>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3>预警列表</h3>
        <span class="panel-sub">共 {{ state.warnings.length }} 条</span>
      </div>
      <div class="panel-body">
        <el-table :data="state.warnings" size="small">
          <el-table-column label="学生" min-width="100">
            <template #default="{ row }">{{ row.student_name || ('学生#' + row.student_id) }}</template>
          </el-table-column>
          <el-table-column label="课程" min-width="140">
            <template #default="{ row }">{{ row.course_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="风险等级" width="110">
            <template #default="{ row }">
              <el-tag :type="RISK_TAG[row.risk_level] || 'warning'">
                {{ RISK_ICON[row.risk_level] }} {{ RISK_LABEL[row.risk_level] || row.risk_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="预警原因" min-width="220">
            <template #default="{ row }">
              <div class="warn-reason">{{ row.reason || '-' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="干预建议" min-width="240">
            <template #default="{ row }">
              <div v-if="row.suggestion" class="warn-suggestion">{{ row.suggestion }}</div>
              <span v-else class="pending-tip">未生成</span>
            </template>
          </el-table-column>
          <el-table-column label="干预措施" min-width="180">
            <template #default="{ row }">
              <div v-if="row.intervention" class="warn-intervention">{{ row.intervention }}</div>
              <span v-else class="pending-tip">—</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="130">
            <template #default="{ row }">
              <template v-if="row.is_resolved">
                <el-tag type="success">已处理</el-tag>
                <div v-if="row.resolved_at" class="warn-resolved-at">{{ fmtTime(row.resolved_at) }}</div>
              </template>
              <el-tag v-else type="warning">待处理</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <div class="row-actions">
                <el-button
                  size="small"
                  :loading="suggestingId === row.id"
                  @click="generateSuggestion(row.id)"
                >
                  {{ suggestingId === row.id ? '生成中…' : 'AI 建议' }}
                </el-button>
                <el-button v-if="!row.is_resolved" size="small" type="primary" @click="openResolveDialog(row)">
                  标记已处理
                </el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-tip">暂无预警，点击「立即扫描」生成</div>
          </template>
        </el-table>
      </div>
    </section>

    <!-- 标记已处理对话框 -->
    <el-dialog v-model="resolveDialog.visible" title="标记预警已处理" width="520px">
      <el-form label-width="100px" label-position="left">
        <el-form-item label="干预措施">
          <el-input
            v-model="resolveDialog.form.intervention"
            type="textarea"
            :rows="4"
            placeholder="记录本次采取的具体干预措施，如：课后 1 对 1 辅导、布置针对性练习…"
          />
        </el-form-item>
      </el-form>
      <p class="form-hint">可先点「AI 建议」生成参考，再在此记录实际采取的措施。</p>
      <template #footer>
        <el-button @click="resolveDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitResolve">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.warn-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 16px;
}

.warn-toolbar .form-row {
  margin-bottom: 0;
}

.form-row.inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  color: #555;
  white-space: nowrap;
}

.risk-select {
  width: 140px;
}

.warn-hint {
  font-size: 13px;
  color: #999;
  align-self: center;
}

/* 面板副标题 */
.panel-sub {
  font-size: 12px;
  color: #999;
}

/* 预警原因 */
.warn-reason {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  max-width: 240px;
}

/* AI 干预建议 */
.warn-suggestion {
  font-size: 13px;
  color: var(--brand-primary);
  line-height: 1.6;
  max-width: 260px;
}

.pending-tip {
  font-size: 13px;
  color: #bbb;
}

/* 干预措施（标记处理时记录） */
.warn-intervention {
  font-size: 13px;
  color: #2e7d32;
  line-height: 1.6;
  max-width: 200px;
}

.warn-resolved-at {
  font-size: 12px;
  color: #999;
  margin-top: 3px;
  white-space: nowrap;
}

/* 对话框内提示文案 */
.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 行内操作按钮 */
.row-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
