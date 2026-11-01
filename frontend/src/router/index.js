import { createRouter, createWebHashHistory } from 'vue-router'

// hash 路由：无需 nginx 的 SPA history 回退配置，部署更简单。
const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/course-resources', name: 'course-resources', component: () => import('../views/CourseResourcesView.vue') },
  { path: '/class-management', name: 'class-management', component: () => import('../views/ClassManagementView.vue') },
  { path: '/aigc', name: 'aigc', component: () => import('../views/AigcView.vue') },
  { path: '/homework-correction', name: 'homework-correction', component: () => import('../views/HomeworkCorrectionView.vue') },
  { path: '/personal-setting', name: 'personal-setting', component: () => import('../views/PersonalSettingView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
