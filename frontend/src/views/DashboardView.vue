<template>
  <div class="h-full overflow-y-auto flex flex-col items-center justify-center gap-4 py-5 px-4 bg-mesh relative">

    <!-- Ambient background blobs -->
    <div class="pointer-events-none fixed inset-0 overflow-hidden">
      <div class="absolute top-[-10%] left-[10%] w-[400px] h-[400px] rounded-full blur-[120px]"
        style="background: radial-gradient(circle, rgba(99,102,241,0.07), transparent 70%);" />
      <div class="absolute bottom-[-5%] right-[10%] w-[360px] h-[360px] rounded-full blur-[120px]"
        style="background: radial-gradient(circle, rgba(139,92,246,0.07), transparent 70%);" />
    </div>

    <!-- ── Welcome Header ────────────────────────────────── -->
    <div class="text-center animate-fade-in relative z-10 flex-shrink-0">
      <p class="text-[10px] text-gray-500 tracking-[0.25em] uppercase mb-1.5">Welcome to</p>
      <h1 class="text-4xl font-extrabold leading-none tracking-tight">
        <span class="text-gradient">Course Compass</span>
      </h1>
      <p class="text-gray-500 text-xs mt-1.5">Click any feature to get started</p>
    </div>

    <!-- ── Compass Arena ──────────────────────────────────── -->
    <div
      class="relative flex-shrink-0 animate-fade-in"
      style="
        width: min(440px, calc(100% - 32px));
        aspect-ratio: 1;
        animation-delay: 0.15s;
      "
    >
      <!-- SVG layer — background rings, connecting lines, animated dots, pulsing nodes -->
      <svg
        class="absolute inset-0 w-full h-full"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
        style="overflow: visible;"
      >
        <!-- Outer decorative dashed rings -->
        <circle cx="300" cy="300" r="245" fill="none" stroke="#1e1e38" stroke-width="1" stroke-dasharray="3 9" />
        <circle cx="300" cy="300" r="175" fill="none" stroke="#1a1a30" stroke-width="1" stroke-dasharray="2 14" />
        <circle cx="300" cy="300" r="110" fill="none" stroke="#161628" stroke-width="1" stroke-dasharray="2 18" />

        <!-- Connecting lines: center → each feature -->
        <line
          v-for="f in features" :key="`line-${f.to}`"
          x1="300" y1="300"
          :x2="f.svgX" :y2="f.svgY"
          :stroke="f.color"
          stroke-width="1.2"
          stroke-opacity="0.2"
          stroke-dasharray="5 6"
        />

        <!-- Animated traveling dot on each line -->
        <circle v-for="(f, i) in features" :key="`dot-${f.to}`" r="2.5" :fill="f.color" opacity="0.85">
          <animateMotion
            :path="`M 300 300 L ${f.svgX} ${f.svgY}`"
            :dur="`${1.6 + i * 0.35}s`"
            repeatCount="indefinite"
          />
        </circle>

        <!-- Glowing pulse ring at each feature node -->
        <circle
          v-for="(f, i) in features" :key="`pulse-${f.to}`"
          :cx="f.svgX" :cy="f.svgY"
          :fill="f.color"
        >
          <animate attributeName="r"       :values="`4;14;4`"     :dur="`${2.4 + i * 0.25}s`" repeatCount="indefinite" />
          <animate attributeName="opacity" :values="`0.25;0;0.25`" :dur="`${2.4 + i * 0.25}s`" repeatCount="indefinite" />
        </circle>
      </svg>

      <!-- ── Central Compass ── -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
        <!-- Outer soft glow -->
        <div class="absolute rounded-full animate-pulse-slow pointer-events-none"
          style="
            width: 140px; height: 140px;
            top: -30px; left: -30px;
            background: radial-gradient(circle, rgba(99,102,241,0.22) 0%, transparent 70%);
            filter: blur(16px);
          "
        />

        <!-- Compass body -->
        <div
          class="relative w-20 h-20 rounded-full flex items-center justify-center"
          style="
            background: radial-gradient(circle at 40% 35%, #1e1e38, #0a0a14);
            border: 1.5px solid rgba(99,102,241,0.45);
            box-shadow: 0 0 0 4px rgba(99,102,241,0.06), 0 0 24px rgba(99,102,241,0.2);
          "
        >
          <!-- Tick marks ring (static) -->
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 80 80">
            <g v-for="n in 24" :key="`tick-${n}`">
              <line
                :x1="40 + 37 * Math.cos((n * 15 - 90) * DEG)"
                :y1="40 + 37 * Math.sin((n * 15 - 90) * DEG)"
                :x2="40 + (n % 6 === 0 ? 30 : n % 2 === 0 ? 33 : 35) * Math.cos((n * 15 - 90) * DEG)"
                :y2="40 + (n % 6 === 0 ? 30 : n % 2 === 0 ? 33 : 35) * Math.sin((n * 15 - 90) * DEG)"
                :stroke="n % 6 === 0 ? '#818cf8' : '#3a3a5c'"
                :stroke-width="n % 6 === 0 ? 1.5 : 0.75"
                :opacity="n % 6 === 0 ? 0.9 : 0.5"
              />
            </g>
          </svg>

          <!-- Rotating compass rose -->
          <svg class="w-11 h-11 animate-spin-slow" viewBox="0 0 64 64">
            <!-- North — white -->
            <polygon points="32,3  29,32  32,24  35,32" fill="white"   opacity="0.95"/>
            <!-- South — brand violet -->
            <polygon points="32,61 29,32  32,40  35,32" fill="#818cf8" opacity="0.90"/>
            <!-- East  — dim -->
            <polygon points="61,32 32,29  40,32  32,35" fill="#3a3a6a" opacity="0.75"/>
            <!-- West  — dim -->
            <polygon points="3,32  32,29  24,32  32,35" fill="#3a3a6a" opacity="0.75"/>
            <!-- NE / SE / SW / NW — tiny intercardinal -->
            <polygon points="53,11 32,32 49,28 28,49" fill="#1e1e35" opacity="0.55"/>
            <polygon points="53,53 32,32 49,36 28,15" fill="#1e1e35" opacity="0.55"/>
            <polygon points="11,53 32,32 15,36 36,15" fill="#1e1e35" opacity="0.55"/>
            <polygon points="11,11 32,32 15,28 36,49" fill="#1e1e35" opacity="0.55"/>
            <!-- Center jewel -->
            <circle cx="32" cy="32" r="3.5" fill="#6366f1"/>
            <circle cx="32" cy="32" r="1.8" fill="white"/>
          </svg>
        </div>

        <!-- "CC" label below -->
        <p class="text-center text-[9px] font-bold tracking-widest text-gray-600 mt-1.5 uppercase">COMPASS</p>
      </div>

      <!-- ── Feature Cards ─────────────────────────────── -->
      <RouterLink
        v-for="(f, i) in features"
        :key="f.to"
        :to="f.to"
        class="absolute z-10 group animate-fade-in cursor-pointer"
        :style="{
          width:          '62px',
          height:         '62px',
          left:           '50%',
          top:            '50%',
          marginLeft:     `calc(${f.cosA} * 33.333% - 31px)`,
          marginTop:      `calc(${f.sinA} * 33.333% - 31px)`,
          animationDelay: (0.2 + i * 0.08) + 's',
        }"
        @mouseenter="hovered = i"
        @mouseleave="hovered = -1"
      >
        <!-- ── Icon card — 62×62px, its center is EXACTLY at cssX%,cssY% ── -->
        <div
          class="w-full h-full rounded-2xl flex items-center justify-center border transition-all duration-300 relative overflow-hidden"
          :style="{
            background:  `${f.color}13`,
            borderColor: `${f.color}45`,
            transform:   hovered === i ? 'scale(1.18)' : 'scale(1)',
            boxShadow:   hovered === i
              ? `0 0 0 1px ${f.color}40, 0 8px 32px ${f.color}50, 0 0 0 10px ${f.color}08`
              : `0 2px 12px rgba(0,0,0,0.45)`,
          }"
        >
          <!-- Radial inner glow -->
          <div
            class="absolute inset-0 rounded-2xl transition-opacity duration-300"
            :style="{
              background: `radial-gradient(circle at 40% 35%, ${f.color}30, transparent 65%)`,
              opacity: hovered === i ? 1 : 0.45,
            }"
          />
          <!-- SVG icon -->
          <div
            class="relative w-[22px] h-[22px] transition-all duration-300 pointer-events-none"
            :style="{
              color:  f.color,
              filter: hovered === i ? `drop-shadow(0 0 7px ${f.color}bb)` : 'none',
            }"
            v-html="f.icon"
          />
        </div>

        <!-- ── Label — absolutely below the icon, does NOT affect centering ── -->
        <div
          class="absolute left-1/2 -translate-x-1/2 whitespace-nowrap
                 text-[10px] font-semibold pointer-events-none
                 transition-all duration-300 select-none"
          style="top: calc(100% + 5px);"
          :style="{
            color:       hovered === i ? f.color : f.color + 'bb',
            textShadow:  hovered === i ? `0 0 10px ${f.color}88` : 'none',
            letterSpacing: '0.03em',
          }"
        >
          {{ f.label }}
        </div>
      </RouterLink>
    </div>

    <!-- ── Stats Bar ───────────────────────────────────── -->
    <div
      class="flex gap-2 flex-wrap justify-center animate-fade-in relative z-10 flex-shrink-0"
      style="animation-delay: 0.65s;"
    >
      <div
        v-for="s in stats" :key="s.label"
        class="flex items-center gap-2 px-3 py-1.5 rounded-full border"
        style="background: rgba(20,20,36,0.8); border-color: rgba(99,102,241,0.12);"
      >
        <span class="text-sm">{{ s.emoji }}</span>
        <div>
          <p class="text-[11px] font-bold text-white leading-none">{{ s.value }}</p>
          <p class="text-[9px] text-gray-500 leading-none mt-0.5">{{ s.label }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const hovered  = ref(-1)
const DEG      = Math.PI / 180
const RADIUS   = 200
const SVG_SIZE = 600

// Feature definitions — angle is degrees from top, going clockwise
const FEATURES_RAW = [
  {
    label: 'Chat',
    to:    '/chat',
    angle: -90,
    color: '#818cf8',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  },
  {
    label: 'Study Planner',
    to:    '/planner',
    angle: -30,
    color: '#34d399',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
  },
  {
    label: 'Progress',
    to:    '/progress',
    angle: 30,
    color: '#22d3ee',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  },
  {
    label: 'Quiz',
    to:    '/quiz',
    angle: 90,
    color: '#fbbf24',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  },
  {
    label: 'Note Taker',
    to:    '/notes',
    angle: 150,
    color: '#f472b6',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  },
  {
    label: 'Course Advisor',
    to:    '/recommend',
    angle: 210,
    color: '#c084fc',
    icon:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  },
]

// cosA/sinA are static — CSS margin percentages (always width-relative) handle the rest
const features = FEATURES_RAW.map(f => {
  const rad  = f.angle * DEG
  const cosA = Math.cos(rad)
  const sinA = Math.sin(rad)
  return {
    ...f,
    svgX: 300 + cosA * RADIUS,
    svgY: 300 + sinA * RADIUS,
    cosA,
    sinA,
  }
})

const stats = [
  { emoji: '🤖', value: 'AI-Powered',  label: 'Local Ollama LLM'   },
  { emoji: '📚', value: '6 Tools',     label: 'Study features'     },
  { emoji: '🔒', value: '100% Local',  label: 'No data leaves you' },
  { emoji: '⚡', value: 'Streaming',   label: 'Real-time responses' },
]
</script>

<style scoped>
/* Ensure the fade-in animation respects the delay set inline */
.animate-fade-in {
  animation-fill-mode: both;
}
</style>
