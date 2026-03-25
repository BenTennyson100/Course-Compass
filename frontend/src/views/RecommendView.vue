<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 glass flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      </div>
      <div>
        <h1 class="text-sm font-semibold text-white">Course Advisor</h1>
        <p class="text-xs text-gray-500">Get a personalized learning roadmap</p>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-hidden grid lg:grid-cols-[340px_1fr]">
      <!-- Left: Form -->
      <div class="border-r border-dark-400/50 p-5 space-y-5 overflow-y-auto">
        <div>
          <label class="label">Topic / Skill *</label>
          <input v-model="form.topic" class="input" placeholder="e.g. Machine Learning, React, DevOps" />
        </div>

        <div>
          <label class="label">Current Level</label>
          <div class="space-y-1.5">
            <button v-for="lvl in levels" :key="lvl.id"
              @click="form.level = lvl.id"
              class="w-full flex items-center gap-3 px-3 py-3 rounded-lg border text-left transition-all duration-200"
              :class="form.level === lvl.id
                ? 'bg-violet-500/15 border-violet-500/40 text-violet-300'
                : 'bg-dark-700 border-dark-400 text-gray-400 hover:border-dark-300'"
            >
              <span class="text-lg">{{ lvl.emoji }}</span>
              <div>
                <p class="text-xs font-semibold leading-tight">{{ lvl.label }}</p>
                <p class="text-[10px] text-gray-500">{{ lvl.desc }}</p>
              </div>
            </button>
          </div>
        </div>

        <div>
          <label class="label">Weekly Commitment</label>
          <div class="space-y-1.5">
            <button v-for="hrs in hourOptions" :key="hrs.id"
              @click="form.weeklyHours = hrs.id"
              class="w-full flex items-center gap-3 px-3 py-2 rounded-lg border text-left transition-all duration-200"
              :class="form.weeklyHours === hrs.id
                ? 'bg-violet-500/15 border-violet-500/40 text-violet-300'
                : 'bg-dark-700 border-dark-400 text-gray-400 hover:border-dark-300'"
            >
              <span class="text-base">{{ hrs.emoji }}</span>
              <span class="text-xs font-medium">{{ hrs.label }}</span>
            </button>
          </div>
        </div>

        <button @click="generate" :disabled="!form.topic.trim() || isLoading" class="btn-primary w-full justify-center py-3"
          style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);">
          <svg v-if="!isLoading" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ isLoading ? 'Building Roadmap…' : 'Generate Roadmap' }}
        </button>
      </div>

      <!-- Right: Output -->
      <div class="overflow-y-auto p-6">
        <!-- Empty state -->
        <div v-if="!output && !isLoading" class="flex flex-col items-center justify-center h-full text-center opacity-40">
          <svg class="w-14 h-14 text-gray-600 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <p class="text-gray-500 text-sm">Your learning roadmap will appear here</p>
        </div>

        <!-- Loading skeleton -->
        <div v-if="isLoading && !output" class="space-y-3 animate-pulse">
          <div v-for="i in 8" :key="i" class="h-4 rounded-lg bg-dark-600" :style="`width:${50+Math.random()*45}%`" />
        </div>

        <!-- Output: rendered sections -->
        <div v-if="output" class="space-y-4 animate-fade-in">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-white">{{ form.topic }} <span class="text-gradient">Roadmap</span></h2>
            <button @click="downloadTxt" class="btn-ghost text-xs gap-1.5">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download
            </button>
          </div>

          <!-- Week sections (collapsible) -->
          <div v-for="(sec, i) in parsedSections" :key="i">
            <!-- Week section -->
            <div v-if="sec.isWeek" class="card mb-0 cursor-pointer hover:border-brand-500/30 transition-all duration-200"
              @click="sec.open = !sec.open">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                    :style="`background: linear-gradient(135deg, ${weekColor(i)}, ${weekColor(i+1)}22);`">
                    {{ sec.weekNum || i + 1 }}
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-white">{{ sec.title }}</p>
                    <p class="text-xs text-gray-500">{{ sec.bullets.length }} items</p>
                  </div>
                </div>
                <svg class="w-4 h-4 text-gray-500 transition-transform duration-200" :class="sec.open ? 'rotate-180' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              <Transition name="expand">
                <ul v-if="sec.open" class="mt-3 space-y-1.5 border-t border-dark-400/50 pt-3">
                  <li v-for="(b, bi) in sec.bullets" :key="bi"
                    class="flex items-start gap-2 text-sm text-gray-300">
                    <span class="text-violet-400 mt-0.5 shrink-0">•</span>
                    <span v-html="linkify(b)" />
                  </li>
                </ul>
              </Transition>
            </div>

            <!-- Special section (Resources, Projects, etc.) -->
            <div v-else class="card">
              <h3 class="text-sm font-bold text-violet-300 mb-3">{{ sec.title }}</h3>
              <ul class="space-y-1.5">
                <li v-for="(b, bi) in sec.bullets" :key="bi" class="flex items-start gap-2 text-sm text-gray-300">
                  <span class="text-violet-400 mt-0.5 shrink-0">•</span>
                  <span v-html="linkify(b)" />
                </li>
              </ul>
            </div>
          </div>

          <!-- Raw fallback -->
          <div v-if="!parsedSections.length" class="card bg-dark-800">
            <pre class="text-sm text-gray-200 whitespace-pre-wrap font-sans leading-relaxed">{{ output }}<span v-if="isLoading" class="cursor-blink" /></pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { streamFetch } from '../utils/stream.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

const form = reactive({ topic:'', level:'Beginner', weeklyHours:'5-8 hrs' })
const output    = ref('')
const isLoading = ref(false)

const levels = [
  { id:'Beginner',     emoji:'🌱', label:'Beginner',     desc:'Little or no experience'     },
  { id:'Intermediate', emoji:'🚀', label:'Intermediate', desc:'Some hands-on experience'    },
  { id:'Advanced',     emoji:'⚡', label:'Advanced',     desc:'Strong foundation, deepening' },
]

const hourOptions = [
  { id:'2-4 hrs',  emoji:'🕐', label:'2–4 hrs/week  (Casual)'  },
  { id:'5-8 hrs',  emoji:'🕓', label:'5–8 hrs/week  (Regular)' },
  { id:'8-12 hrs', emoji:'🕗', label:'8–12 hrs/week (Focused)' },
  { id:'12+ hrs',  emoji:'🔥', label:'12+ hrs/week  (Intensive)' },
]

const WEEK_COLORS = ['#818cf8','#34d399','#f59e0b','#f472b6','#60a5fa','#a78bfa','#fb923c','#2dd4bf']

function weekColor(i) { return WEEK_COLORS[i % WEEK_COLORS.length] }

async function generate() {
  if (!form.topic.trim()) return
  output.value = ''
  isLoading.value = true

  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}

  await streamFetch(
    '/api/recommend',
    { topic: form.topic, level: form.level, weekly_hours: form.weeklyHours },
    (token) => { output.value += token },
    () => {
      isLoading.value = false
      // Capture topic + level directly from user's explicit choices
      auth.upsertMemory({
        interests:      form.topic.trim(),
        expertise_level: form.level.toLowerCase(),
      })
    },
    (err) => { output.value = `Error: ${err}`; isLoading.value = false },
    authHeader,
  )
}

const parsedSections = computed(() => {
  if (!output.value) return []
  const sections = []
  const lines    = output.value.split('\n')
  let   current  = null

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) continue

    // Week header: ### Week N: Title  or  ## Week N ...
    const weekMatch = line.match(/^#{1,3}\s*Week\s*(\d+)\s*[:\-]?\s*(.*)$/i)
    if (weekMatch) {
      if (current) sections.push(current)
      current = { isWeek: true, weekNum: parseInt(weekMatch[1]), title: `Week ${weekMatch[1]}: ${weekMatch[2]}`.trim(), bullets: [], open: true }
      continue
    }

    // Special section header
    const secMatch = line.match(/^#{1,3}\s*(.+)$/)
    if (secMatch && !line.startsWith('-') && !line.startsWith('*')) {
      if (current) sections.push(current)
      current = { isWeek: false, title: secMatch[1].replace(/\*\*/g,'').trim(), bullets: [], open: true }
      continue
    }

    // Bullet
    const bullet = line.replace(/^[-*•]\s*/, '').replace(/^\d+\.\s*/, '').trim()
    if (bullet && current) {
      current.bullets.push(bullet)
    } else if (bullet && !current) {
      current = { isWeek: false, title: 'Overview', bullets: [bullet], open: true }
    }
  }
  if (current) sections.push(current)
  return sections.filter(s => s.bullets.length > 0)
})

function linkify(text) {
  // Convert URLs to clickable links
  return text
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-dark-600 text-violet-300 px-1 rounded text-xs font-mono">$1</code>')
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener" class="text-brand-400 hover:text-brand-300 underline underline-offset-2 break-all">$1</a>')
}

function downloadTxt() {
  const blob = new Blob([output.value], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = `${form.topic.replace(/\s+/g,'-')}_roadmap.txt`; a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.expand-enter-active, .expand-leave-active { transition: opacity 0.2s, transform 0.2s; }
.expand-enter-from, .expand-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
