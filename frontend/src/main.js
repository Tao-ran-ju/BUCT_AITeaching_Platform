import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import { readTokenFromUrl } from './composables/useAuth'

import './styles/base.css'
import './styles/theme.css'
import './styles/global.css'

// 学生端 SSO 免登跳转到教师端时携带 ?token=<JWT>，先落库再抹掉地址栏参数。
readTokenFromUrl()

const app = createApp(App)
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
