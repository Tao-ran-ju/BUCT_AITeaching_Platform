<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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

// ---------- 滑动下划线（悬停跟随，移开后回到当前激活项） ----------
const navWrapper = ref(null)
const underlineEl = ref(null)

function targetEl() {
  const wrapper = navWrapper.value
  if (!wrapper) return null
  // 当前激活的核心栏目，或激活的「更多功能」
  return wrapper.querySelector('a.activated, .more-trigger.activated')
}

function moveUnderline(el) {
  if (!el || !underlineEl.value || !navWrapper.value) return
  const aRect = el.getBoundingClientRect()
  const wRect = navWrapper.value.getBoundingClientRect()
  const pad = parseFloat(getComputedStyle(el).paddingLeft) || 0
  underlineEl.value.style.left = (aRect.left - wRect.left + pad) + 'px'
}

function onEnter(e) {
  moveUnderline(e.currentTarget)
}

function onLeave() {
  moveUnderline(targetEl())
}

function reposition() {
  nextTick(() => moveUnderline(targetEl()))
}

function onResize() {
  reposition()
}

onMounted(() => {
  reposition()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})

watch(() => route.path, reposition)
</script>

<template>
  <div class="shortcut">
    <div class="wrapper nav-wrapper" ref="navWrapper">
      <img src="/assets/images/buct.png" alt="北京化工大学" class="logo">
      <img
        src="/assets/images/college_of_information_science_and_technology.png"
        alt="信息科学与技术学院"
        class="logo-college"
      >
      <span class="brand-title">教师端在线</span>
      <ul class="nav-list">
        <li v-for="item in coreNav" :key="item.to">
          <router-link
            :to="item.to"
            :class="{ activated: isActive(item.to) }"
            @mouseenter="onEnter"
            @mouseleave="onLeave"
          >
            {{ item.label }}
          </router-link>
        </li>
        <li>
          <el-dropdown trigger="hover">
            <span
              class="more-trigger"
              :class="{ activated: moreActive }"
              @mouseenter="onEnter"
              @mouseleave="onLeave"
            >更多功能 ▾</span>
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
      <div class="underline" ref="underlineEl"></div>
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
  height: 34px;
  flex-shrink: 0;
}

.logo-college {
  height: 34px;
  max-width: 90%;
  max-height: 90%;
  margin: 0 14px;
  flex-shrink: 0;
}

.brand-title {
  line-height: 52px;
  font-family: 'STXingkai', '华文行楷', sans-serif;
  font-weight: 700;
  font-size: 30px;
  color: #333;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-list {
  display: flex;
  margin-left: auto;
  line-height: 52px;
  flex-shrink: 0;
}

.nav-list li a,
.more-trigger {
  display: inline-block;
  padding: 0 14px;
  color: #333;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: color 0.2s;
}

.nav-list li a {
  border-right: 1px solid #333;
}

.nav-list li a:hover,
.more-trigger:hover,
.activated {
  color: var(--brand-primary);
}

/* 滑动下划线：悬停/激活时跟随到对应栏目下方 */
.underline {
  position: absolute;
  bottom: 8px;
  left: 0;
  width: 65px;
  height: 2px;
  background: var(--brand-primary);
  transition: left 0.3s ease;
  pointer-events: none;
}
</style>
