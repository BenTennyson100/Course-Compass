<template>
  <aside
    class="fixed left-0 top-0 h-full z-40 flex flex-col transition-all duration-300 select-none"
    :class="open ? 'w-60' : 'w-16'"
    style="background: rgba(8,8,15,0.97); border-right: 1px solid rgba(99,102,241,0.1);"
  >
    <!-- Header -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-dark-400/50">
      <!-- Compass Logo -->
      <div class="shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-glow-sm">
        <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
        </svg>
      </div>
      <Transition name="label">
        <div v-if="open" class="overflow-hidden">
          <p class="text-sm font-bold text-white whitespace-nowrap leading-tight">Course Compass</p>
          <p class="text-[10px] text-gray-500 whitespace-nowrap">AI Study Assistant</p>
        </div>
      </Transition>
      <!-- Collapse toggle -->
      <button
        @click="store.toggleSidebar()"
        class="ml-auto p-1.5 rounded-md text-gray-500 hover:text-gray-200 hover:bg-dark-500 transition-colors shrink-0"
      >
        <svg class="w-4 h-4 transition-transform duration-300" :class="open ? '' : 'rotate-180'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto no-scrollbar">
      <NavItem v-for="item in visibleNavItems" :key="item.to"
        :item="item" :collapsed="!open"
      />
    </nav>

    <!-- Footer -->
    <div class="px-3 py-3 border-t border-dark-400/50 space-y-2">
      <!-- Ollama status -->
      <div v-if="open" class="flex items-center gap-2.5 px-2">
        <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow shrink-0" />
        <span class="text-xs text-gray-500 truncate">Ollama Connected</span>
      </div>
      <div v-else class="flex justify-center">
        <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow" />
      </div>

      <!-- User info + logout -->
      <div v-if="authUser" class="flex items-center gap-2 px-1 pt-1">
        <img
          :src="authUser.picture"
          :alt="authUser.name"
          class="w-7 h-7 rounded-full shrink-0 ring-1 ring-brand-500/40"
        />
        <Transition name="label">
          <div v-if="open" class="flex-1 min-w-0">
            <p class="text-xs font-medium text-gray-300 truncate">{{ authUser.name }}</p>
            <p class="text-[10px] text-gray-600 truncate">{{ authUser.email }}</p>
          </div>
        </Transition>
        <Transition name="label">
          <button
            v-if="open"
            @click="handleLogout"
            title="Sign out"
            class="shrink-0 p-1 rounded-md text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </Transition>
      </div>
    </div>
  </aside>

  <!-- Overlay mobile -->
  <div v-if="open" class="fixed inset-0 z-30 lg:hidden" @click="open = false" />
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import NavItem from './NavItem.vue'
import { useAppStore } from '../stores/app.js'
import { useAuthStore } from '../stores/auth.js'

const store    = useAppStore()
const auth     = useAuthStore()
const router   = useRouter()
const authUser = computed(() => auth.user)

function handleLogout() {
  auth.logout()
  router.replace('/login')
}

const open  = computed({
  get: ()  => store.sidebarOpen,
  set: (v) => { store.sidebarOpen = v },
})
const route = useRoute()

// Hide the "Home" nav item when the user is already on the dashboard
const visibleNavItems = computed(() =>
  route.path === '/'
    ? navItems.filter(item => item.to !== '/')
    : navItems
)

const navItems = [
  {
    to: '/',
    label: 'Home',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
    </svg>`,
    color: 'from-brand-500 to-violet-500',
  },
  {
    to: '/chat',
    label: 'Chat',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>`,
    color: 'from-indigo-500 to-brand-500',
  },
  {
    to: '/planner',
    label: 'Study Planner',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>`,
    color: 'from-emerald-500 to-teal-500',
  },
  {
    to: '/progress',
    label: 'Progress',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>`,
    color: 'from-cyan-500 to-blue-500',
  },
  {
    to: '/quiz',
    label: 'Quiz Generator',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>`,
    color: 'from-amber-500 to-orange-500',
  },
  {
    to: '/notes',
    label: 'Note Taker',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>`,
    color: 'from-pink-500 to-rose-500',
  },
  {
    to: '/recommend',
    label: 'Course Advisor',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>`,
    color: 'from-violet-500 to-purple-600',
  },
]
</script>

<style scoped>
.label-enter-active, .label-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.label-enter-from, .label-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}
</style>
