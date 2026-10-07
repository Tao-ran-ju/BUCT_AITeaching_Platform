<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const coreNav = [
  { label: '网站主页', to: '/' },
  { label: '课程资源', to: '/course-resources' },
  { label: '班级管理', to: '/class-management' },
  { label: '备课中心', to: '/aigc' },
  { label: '作业批改', to: '/homework-correction' },
  { label: '消息队列', to: '/message-queue' },
  { label: '个人设置', to: '/personal-setting' }
]

const moreNav = [
  { label: '数据驾驶舱', to: '/dashboard' },
  { label: '学情预警', to: '/warning' },
  { label: '主题讨论区', to: '/discussion' },
  { label: '学习小组', to: '/team' },
  { label: 'Q&A', to: '/qa' }
]

function isActive(to) {
  return route.path === to
}

const moreActive = computed(() => moreNav.some((item) => route.path === item.to))

function go(to) {
  router.push(to)
}
</script>

<template>
  <div class="shortcut">
    <div class="wrapper nav-wrapper">
      <img src="/assets/images/buct.png" alt="北京化工大学" class="logo">
      <img
        src="/assets/images/college_of_information_science_and_technology.png"
        alt="信息科学与技术学院"
        class="logo-college"
      >
      <span class="brand-title">教师端在线</span>
      <ul class="nav-list">
        <li v-for="item in coreNav" :key="item.to">
          <router-link :to="item.to" :class="{ activated: isActive(item.to) }">
            {{ item.label }}
          </router-link>
        </li>
        <li>
          <el-dropdown trigger="hover">
            <span class="more-trigger" :class="{ activated: moreActive }">更多功能 ▾</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="item in moreNav"
                  :key="item.to"
                  @click="go(item.to)"
                >
                  {{ item.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.shortcut {
  height: 52px;
  background-color: #fff;
  box-shadow: 0 8px 10px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-wrapper {
  display: flex;
  align-items: center;
  height: 52px;
  position: relative;
  background-color: #fff;
}

.logo {
  height: 40px;
}

.logo-college {
  height: 40px;
  max-height: 90%;
  max-width: 90%;
  margin: 0 25px;
}

.brand-title {
  line-height: 52px;
  font-family: 'STXingkai', '华文行楷', sans-serif;
  font-weight: 700;
  font-size: 40px;
  color: #333;
}

.nav-list {
  display: flex;
  margin-left: auto;
  line-height: 52px;
}

.nav-list li a,
.more-trigger {
  display: inline-block;
  padding: 0 15px;
  border-right: 1px solid #333;
  color: #333;
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}

.nav-list li:last-child a,
.more-trigger {
  border-right: none;
}

.nav-list li a:hover,
.more-trigger:hover,
.activated {
  color: var(--brand-primary);
}

.nav-list li a {
  border-bottom: 2px solid transparent;
}

.nav-list li a.activated {
  border-bottom: 2px solid var(--brand-primary);
}
</style>
