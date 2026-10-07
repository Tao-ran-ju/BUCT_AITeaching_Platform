<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// ========== 轮播 ==========
const banners = [
  { src: '/assets/images/banner1.jpeg', alt: '轮播图1' },
  { src: '/assets/images/banner2.jpeg', alt: '轮播图2' },
  { src: '/assets/images/banner3.jpeg', alt: '轮播图3' }
]
const currentIndex = ref(0)
let timer = null

function switchTo(index) {
  const n = banners.length
  currentIndex.value = ((index % n) + n) % n
}
function startAutoPlay() {
  timer = setInterval(() => switchTo(currentIndex.value + 1), 3000)
}
function stopAutoPlay() {
  clearInterval(timer)
}

// ========== 时钟 ==========
const digitalTime = ref('')
const secDeg = ref(0)
const minDeg = ref(0)
const hourDeg = ref(0)

function padZero(n) {
  return n.toString().padStart(2, '0')
}

function updateClock() {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const d = now.getDate()
  const h = now.getHours()
  const mi = now.getMinutes()
  const s = now.getSeconds()

  digitalTime.value = `${y}年${padZero(m)}月${padZero(d)}日 ${padZero(h)}:${padZero(mi)}:${padZero(s)}`
  secDeg.value = s * 6
  minDeg.value = mi * 6 + s * 0.1
  hourDeg.value = (h % 12) * 30 + mi * 0.5
}

// ========== 日历 ==========
const calHeader = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月`
})

const dayCells = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const todayDate = now.getDate()

  const firstDay = new Date(year, month, 1)
  const totalDays = new Date(year, month + 1, 0).getDate()
  const startWeek = firstDay.getDay()
  const prevMonthLast = new Date(year, month, 0).getDate()

  const cells = []
  for (let i = 0; i < startWeek; i++) {
    cells.push({ day: prevMonthLast - startWeek + 1 + i, other: true })
  }
  for (let d = 1; d <= totalDays; d++) {
    cells.push({ day: d, other: false, today: d === todayDate })
  }
  const needFill = 42 - cells.length
  for (let i = 1; i <= needFill; i++) {
    cells.push({ day: i, other: true })
  }
  return cells
})

// ========== 静态内容 ==========
const news = [
  { text: '新人入站必看！关于教师端的集中答疑Q&A', to: '/qa' },
  { text: '关于教师端服务器维修的通知', to: '' },
  { text: '关于教师端网页功能布局的改动通知', to: '' },
  { text: '其他公告信息示例', to: '' },
  { text: '条目测试中...', to: '' },
  { text: '条目测试中...', to: '' },
  { text: '条目测试中...', to: '' },
  { text: '条目测试中...', to: '' }
]

const features = [
  { icon: '📊', title: '数据驾驶舱', desc: '核心指标 · 能力矩阵 · 学习不积极学生预警', to: '/dashboard' },
  { icon: '⚠️', title: '学情预警与干预', desc: '规则扫描 · 风险分级 · AI 干预建议', to: '/warning' },
  { icon: '💬', title: '主题讨论区', desc: '发帖讨论 · 精华置顶 · 师生互动', to: '/discussion' },
  { icon: '👥', title: '学习小组', desc: '组建小组 · 指定组长 · 成员管理', to: '/team' }
]

onMounted(() => {
  startAutoPlay()
  updateClock()
  setInterval(updateClock, 1000)
})

onBeforeUnmount(() => {
  stopAutoPlay()
})
</script>

<template>
  <div class="wrapper">
    <div class="main-content">
      <!-- 左侧：系统公告 -->
      <div class="news">
        <h3>系统公告</h3>
        <ul class="news_content">
          <li v-for="(item, i) in news" :key="i">
            <router-link v-if="item.to" :to="item.to">{{ item.text }}</router-link>
            <template v-else>{{ item.text }}</template>
          </li>
        </ul>
      </div>

      <!-- 中间：轮播 Banner -->
      <div class="banner" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
        <div class="banner-images">
          <img
            v-for="(b, i) in banners"
            :key="b.src"
            :src="b.src"
            :alt="b.alt"
            class="banner-item"
            :class="{ active: currentIndex === i }"
          >
        </div>
        <a href="javascript:;" class="banner-arrow arrow-left" @click="switchTo(currentIndex - 1)">&lt;</a>
        <a href="javascript:;" class="banner-arrow arrow-right" @click="switchTo(currentIndex + 1)">&gt;</a>
        <div class="banner-indicators">
          <span
            v-for="(b, i) in banners"
            :key="i"
            class="indicator"
            :class="{ active: currentIndex === i }"
            @click="switchTo(i)"
          ></span>
        </div>
      </div>

      <!-- 右侧：时钟 + 日历 -->
      <div class="sidebar">
        <div class="card clock-card">
          <div class="card-title">实时时钟</div>
          <div class="digital-time">{{ digitalTime }}</div>
          <div class="analog-clock">
            <div class="clock-center"></div>
            <div class="hand hour-hand" :style="{ transform: `rotate(${hourDeg}deg)` }"></div>
            <div class="hand min-hand" :style="{ transform: `rotate(${minDeg}deg)` }"></div>
            <div class="hand sec-hand" :style="{ transform: `rotate(${secDeg}deg)` }"></div>
          </div>
        </div>

        <div class="card calendar-card">
          <div class="card-title">{{ calHeader }}</div>
          <div class="week-row">
            <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
          </div>
          <div class="day-grid">
            <div
              v-for="(cell, i) in dayCells"
              :key="i"
              class="day-cell"
              :class="{ today: cell.today, 'other-month': cell.other }"
            >{{ cell.day }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="feature-entry">
      <router-link v-for="f in features" :key="f.to" :to="f.to" class="feature-card">
        <span class="feature-icon">{{ f.icon }}</span>
        <span class="feature-title">{{ f.title }}</span>
        <span class="feature-desc">{{ f.desc }}</span>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.news {
  width: 300px;
  flex-shrink: 0;
  background-color: #fff;
  border-radius: 5px;
  border: #d0d0d0 solid 2px;
  overflow: hidden;
}
.news h3 {
  padding: 12px 15px;
  border-bottom: 2px solid #d0d0d0;
  font-size: 18px;
  font-weight: normal;
}
.news_content li {
  padding: 10px 0;
  margin: 0 10px;
  border-bottom: gray solid 2px;
}
.news_content li:last-child {
  border-bottom: none;
}
.news_content a:hover {
  color: #6a0dad;
  text-decoration: underline;
}

.main-content {
  display: flex;
  gap: 25px;
  padding: 50px 0;
  align-items: flex-start;
}

.banner {
  flex: 1;
  height: 360px;
  position: relative;
  border-radius: 5px;
  border: 2px solid #d0d0d0;
  overflow: hidden;
  background-color: #fff;
}
.banner-images {
  width: 100%;
  height: 100%;
  position: relative;
}
.banner-item {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.5s ease;
}
.banner-item.active {
  opacity: 1;
}
.banner-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 60px;
  background-color: rgba(0, 0, 0, 0.3);
  color: #fff;
  text-align: center;
  line-height: 60px;
  font-size: 20px;
  z-index: 10;
  transition: background-color 0.3s;
}
.banner-arrow:hover {
  background-color: rgba(0, 0, 0, 0.5);
}
.arrow-left {
  left: 0;
  border-radius: 0 4px 4px 0;
}
.arrow-right {
  right: 0;
  border-radius: 4px 0 0 4px;
}
.banner-indicators {
  position: absolute;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}
.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: background-color 0.3s;
}
.indicator.active {
  background-color: #fff;
}

.sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.card {
  background-color: #fff;
  border-radius: 5px;
  border: 2px solid #d0d0d0;
  overflow: hidden;
}
.card-title {
  padding: 12px 15px;
  border-bottom: 2px solid #d0d0d0;
  font-size: 18px;
}

.clock-card {
  text-align: center;
}
.digital-time {
  padding: 15px 0;
  font-size: 16px;
  font-family: monospace;
}
.analog-clock {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 6px solid #d0d0d0;
  position: relative;
  margin: 0 auto 20px;
  background-color: #f9f9f9;
}
.hand {
  position: absolute;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  border-radius: 4px;
}
.hour-hand {
  width: 6px;
  height: 48px;
  background-color: #333;
  margin-left: -3px;
}
.min-hand {
  width: 4px;
  height: 65px;
  background-color: #666;
  margin-left: -2px;
}
.sec-hand {
  width: 2px;
  height: 75px;
  background-color: #e94560;
  margin-left: -1px;
}
.clock-center {
  width: 12px;
  height: 12px;
  background: #333;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.calendar-card .card-title {
  text-align: center;
  margin-bottom: 10px;
}
.week-row,
.day-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  padding: 0 10px;
  text-align: center;
}
.week-row {
  margin-bottom: 8px;
  font-weight: bold;
  color: #666;
  font-size: 14px;
}
.day-cell {
  padding: 8px 0;
  border-radius: 4px;
  background-color: #f0f0f0;
  font-size: 14px;
}
.day-cell.today {
  background-color: #6a0dad;
  color: #fff;
  font-weight: bold;
}
.day-cell.other-month {
  color: #aaa;
  background-color: #f8f8f8;
}

.feature-entry {
  display: flex;
  gap: 25px;
  padding-bottom: 50px;
}
.feature-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background-color: #fff;
  border: 2px solid #d0d0d0;
  border-radius: 5px;
  padding: 22px 20px;
  text-decoration: none;
  color: #333;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.feature-card:hover {
  border-color: #6a0dad;
  box-shadow: 0 4px 12px rgba(106, 13, 173, 0.12);
  transform: translateY(-2px);
}
.feature-icon {
  font-size: 30px;
  line-height: 1;
}
.feature-title {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}
.feature-card:hover .feature-title {
  color: #6a0dad;
}
.feature-desc {
  font-size: 13px;
  color: #888;
}
</style>
