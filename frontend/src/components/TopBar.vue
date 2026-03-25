<template>
  <div
    class="shrink-0 flex items-center gap-6 px-5 border-b border-dark-400/40 select-none"
    style="height: 72px; background: rgba(6,6,12,0.97);"
  >

    <!-- ── Level Progress ─────────────────────────────────────── -->
    <div class="flex flex-col justify-center gap-1 min-w-[220px] max-w-[300px]">
      <div class="flex items-center justify-between">
        <span class="text-[9px] font-semibold uppercase tracking-widest text-gray-600">Learning Level</span>
        <span class="text-[11px] font-bold tracking-wide" :class="levelMeta.textColor">
          {{ levelMeta.label }}
        </span>
      </div>

      <!-- Bar -->
      <div class="relative h-1.5 rounded-full bg-dark-600 overflow-visible">
        <!-- Fill -->
        <div
          class="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
          :style="`width: ${levelMeta.pct}%; background: linear-gradient(90deg, ${levelMeta.from}, ${levelMeta.to})`"
        />
        <!-- Milestone dots -->
        <div v-for="m in MILESTONES" :key="m.pct"
          class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full border-2 transition-all duration-700"
          :style="`left: ${m.pct}%`"
          :class="levelMeta.pct >= m.pct
            ? 'border-transparent'
            : 'bg-dark-600 border-dark-400'"
          :style2="levelMeta.pct >= m.pct ? `background: ${levelMeta.to}` : ''"
          v-bind="levelMeta.pct >= m.pct ? { style: `left:${m.pct}%; background:${m.color}; border-color:${m.color}` } : { style: `left:${m.pct}%` }"
        />
      </div>

      <!-- Stage labels -->
      <div class="flex justify-between">
        <span v-for="s in STAGES" :key="s.label"
          class="text-[9px] transition-colors duration-500"
          :class="levelMeta.label === s.label ? s.activeColor : 'text-gray-700'"
        >{{ s.label }}</span>
      </div>
    </div>

    <!-- ── Spacer ──────────────────────────────────────────────── -->
    <div class="flex-1" />

    <!-- ── Streak Map ─────────────────────────────────────────── -->
    <div class="flex items-center gap-3">
      <!-- Label + current streak count -->
      <div class="text-right hidden sm:block">
        <p class="text-[9px] font-semibold uppercase tracking-widest text-gray-600">Practice Streak</p>
        <p class="text-[11px] font-bold text-brand-400">
          {{ currentStreak }} <span class="text-gray-600 font-normal">day{{ currentStreak !== 1 ? 's' : '' }}</span>
        </p>
      </div>

      <!-- Grid: 5 weeks × 7 days -->
      <div class="flex gap-[3px] items-start">
        <!-- Day-of-week labels -->
        <div class="flex flex-col gap-[3px] mr-0.5">
          <span v-for="d in DAY_LABELS" :key="d"
            class="text-[8px] text-gray-700 leading-none flex items-center"
            style="height: 10px;"
          >{{ d }}</span>
        </div>

        <!-- Week columns -->
        <div v-for="(week, wi) in streakGrid" :key="wi" class="flex flex-col gap-[3px]">
          <div
            v-for="(cell, di) in week" :key="di"
            class="rounded-[2px] cursor-default transition-all duration-150"
            style="width: 10px; height: 10px;"
            :style="`background: ${cellColor(cell)}`"
            @mouseenter="e => showTooltip(e, cell)"
            @mouseleave="tooltip = null"
          />
        </div>
      </div>
    </div>

    <!-- ── Tooltip (teleported to body) ───────────────────────── -->
    <Teleport to="body">
      <Transition name="tip">
        <div
          v-if="tooltip"
          class="fixed z-[9999] px-3 py-2 rounded-xl pointer-events-none text-xs"
          style="background: rgba(10,10,20,0.97); border: 1px solid rgba(99,102,241,0.25); box-shadow: 0 8px 32px rgba(0,0,0,0.6);"
          :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px', transform: 'translateX(-50%) translateY(-115%)' }"
        >
          <p class="font-semibold text-white whitespace-nowrap">{{ tooltip.label }}</p>
          <p v-if="tooltip.active" class="text-[10px] mt-0.5 text-gray-300">
            {{ tooltip.count }} {{ tooltip.count === 1 ? 'activity' : 'activities' }}
            <span class="text-gray-500 ml-1">· {{ tooltip.types.join(' & ') }}</span>
          </p>
          <p v-else class="text-[10px] mt-0.5 text-gray-600">No activity</p>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// ── Constants ──────────────────────────────────────────────────────────────

const DAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

const MILESTONES = [
  { pct: 0,   color: '#34d399' },
  { pct: 50,  color: '#818cf8' },
  { pct: 100, color: '#a78bfa' },
]

const STAGES = [
  { label: 'Starter',      activeColor: 'text-emerald-400' },
  { label: 'Intermediate', activeColor: 'text-brand-400'   },
  { label: 'Advanced',     activeColor: 'text-violet-400'  },
]

const LEVEL_META = {
  beginner:     { label: 'Starter',      pct: 15,  from: '#34d399', to: '#6ee7b7', textColor: 'text-emerald-400' },
  intermediate: { label: 'Intermediate', pct: 55,  from: '#34d399', to: '#818cf8', textColor: 'text-brand-400'   },
  advanced:     { label: 'Advanced',     pct: 90,  from: '#34d399', to: '#a78bfa', textColor: 'text-violet-400'  },
  default:      { label: 'Starter',      pct: 5,   from: '#1e1e3f', to: '#374151', textColor: 'text-gray-600'    },
}

// ── Level ──────────────────────────────────────────────────────────────────

const levelMeta = computed(() => {
  const raw = auth.memoryMap?.expertise_level?.toLowerCase() ?? ''
  return LEVEL_META[raw] ?? LEVEL_META.default
})

// ── Streak grid ────────────────────────────────────────────────────────────

// Returns 5 columns (weeks) × 7 rows (Mon→Sun)
const streakGrid = computed(() => {
  const today  = new Date()
  // Find last Monday
  const dow    = today.getDay()          // 0=Sun … 6=Sat
  const toMon  = dow === 0 ? 6 : dow - 1 // days since last Monday
  const monday = new Date(today)
  monday.setDate(today.getDate() - toMon - 28)  // start 4 weeks before last Monday
  monday.setHours(0, 0, 0, 0)

  const weeks = []
  for (let w = 0; w < 5; w++) {
    const week = []
    for (let d = 0; d < 7; d++) {
      const date = new Date(monday)
      date.setDate(monday.getDate() + w * 7 + d)
      const dateStr   = date.toISOString().split('T')[0]
      const activity  = auth.activityMap[dateStr]
      const isFuture  = date > today
      week.push({
        date,
        dateStr,
        active:   !isFuture && !!activity,
        count:    activity?.count ?? 0,
        types:    activity?.types ?? [],
        isFuture,
      })
    }
    weeks.push(week)
  }
  return weeks
})

function cellColor(cell) {
  if (cell.isFuture) return 'rgba(255,255,255,0.03)'
  if (!cell.active)  return 'rgba(255,255,255,0.06)'
  if (cell.count <= 2) return 'rgba(99,102,241,0.35)'
  if (cell.count <= 5) return 'rgba(99,102,241,0.65)'
  return 'rgba(99,102,241,1)'
}

// Current streak = consecutive active days ending today
const currentStreak = computed(() => {
  let streak = 0
  const today = new Date()
  for (let i = 0; i < 60; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = d.toISOString().split('T')[0]
    if (auth.activityMap[key]) streak++
    else if (i > 0) break  // allow today to be empty (day not over yet)
  }
  return streak
})

// ── Tooltip ────────────────────────────────────────────────────────────────

const tooltip = ref(null)

function showTooltip(e, cell) {
  const date = cell.date
  const label = date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
  tooltip.value = {
    x:      e.clientX,
    y:      e.clientY,
    label,
    active: cell.active,
    count:  cell.count,
    types:  cell.types,
  }
}
</script>

<style scoped>
.tip-enter-active, .tip-leave-active { transition: opacity 0.12s, transform 0.12s; }
.tip-enter-from, .tip-leave-to { opacity: 0; transform: translateX(-50%) translateY(-105%); }
</style>
