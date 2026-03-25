<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 glass">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        </div>
        <div class="flex-1">
          <h1 class="text-sm font-semibold text-white">Progress Tracker</h1>
          <p class="text-xs text-gray-500">Visualize your academic performance across terms</p>
        </div>
        <button @click="exportCsv" class="btn-ghost text-xs gap-1.5">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Export CSV
        </button>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6">
      <!-- Chart -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-white">Performance Overview</h2>
          <div class="flex gap-2 flex-wrap">
            <span v-for="(color, label) in legendColors" :key="label"
              class="flex items-center gap-1.5 text-xs text-gray-400">
              <span class="w-3 h-0.5 rounded-full" :style="`background:${color}`" />
              {{ label }}
            </span>
          </div>
        </div>
        <div class="h-64">
          <Line v-if="chartData.labels.length" :data="chartData" :options="chartOptions" />
          <div v-else class="h-full flex items-center justify-center text-gray-600 text-sm">
            Add subjects and scores to see the chart
          </div>
        </div>
      </div>

      <!-- Terms management -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-white">Terms</h2>
          <button @click="addTerm" :disabled="terms.length >= 6" class="btn-ghost text-xs gap-1.5">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Term
          </button>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="(term, ti) in terms" :key="term.id"
            class="card-sm space-y-3 animate-fade-in"
          >
            <!-- Term name + remove -->
            <div class="flex items-center gap-2">
              <input
                v-model="term.name"
                class="input flex-1 text-sm py-1.5"
                placeholder="Term name"
              />
              <button v-if="terms.length > 2" @click="removeTerm(term.id)" class="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded-md hover:bg-red-500/10">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <!-- Subjects input -->
            <div>
              <label class="label text-[10px]">Subjects (comma-sep)</label>
              <input
                :value="subjectStr(term)"
                @change="e => updateSubjects(term, e.target.value)"
                class="input text-xs py-1.5"
                placeholder="Math, Physics, DSA"
              />
            </div>

            <!-- Scores -->
            <div v-if="Object.keys(term.scores).length" class="space-y-1.5">
              <label class="label text-[10px]">Scores (0–100)</label>
              <div v-for="(score, subj) in term.scores" :key="subj" class="flex items-center gap-2">
                <span class="text-xs text-gray-400 w-24 truncate">{{ subj }}</span>
                <input
                  type="number" min="0" max="100"
                  :value="score"
                  @input="e => updateScore(term, subj, e.target.value)"
                  class="input flex-1 text-xs py-1 text-center"
                />
                <!-- Mini bar -->
                <div class="w-16 h-1.5 rounded-full bg-dark-400 overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-300"
                    :style="`width:${score}%; background:${scoreColor(score)}`" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'
import { useAppStore } from '../stores/app.js'
import { storeToRefs } from 'pinia'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const store = useAppStore()
const { terms } = storeToRefs(store)
const { addTerm, removeTerm } = store

// Palette for datasets
const PALETTE = ['#818cf8','#34d399','#f59e0b','#f472b6','#60a5fa','#a78bfa']

// All unique subjects across all terms
const allSubjects = computed(() => {
  const set = new Set()
  terms.value.forEach(t => Object.keys(t.scores).forEach(s => set.add(s)))
  return [...set]
})

const legendColors = computed(() => {
  const out = {}
  allSubjects.value.forEach((s, i) => { out[s] = PALETTE[i % PALETTE.length] })
  return out
})

const chartData = computed(() => {
  const labels = terms.value.map(t => t.name)
  const datasets = allSubjects.value.map((subj, i) => ({
    label:           subj,
    data:            terms.value.map(t => t.scores[subj] ?? null),
    borderColor:     PALETTE[i % PALETTE.length],
    backgroundColor: PALETTE[i % PALETTE.length] + '22',
    pointBackgroundColor: PALETTE[i % PALETTE.length],
    pointRadius:     5,
    pointHoverRadius:7,
    tension:         0.4,
    fill:            false,
    spanGaps:        true,
  }))
  return { labels, datasets }
})

const chartOptions = {
  responsive:          true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1a1a30',
      borderColor:     'rgba(99,102,241,0.3)',
      borderWidth:     1,
      titleColor:      '#e2e2ff',
      bodyColor:       '#9494c0',
      padding:         10,
    },
  },
  scales: {
    x: {
      grid:   { color: 'rgba(255,255,255,0.04)' },
      ticks:  { color: '#6b7280' },
    },
    y: {
      min:    0,
      max:    100,
      grid:   { color: 'rgba(255,255,255,0.04)' },
      ticks:  { color: '#6b7280', stepSize: 20 },
    },
  },
}

function subjectStr(term) {
  return Object.keys(term.scores).join(', ')
}

function updateSubjects(term, val) {
  const subjects = val.split(',').map(s => s.trim()).filter(Boolean)
  const newScores = {}
  subjects.forEach(s => { newScores[s] = term.scores[s] ?? 0 })
  term.scores = newScores
}

function updateScore(term, subj, val) {
  term.scores[subj] = Math.max(0, Math.min(100, Number(val) || 0))
}

function scoreColor(score) {
  if (score >= 75) return '#34d399'
  if (score >= 50) return '#f59e0b'
  return '#f87171'
}

function exportCsv() {
  const subjects = allSubjects.value
  const header   = ['Term', ...subjects].join(',')
  const rows     = terms.value.map(t =>
    [t.name, ...subjects.map(s => t.scores[s] ?? '')].join(',')
  )
  const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'progress.csv'; a.click()
  URL.revokeObjectURL(url)
}
</script>
