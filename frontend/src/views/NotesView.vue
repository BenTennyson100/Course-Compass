<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 glass flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      </div>
      <div>
        <h1 class="text-sm font-semibold text-white">Note Taker</h1>
        <p class="text-xs text-gray-500">Process your lecture notes with AI</p>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-hidden grid lg:grid-cols-2">
      <!-- Left: Input -->
      <div class="flex flex-col border-r border-dark-400/50 p-5 space-y-4 overflow-y-auto">
        <div class="flex-1 flex flex-col">
          <label class="label">Raw Notes</label>
          <textarea
            v-model="rawNotes"
            class="textarea flex-1 min-h-[200px] font-mono text-xs leading-relaxed"
            placeholder="Paste your lecture notes, textbook excerpts, or any raw text here…"
          />
        </div>

        <!-- Action buttons -->
        <div>
          <label class="label">Action</label>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="action in actions" :key="action.id"
              @click="process(action.id)"
              :disabled="!rawNotes.trim() || isLoading"
              class="flex items-center gap-2.5 px-3 py-3 rounded-xl border text-left transition-all duration-200 disabled:opacity-40"
              :class="activeAction === action.id
                ? 'bg-pink-500/15 border-pink-500/40 text-pink-300'
                : 'bg-dark-700 border-dark-400 text-gray-300 hover:border-dark-300 hover:bg-dark-600'"
            >
              <span class="text-lg">{{ action.emoji }}</span>
              <div>
                <p class="text-xs font-semibold leading-tight">{{ action.label }}</p>
                <p class="text-[10px] text-gray-500 leading-tight">{{ action.desc }}</p>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Output -->
      <div class="flex flex-col p-5 space-y-3 overflow-y-auto">
        <div class="flex items-center justify-between">
          <label class="label">Output</label>
          <button v-if="output" @click="downloadTxt" class="btn-ghost text-xs gap-1.5">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download
          </button>
        </div>

        <!-- Empty state -->
        <div v-if="!output && !isLoading" class="flex-1 flex flex-col items-center justify-center text-center opacity-40">
          <svg class="w-12 h-12 text-gray-600 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <p class="text-gray-500 text-sm">Select an action to process your notes</p>
        </div>

        <!-- Loading pulses -->
        <div v-if="isLoading && !output" class="space-y-2 animate-pulse">
          <div v-for="i in 8" :key="i" class="h-3 rounded bg-dark-600" :style="`width:${60+Math.random()*35}%`" />
        </div>

        <!-- Output content -->
        <div v-if="output" class="card bg-dark-800 flex-1 animate-fade-in">
          <!-- Flashcard special render -->
          <div v-if="activeAction === 'flashcards'" class="space-y-3">
            <div v-for="(card, i) in parsedFlashcards" :key="i"
              class="rounded-lg border border-dark-400 overflow-hidden">
              <div class="px-4 py-2.5 bg-dark-700 border-b border-dark-400">
                <p class="text-xs text-pink-400 font-semibold mb-0.5">Q{{ i+1 }}</p>
                <p class="text-sm text-gray-200">{{ card.q }}</p>
              </div>
              <div class="px-4 py-2.5">
                <p class="text-xs text-gray-500 font-semibold mb-0.5">Answer</p>
                <p class="text-sm text-gray-300">{{ card.a }}</p>
              </div>
            </div>
          </div>
          <!-- Default: formatted text -->
          <div v-else>
            <pre class="text-sm text-gray-200 whitespace-pre-wrap font-sans leading-relaxed">{{ output }}<span v-if="isLoading" class="cursor-blink" /></pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { streamFetch } from '../utils/stream.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// Map action → learning style insight
const ACTION_STYLE = {
  flashcards: 'example-driven',
  outline:    'step-by-step',
  summarize:  'conceptual',
  clean:      'step-by-step',
}

const rawNotes    = ref('')
const output      = ref('')
const isLoading   = ref(false)
const activeAction= ref('')

const actions = [
  { id:'clean',      emoji:'✨', label:'Clean & Format', desc:'Headings + bullets'  },
  { id:'summarize',  emoji:'📝', label:'Summarize',      desc:'4-5 key points'     },
  { id:'outline',    emoji:'🗂️', label:'Outline',        desc:'Nested structure'   },
  { id:'flashcards', emoji:'🃏', label:'Flashcards',     desc:'5 Q&A pairs'        },
]

async function process(actionId) {
  if (!rawNotes.value.trim()) return
  output.value      = ''
  activeAction.value= actionId
  isLoading.value   = true

  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}

  await streamFetch(
    '/api/notes',
    { notes: rawNotes.value, action: actionId },
    (token) => { output.value += token },
    () => {
      isLoading.value = false
      // Infer learning style from chosen action
      const style = ACTION_STYLE[actionId]
      if (style) auth.upsertMemory({ learning_style: style })
    },
    (err) => { output.value = `Error: ${err}`; isLoading.value = false },
    authHeader,
  )
}

const parsedFlashcards = computed(() => {
  if (!output.value) return []
  const cards = []
  const blocks = output.value.split(/\n---+\n?/)
  for (const block of blocks) {
    const qm = block.match(/Q:\s*(.+?)(?:\n|$)/s)
    const am = block.match(/A:\s*(.+?)(?:\n|$)/s)
    if (qm && am) cards.push({ q: qm[1].trim(), a: am[1].trim() })
  }
  return cards
})

function downloadTxt() {
  const blob = new Blob([output.value], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = `notes_${activeAction.value}.txt`; a.click()
  URL.revokeObjectURL(url)
}
</script>
