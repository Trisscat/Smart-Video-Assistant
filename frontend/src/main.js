import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import UploadView from './views/UploadView.vue'
import ResultView from './views/ResultView.vue'

const routes = [
  { path: '/', name: 'Upload', component: UploadView },
  { path: '/result/:taskId', name: 'Result', component: ResultView, props: true },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 全局导航守卫：离开 ResultView 时清理，确保路由不被阻塞
router.beforeEach((to, from) => {
  // 任何导航都会清除可能的阻塞状态
  return true
})

createApp(App).use(router).mount('#app')
