import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken } from '../api/client'
import LoginPage from '../views/LoginPage.vue'
import HomePage from '../views/HomePage.vue'
import ContentStudioPage from '../views/ContentStudioPage.vue'
import PublishWorkspacePage from '../views/PublishWorkspacePage.vue'
import RecordsPage from '../views/RecordsPage.vue'
import AccountsPage from '../views/AccountsPage.vue'
import ProfilePage from '../views/ProfilePage.vue'

const routes = [
  { path: '/login', component: LoginPage, meta: { title: '登录' } },
  { path: '/', component: HomePage, meta: { title: '首页' } },
  { path: '/content', component: ContentStudioPage, meta: { title: '内容准备' } },
  { path: '/publish', component: PublishWorkspacePage, meta: { title: '发布中心' } },
  { path: '/records', component: RecordsPage, meta: { title: '执行记录' } },
  { path: '/accounts', component: AccountsPage, meta: { title: '账号管理' } },
  { path: '/profile', component: ProfilePage, meta: { title: '个人中心' } }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to) => {
  const authed = Boolean(getToken())
  if (!authed && to.path !== '/login') return '/login'
  if (authed && to.path === '/login') return '/'
  document.title = `${to.meta.title || '用户端'} - 自媒体自动发布`
  return true
})

export default router
