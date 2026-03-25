import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

import LoginView        from '../views/LoginView.vue'
import AuthCallbackView from '../views/AuthCallbackView.vue'
import DashboardView    from '../views/DashboardView.vue'
import ChatView         from '../views/ChatView.vue'
import PlannerView      from '../views/PlannerView.vue'
import ProgressView     from '../views/ProgressView.vue'
import QuizView         from '../views/QuizView.vue'
import NotesView        from '../views/NotesView.vue'
import RecommendView    from '../views/RecommendView.vue'

const routes = [
  { path: '/login',         component: LoginView,        name: 'login',    meta: { public: true } },
  { path: '/auth/callback', component: AuthCallbackView, name: 'callback', meta: { public: true } },
  { path: '/',              component: DashboardView,    name: 'dashboard' },
  { path: '/chat',          component: ChatView,         name: 'chat'      },
  { path: '/planner',       component: PlannerView,      name: 'planner'   },
  { path: '/progress',      component: ProgressView,     name: 'progress'  },
  { path: '/quiz',          component: QuizView,         name: 'quiz'      },
  { path: '/notes',         component: NotesView,        name: 'notes'     },
  { path: '/recommend',     component: RecommendView,    name: 'recommend' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()

  // If we have a token but no user yet, try to fetch user first
  if (auth.token && !auth.user) {
    await auth.fetchUser()
  }

  if (!auth.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router
