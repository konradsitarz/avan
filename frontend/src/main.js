import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from './App.vue'
import BriefingView from './views/BriefingView.vue'
import FeedView from './views/FeedView.vue'
import TimelineView from './views/TimelineView.vue'
import RespondView from './views/RespondView.vue'
import RulesView from './views/RulesView.vue'

const routes = [
  { path: '/', redirect: '/briefing' },
  { path: '/briefing', component: BriefingView },
  { path: '/feed', component: FeedView },
  { path: '/timeline', component: TimelineView },
  { path: '/respond', component: RespondView },
  { path: '/rules', component: RulesView },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
