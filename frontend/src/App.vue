<template>
  <!-- Auth pages (login / callback) — no sidebar -->
  <div v-if="isPublicRoute" class="min-h-screen bg-mesh">
    <RouterView />
  </div>

  <!-- App shell with sidebar -->
  <div v-else class="flex h-screen bg-mesh overflow-hidden">
    <Sidebar />
    <div
      class="flex-1 flex flex-col overflow-hidden transition-all duration-300"
      :style="{ marginLeft: sidebarOpen ? '240px' : '64px' }"
    >
      <TopBar />
      <main class="flex-1 min-h-0 overflow-hidden">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TopBar  from './components/TopBar.vue'
import { useAppStore } from './stores/app.js'

const store       = useAppStore()
const route       = useRoute()
const sidebarOpen = computed(() => store.sidebarOpen)
const isPublicRoute = computed(() => !!route.meta?.public)
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
