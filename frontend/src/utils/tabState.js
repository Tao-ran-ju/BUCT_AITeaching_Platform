// 跨页 Tab 状态：用于「更多功能」归并后，跨页跳转到指定内部标签页。
import { reactive } from 'vue'

export const tabState = reactive({
  home: 'overview',          // 网站主页：overview / dashboard / warning
  courseResources: 'resources', // 课程资源：resources / discussion / team
  personalSetting: 'profile'    // 个人设置：profile / help
})

// 便捷：跳转到某页的指定标签（调用方自行 router.push 到对应路由）
export function switchTab(page, tab) {
  tabState[page] = tab
}
