<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 glass">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
          <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        </div>
        <div>
          <h1 class="text-sm font-semibold text-white">Study Planner</h1>
          <p class="text-xs text-gray-500">Generate a personalized weekly schedule</p>
        </div>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto">
      <div class="grid lg:grid-cols-[380px_1fr] h-full">
        <!-- Left: Form -->
        <div class="border-r border-dark-400/50 p-6 space-y-5 overflow-y-auto">
          <!-- Subjects -->
          <div>
            <label class="label">Subjects</label>
            <input v-model="form.subjects" class="input" placeholder="e.g. Math, Physics, DSA, DBMS" />
            <p class="text-xs text-gray-500 mt-1">Separate with commas</p>
          </div>

          <!-- Grades -->
          <div>
            <label class="label">Subject Grades <span class="normal-case font-normal text-gray-500">(optional)</span></label>
            <input v-model="form.grades" class="input" placeholder="e.g. Math: 70, Physics: 85" />
            <p class="text-xs text-gray-500 mt-1">Lower grades get more time slots</p>
          </div>

          <!-- Days -->
          <div>
            <label class="label">Study Days</label>
            <div class="grid grid-cols-4 gap-1.5">
              <button
                v-for="d in allDays" :key="d"
                @click="toggleDay(d)"
                class="py-2 rounded-lg text-xs font-medium transition-all duration-200 border"
                :class="form.days.includes(d)
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                  : 'bg-dark-600 text-gray-400 border-dark-400 hover:border-dark-300'"
              >{{ d.slice(0, 3) }}</button>
            </div>
          </div>

          <!-- Generate -->
          <button
            @click="generate"
            :disabled="!form.subjects.trim() || isLoading"
            class="btn-primary w-full justify-center py-3"
            style="background: linear-gradient(135deg, #10b981, #0d9488);"
          >
            <svg v-if="!isLoading" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3l14 9-14 9V3z"/></svg>
            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
            {{ isLoading ? 'Generating…' : 'Generate Schedule' }}
          </button>
        </div>

        <!-- Right: Output -->
        <div class="p-6 overflow-y-auto">
          <!-- Placeholder -->
          <div v-if="!output && !isLoading" class="flex flex-col items-center justify-center h-full text-center opacity-40">
            <svg class="w-16 h-16 text-gray-600 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            <p class="text-gray-500 text-sm">Your schedule will appear here</p>
          </div>

          <!-- Loading skeleton -->
          <div v-if="isLoading && !output" class="space-y-3 animate-pulse">
            <div v-for="i in 6" :key="i" class="h-10 rounded-lg bg-dark-600" :style="`width: ${70 + (i % 3) * 10}%`" />
          </div>

          <!-- Output -->
          <div v-if="output" class="animate-fade-in">
            <div class="flex items-center justify-between mb-4">
              <span class="badge-success">Schedule Ready</span>
              <button @click="downloadTxt" class="btn-ghost text-xs gap-1.5">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download .txt
              </button>
            </div>
            <div class="card bg-dark-800">
              <pre class="text-sm text-gray-200 whitespace-pre-wrap font-mono leading-relaxed"><span>{{ output }}</span><span v-if="isLoading" class="cursor-blink" /></pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { streamFetch } from '../utils/stream.js'
import { useAuthStore } from '../stores/auth.js'

const auth    = useAuthStore()
const allDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

const form = reactive({
  subjects: '',
  grades: '',
  days: ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
})

const output    = ref('')
const isLoading = ref(false)

function toggleDay(d) {
  const i = form.days.indexOf(d)
  if (i === -1) form.days.push(d)
  else form.days.splice(i, 1)
}

async function generate() {
  if (!form.subjects.trim()) return
  output.value    = ''
  isLoading.value = true

  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}

  await streamFetch(
    '/api/planner',
    { subjects: form.subjects, grades: form.grades, days: form.days },
    (token) => { output.value += token },
    () => {
      isLoading.value = false
      // Save subjects as interests in memory
      if (form.subjects.trim()) {
        auth.upsertMemory({ interests: form.subjects.trim() })
      }
    },
    (err) => { output.value = `Error: ${err}`; isLoading.value = false },
    authHeader,
  )
}

function downloadTxt() {
  const blob = new Blob([output.value], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'study_schedule.txt'; a.click()
  URL.revokeObjectURL(url)
}
</script>
