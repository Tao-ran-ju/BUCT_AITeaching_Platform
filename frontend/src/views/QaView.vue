<script setup>
import { ref } from 'vue'

// ---------- 常见问题（纯静态，无 API） ----------
const qaItems = [
  {
    q: '1. 教师端如何登录？初始账号密码是什么？',
    a: '教师账号由系统管理员统一分配，初始账号为工号，初始密码为身份证后六位。首次登录后请务必前往「个人设置」中修改密码并绑定手机号，确保账号安全。如忘记密码可联系管理员重置。'
  },
  {
    q: '2. 如何录入和修改学生课程成绩？',
    a: '登录后进入「课程管理」-「成绩录入」，选择对应班级与课程即可在线录入成绩；支持批量导入Excel表格，模板可在页面右上角下载。成绩提交后在审核通过前可修改，审核通过后需提交成绩变更申请。'
  },
  {
    q: '3. 怎么发布班级公告和作业通知？',
    a: '在「班级管理」中选择对应班级，点击「发布公告」即可编辑通知内容，支持附件上传；发布后学生端将实时收到提醒。公告可设置置顶、定时发布和撤回，操作记录全程可追溯。'
  },
  {
    q: '4. 可以导出班级学生名单和考勤数据吗？',
    a: '支持导出。在「数据统计」模块可选择导出学生名单、考勤记录、成绩分析表等，支持Excel和PDF两种格式。导出数据默认按学期筛选，可自定义时间范围和导出字段。'
  },
  {
    q: '5. 教师端支持哪些浏览器？出现页面显示异常怎么办？',
    a: '推荐使用 Chrome、Edge、Firefox 最新版本浏览器，不建议使用 IE 浏览器。如出现页面加载异常、按钮无反应等情况，请先清除浏览器缓存或切换无痕模式重试，仍无法解决可联系开发者排查。'
  },
  {
    q: '6. 一个教师可以同时管理多个班级吗？',
    a: '可以。系统支持一位教师绑定多门课程、多个班级，登录后可在顶部班级切换栏快速跳转。不同班级的数据相互独立，成绩、公告、考勤均分开统计，不会混淆。'
  }
]

// 默认全部展开（与原页面的初始状态一致）
const activeNames = ref(qaItems.map((_, i) => i))

const developer = {
  avatar: '/assets/images/developer_avatar.png',
  name: '网站技术组',
  email: 'dev@example.com',
  phone: '010-xxxxxxx'
}
</script>

<template>
  <div class="wrapper page-body">
    <div class="page-header">
      <h2>常见问题答疑</h2>
      <p>针对每条问答，点击右上角 + 号以查看详情，点击右上角 x 号以关闭详情</p>
    </div>

    <div class="qa-container">
      <!-- 问答列表 -->
      <div class="qa-list">
        <el-collapse v-model="activeNames">
          <el-collapse-item v-for="(item, i) in qaItems" :key="i" :name="i">
            <template #title>
              <span class="q-title">{{ item.q }}</span>
            </template>
            <div class="q-answer">{{ item.a }}</div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 联系开发者区域 -->
      <div class="contact-developer">
        <div class="contact-text">
          <h3>没看到关于你疑问的解答？请联系开发者</h3>
          <p>工作时间：工作日 9:00 - 17:00</p>
          <p>非紧急问题可发送邮件，24小时内回复</p>
        </div>
        <div class="developer-info">
          <img :src="developer.avatar" alt="开发者头像" class="avatar">
          <div class="info-detail">
            <p><strong>开发者：</strong>{{ developer.name }}</p>
            <p><strong>联系邮箱：</strong>{{ developer.email }}</p>
            <p><strong>联系电话：</strong>{{ developer.phone }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qa-container {
  max-width: 850px;
  margin: 0 auto;
}

.qa-list {
  margin-bottom: 40px;
}

.q-title {
  font-weight: 500;
  color: #333;
}

.q-answer {
  line-height: 1.8;
  color: #555;
}

/* 让折叠面板呈现出与原页一致的卡片外观 */
.qa-list :deep(.el-collapse) {
  border: none;
}

.qa-list :deep(.el-collapse-item) {
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  margin-bottom: 12px;
  overflow: hidden;
}

.qa-list :deep(.el-collapse-item__header) {
  background-color: #fafafa;
  font-size: 15px;
  height: auto;
  min-height: 48px;
  line-height: 1.6;
  padding: 12px 20px;
  transition: background-color 0.2s;
}

.qa-list :deep(.el-collapse-item__header:hover) {
  background-color: #f0f0f0;
}

.qa-list :deep(.el-collapse-item__content) {
  padding: 15px 20px;
  border-top: 1px solid #eee;
}

/* 联系开发者区域 */
.contact-developer {
  background-color: #fff;
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  padding: 25px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.contact-text h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: var(--brand-primary);
}

.contact-text p {
  color: #666;
  font-size: 14px;
  line-height: 1.8;
}

.developer-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.avatar {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  border: 2px solid #d0d0d0;
  object-fit: cover;
}

.info-detail p {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}
</style>
