<template>
  <RouterLink
    :to="item.to"
    custom
    v-slot="{ isActive, navigate }"
  >
    <button
      @click="navigate"
      class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative"
      :class="[
        isActive
          ? 'bg-brand-500/15 text-white'
          : 'text-gray-500 hover:text-gray-200 hover:bg-dark-600'
      ]"
    >
      <!-- Active indicator bar -->
      <div
        v-if="isActive"
        class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r-full bg-brand-400"
      />

      <!-- Icon wrapper -->
      <div
        class="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200"
        :class="isActive
          ? `bg-gradient-to-br ${item.color} shadow-glow-sm`
          : 'bg-dark-500 group-hover:bg-dark-400'"
      >
        <div class="w-4 h-4" :class="isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'" v-html="item.icon" />
      </div>

      <!-- Label -->
      <Transition name="label">
        <span v-if="!collapsed" class="text-sm font-medium whitespace-nowrap overflow-hidden">
          {{ item.label }}
        </span>
      </Transition>

      <!-- Tooltip when collapsed -->
      <div
        v-if="collapsed"
        class="absolute left-full ml-3 px-2.5 py-1 bg-dark-600 text-gray-100 text-xs rounded-lg
               whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none
               transition-opacity duration-150 shadow-card z-50 border border-dark-400"
      >
        {{ item.label }}
      </div>
    </button>
  </RouterLink>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  item:      { type: Object,  required: true },
  collapsed: { type: Boolean, default: false },
})
</script>

<style scoped>
.label-enter-active, .label-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.label-enter-from, .label-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}
</style>
