<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

// ---------- 演示数据（无后端时回退） ----------
const DEFAULT_AVATAR = '/assets/images/default_avatar.png'

const DEMO_USER = {
  id: 1, username: 'T2024001', name: '张老师', role: 'teacher',
  department: '计算机科学与技术学院', email: 'teacher@buct.edu.cn',
  phone: '13800138000', position: '副教授', avatar: null, status: 'active'
}

const currentUser = reactive({ ...DEMO_USER })
const form = reactive({ username: '', name: '', department: '', email: '', phone: '', position: '' })
const avatarUrl = ref(DEFAULT_AVATAR)
const avatarInput = ref(null)
const saving = ref(false)
const saveTip = ref('')
const saveTipError = ref(false)
let tipTimer = null

// 修改密码对话框
const pwdDialog = reactive({
  visible: false,
  form: { old_password: '', new_password: '', confirm_password: '' }
})

// ---------- 工具函数 ----------
function fullUrl(path) {
  if (!path) return DEFAULT_AVATAR
  if (/^https?:\/\//.test(path)) return path
  const origin = api.BASE_URL ? api.BASE_URL.replace(/\/api\/v1\/?$/, '') : ''
  const clean = path.charAt(0) === '/' ? path : '/' + path
  return origin ? origin + clean : clean
}

function fillForm(user) {
  Object.assign(currentUser, user || DEMO_USER)
  form.username = currentUser.username || ''
  form.name = currentUser.name || ''
  form.department = currentUser.department || ''
  form.email = currentUser.email || ''
  form.phone = currentUser.phone || ''
  form.position = currentUser.position || ''
  avatarUrl.value = fullUrl(currentUser.avatar || null)
}

function setTip(msg, isError) {
  saveTip.value = msg || ''
  saveTipError.value = !!isError
  if (tipTimer) clearTimeout(tipTimer)
  if (msg) tipTimer = setTimeout(() => { saveTip.value = '' }, 4000)
}

// ---------- 加载 ----------
async function loadProfile() {
  const data = await api.request(api.getMe(), DEMO_USER)
  fillForm(data || DEMO_USER)
}

// ---------- 头像上传 ----------
function pickAvatar() {
  avatarInput.value && avatarInput.value.click()
}

function onAvatarChange(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (!file.type || file.type.indexOf('image/') !== 0) {
    ElMessage.error('请选择图片文件')
    e.target.value = ''
    return
  }

  // 先本地预览，再真实上传
  const reader = new FileReader()
  reader.onload = (ev) => {
    avatarUrl.value = ev.target.result
  }
  reader.readAsDataURL(file)

  const fd = new FormData()
  fd.append('file', file)
  api.request(api.uploadAvatar(fd)).then((res) => {
    if (res && res.avatar) {
      currentUser.avatar = res.avatar
      avatarUrl.value = fullUrl(res.avatar)
    }
    ElMessage.success('头像已上传并保存')
  }).catch(() => {
    ElMessage.success('演示模式：头像仅本地预览，未上传')
  })

  e.target.value = '' // 允许再次选择同一文件
}

// ---------- 保存基本信息 ----------
function saveProfile() {
  const payload = {
    name: form.name.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
    department: form.department.trim(),
    position: form.position.trim()
  }

  if (!payload.name) { setTip('姓名不能为空', true); return }
  if (!payload.email) { setTip('邮箱不能为空', true); return }

  saving.value = true
  api.request(api.updateMe(payload)).then((res) => {
    if (res && res.name) fillForm(res)
    setTip('保存成功，已写入数据库', false)
    ElMessage.success('个人信息保存成功')
  }).catch(() => {
    Object.assign(currentUser, payload)
    fillForm(currentUser)
    setTip('演示模式：未连接后端，信息未真正保存', true)
    ElMessage.success('演示模式：信息未真正保存')
  }).finally(() => {
    saving.value = false
  })
}

function resetForm() {
  fillForm(currentUser)
  setTip('', false)
}

// ---------- 修改密码 ----------
function openPwdDialog() {
  pwdDialog.form = { old_password: '', new_password: '', confirm_password: '' }
  pwdDialog.visible = true
}

function submitPassword() {
  const { old_password, new_password, confirm_password } = pwdDialog.form
  if (!old_password) { ElMessage.error('请输入原密码'); return }
  if (!new_password) { ElMessage.error('请输入新密码'); return }
  if (new_password !== confirm_password) { ElMessage.error('两次输入的新密码不一致'); return }

  api.request(api.changePassword({ old_password, new_password })).then(() => {
    ElMessage.success('密码修改成功')
    pwdDialog.visible = false
  }).catch(() => {
    ElMessage.success('演示模式：密码未真正修改')
    pwdDialog.visible = false
  })
}

onMounted(loadProfile)
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>个人设置</h2>
      <p>维护个人基本信息、上传头像，并管理账号密码。</p>
    </div>

    <div class="profile-container">
      <!-- 左侧：头像展示与上传区 -->
      <section class="panel profile-left">
        <div class="panel-body avatar-body">
          <img class="avatar" :src="avatarUrl" alt="用户头像">

          <div class="upload-area">
            <input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatarChange">
            <el-button type="primary" @click="pickAvatar">上传新头像</el-button>
          </div>

          <div class="preview-area">
            <h4>头像预览</h4>
            <img :src="avatarUrl" alt="预览图">
            <p>上传后可在此预览效果</p>
          </div>
        </div>
      </section>

      <!-- 右侧：个人信息编辑区 -->
      <section class="panel profile-right">
        <div class="panel-head">
          <h3>个人基本信息</h3>
          <el-button size="small" @click="openPwdDialog">修改密码</el-button>
        </div>
        <div class="panel-body">
          <el-form label-width="90px" label-position="left" @submit.prevent="saveProfile">
            <el-form-item label="工号">
              <el-input v-model="form.username" disabled />
            </el-form-item>
            <el-form-item label="姓名" required>
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="所属部门">
              <el-input v-model="form.department" placeholder="请输入所属部门" />
            </el-form-item>
            <el-form-item label="邮箱" required>
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="联系方式">
              <el-input v-model="form.phone" placeholder="请输入联系方式" />
            </el-form-item>
            <el-form-item label="职称">
              <el-input v-model="form.position" placeholder="请输入职称" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="saving">保存修改</el-button>
              <el-button @click="resetForm">重置</el-button>
              <span v-if="saveTip" class="save-tip" :class="{ error: saveTipError }">{{ saveTip }}</span>
            </el-form-item>
          </el-form>
        </div>
      </section>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="pwdDialog.visible" title="修改密码" width="440px">
      <el-form label-width="90px">
        <el-form-item label="原密码" required>
          <el-input v-model="pwdDialog.form.old_password" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="pwdDialog.form.new_password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="pwdDialog.form.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.profile-container {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.profile-left {
  flex: 1 1 380px;
  min-width: 0;
  text-align: center;
}

.profile-right {
  flex: 1 1 640px;
  min-width: 0;
}

.avatar-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 30px 20px;
}

.profile-left .avatar {
  width: 260px;
  height: 260px;
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  object-fit: cover;
  background: #f5f5f5;
}

.preview-area h4 {
  font-size: 14px;
  font-weight: normal;
  color: #666;
  margin-bottom: 8px;
}

.preview-area img {
  width: 60px;
  height: 60px;
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  object-fit: cover;
  margin: 0 auto 4px;
}

.preview-area p {
  font-size: 12px;
  color: #999;
}

.save-tip {
  font-size: 14px;
  color: #2e7d32;
  margin-left: 10px;
}

.save-tip.error {
  color: #c62828;
}
</style>
