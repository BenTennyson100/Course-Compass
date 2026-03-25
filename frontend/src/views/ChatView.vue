<template>
  <div class="flex h-full overflow-hidden relative">

    <!-- ── Main chat ─────────────────────────────────────────────────────── -->
    <div class="flex flex-col flex-1 h-full min-w-0 transition-all duration-300">

      <!-- Header -->
      <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 flex items-center gap-3 glass">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center">
          <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div>
          <h1 class="text-sm font-semibold text-white">AI Chat</h1>
          <p class="text-xs text-gray-500">Ask anything academic</p>
        </div>

        <div class="ml-auto flex items-center gap-2">
          <!-- Memory toggle -->
          <button
            @click="openPanel('memory')"
            :class="activePanel === 'memory' ? 'text-violet-400 bg-violet-500/10' : ''"
            class="btn-ghost text-xs gap-1.5"
            title="AI Memory"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
            </svg>
            Memory
          </button>
          <!-- History toggle -->
          <button
            @click="openPanel('history')"
            :class="activePanel === 'history' ? 'text-brand-400 bg-brand-500/10' : ''"
            class="btn-ghost text-xs gap-1.5"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
            </svg>
            History
          </button>
          <button @click="clearChat" class="btn-ghost text-xs gap-1.5">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.5"/></svg>
            Clear
          </button>
        </div>
      </header>

      <!-- Messages -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto px-6 py-6 space-y-6">

        <!-- Empty state -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center animate-fade-in">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center mb-4 shadow-glow">
            <svg class="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
          </div>
          <h2 class="text-xl font-bold text-white mb-2">Course Compass</h2>
          <p class="text-gray-400 text-sm max-w-sm">Your AI-powered academic mentor. Ask me anything about computer science, math, data science, or any subject you're studying.</p>
          <div class="grid grid-cols-2 gap-2 mt-6 w-full max-w-sm">
            <button v-for="p in prompts" :key="p" @click="sendQuick(p)"
              class="px-3 py-2 rounded-lg bg-dark-600 hover:bg-dark-500 border border-dark-400 text-xs text-gray-300 hover:text-white text-left transition-all duration-200 hover:border-brand-500/50"
            >{{ p }}</button>
          </div>
        </div>

        <!-- Message list -->
        <template v-if="messages.length > 0">
          <div
            v-for="(msg, i) in messages" :key="i"
            class="flex gap-3 animate-fade-in"
            :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
          >
            <!-- Avatar -->
            <div class="shrink-0">
              <div v-if="msg.role === 'assistant'"
                class="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-glow-sm">
                <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
              </div>
              <div v-else class="w-8 h-8 rounded-full overflow-hidden border border-dark-300 shrink-0">
                <img v-if="auth.user?.picture" :src="auth.user.picture" :alt="auth.user.name" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-dark-500 flex items-center justify-center text-xs font-bold text-gray-300">U</div>
              </div>
            </div>

            <!-- Bubble -->
            <div class="max-w-[75%] space-y-1">
              <div
                class="px-4 py-3 rounded-2xl text-sm leading-relaxed"
                :class="msg.role === 'user'
                  ? 'bg-brand-600 text-white rounded-tr-sm'
                  : 'bg-dark-700 border border-dark-400 text-gray-200 rounded-tl-sm'"
              >
                <span v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)" />
                <span v-else>{{ msg.content }}</span>
                <span v-if="i === messages.length - 1 && msg.role === 'assistant' && isStreaming" class="cursor-blink" />
              </div>
              <p class="text-[10px] text-gray-600 px-1" :class="msg.role === 'user' ? 'text-right' : 'text-left'">
                {{ formatTime(msg.timestamp) }}
              </p>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="isThinking" class="flex gap-3 animate-fade-in">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-glow-sm shrink-0">
              <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
            </div>
            <div class="bg-dark-700 border border-dark-400 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 min-w-[140px]">
              <span class="thinking-word text-sm text-brand-300 font-medium">{{ thinkingWord }}</span>
              <span class="flex gap-0.5 items-center">
                <span v-for="n in 3" :key="n" class="w-1 h-1 rounded-full bg-brand-400/60" :style="`animation: bounce 1.2s ${(n-1)*0.2}s ease-in-out infinite`" />
              </span>
            </div>
          </div>
        </template>
      </div>

      <!-- Input -->
      <div class="shrink-0 px-6 py-4 border-t border-dark-400/50 glass">
        <div class="flex gap-3 items-end max-w-4xl mx-auto">
          <div class="flex-1 relative">
            <textarea
              ref="inputEl"
              v-model="input"
              @keydown.enter.exact.prevent="send"
              @keydown.enter.shift.exact="() => {}"
              rows="1"
              placeholder="Ask anything... (Enter to send, Shift+Enter for new line)"
              class="textarea resize-none max-h-36 overflow-y-auto pr-4"
              :disabled="isStreaming || isThinking"
              @input="autoResize"
            />
          </div>
          <button
            @click="send"
            :disabled="!input.trim() || isStreaming || isThinking"
            class="btn-primary h-10 px-4 shrink-0"
          >
            <svg v-if="!isStreaming" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          </button>
        </div>
        <p class="text-center text-[10px] text-gray-600 mt-2">Powered by Ollama · Local AI · No data leaves your machine</p>
      </div>
    </div>

    <!-- ── Side Panel (History / Memory) ────────────────────────────────── -->
    <Transition name="history-slide">
      <aside
        v-if="activePanel"
        class="fixed right-0 top-0 h-full w-80 flex flex-col z-30 border-l border-dark-400/50"
        style="background: rgba(8,8,15,0.98);"
      >

        <!-- ── History panel ─────────────────────────────────────────── -->
        <template v-if="activePanel === 'history'">
          <div class="shrink-0 px-4 py-4 border-b border-dark-400/50 flex items-center gap-2">
            <svg class="w-4 h-4 text-brand-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
            </svg>
            <h2 class="text-sm font-semibold text-white">Chat History</h2>
            <button @click="activePanel = null" class="ml-auto text-gray-500 hover:text-gray-300 transition-colors">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div v-if="historyLoading" class="flex-1 flex items-center justify-center">
            <svg class="w-5 h-5 animate-spin text-brand-400" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          </div>

          <div v-else-if="groupedHistory.length === 0" class="flex-1 flex flex-col items-center justify-center text-center px-6">
            <svg class="w-10 h-10 text-gray-700 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
            </svg>
            <p class="text-sm text-gray-500">No history yet.</p>
            <p class="text-xs text-gray-600 mt-1">Start chatting to build your history.</p>
          </div>

          <div v-else class="flex-1 overflow-y-auto py-3 space-y-4">
            <div v-for="group in groupedHistory" :key="group.date">
              <div class="px-4 py-1">
                <span class="text-[10px] font-semibold uppercase tracking-widest text-gray-600">{{ group.label }}</span>
              </div>
              <div
                v-for="(msg, i) in group.messages" :key="i"
                class="mx-3 px-3 py-2 rounded-xl mb-1"
                :class="msg.role === 'user' ? 'bg-brand-600/10 border border-brand-500/20' : 'bg-dark-700/60 border border-dark-400/30'"
              >
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-[10px] font-medium" :class="msg.role === 'user' ? 'text-brand-400' : 'text-violet-400'">
                    {{ msg.role === 'user' ? 'You' : 'AI' }}
                  </span>
                  <span class="text-[10px] text-gray-600">{{ formatTime(msg.timestamp) }}</span>
                </div>
                <p class="text-xs text-gray-300 line-clamp-3 leading-relaxed">{{ stripMarkdown(msg.content) }}</p>
              </div>
            </div>
          </div>

          <div class="shrink-0 px-4 py-3 border-t border-dark-400/50">
            <p class="text-[10px] text-gray-600 text-center">{{ totalHistoryCount }} messages saved</p>
          </div>
        </template>

        <!-- ── Memory panel ───────────────────────────────────────────── -->
        <template v-if="activePanel === 'memory'">
          <div class="shrink-0 px-4 py-4 border-b border-dark-400/50 flex items-center gap-2">
            <svg class="w-4 h-4 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
            </svg>
            <h2 class="text-sm font-semibold text-white">AI Memory</h2>
            <button
              v-if="memoryEntries.length"
              @click="handleClearMemory"
              class="ml-auto text-[10px] text-red-400/70 hover:text-red-400 transition-colors px-2 py-0.5 rounded border border-red-400/20 hover:border-red-400/50"
            >Clear all</button>
            <button @click="activePanel = null" :class="memoryEntries.length ? 'ml-2' : 'ml-auto'" class="text-gray-500 hover:text-gray-300 transition-colors">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div v-if="memoryLoading" class="flex-1 flex items-center justify-center">
            <svg class="w-5 h-5 animate-spin text-violet-400" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          </div>

          <div v-else-if="memoryEntries.length === 0" class="flex-1 flex flex-col items-center justify-center text-center px-6">
            <svg class="w-10 h-10 text-gray-700 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
            </svg>
            <p class="text-sm text-gray-500">No memory yet.</p>
            <p class="text-xs text-gray-600 mt-1">The AI learns about you as you chat.</p>
          </div>

          <div v-else class="flex-1 overflow-y-auto py-3 px-3 space-y-2">
            <p class="text-[10px] text-gray-600 px-1 pb-1">The AI uses this to personalize every response.</p>
            <div
              v-for="entry in memoryEntries" :key="entry.key"
              class="group flex items-start gap-2 px-3 py-2.5 rounded-xl border transition-colors"
              :class="categoryStyle(entry.category)"
            >
              <div class="flex-1 min-w-0">
                <p class="text-[10px] font-semibold uppercase tracking-wide mb-0.5" :class="categoryLabelColor(entry.category)">
                  {{ memoryKeyLabel(entry.key) }}
                </p>
                <p class="text-xs text-gray-300 leading-relaxed">{{ entry.value }}</p>
              </div>
              <button
                @click="handleDeleteMemory(entry.key)"
                class="shrink-0 opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all mt-0.5"
                title="Forget this"
              >
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="shrink-0 px-4 py-3 border-t border-dark-400/50">
            <p class="text-[10px] text-gray-600 text-center">Updated automatically after each chat</p>
          </div>
        </template>

      </aside>
    </Transition>

    <!-- Overlay -->
    <div v-if="activePanel" class="fixed inset-0 z-20 lg:hidden" @click="activePanel = null" />
  </div>
</template>

<script setup>
import { ref, nextTick, computed, watch, onMounted } from 'vue'
import { useAppStore } from '../stores/app.js'
import { useAuthStore } from '../stores/auth.js'
import { streamFetch } from '../utils/stream.js'

const store      = useAppStore()
const auth       = useAuthStore()
const messages   = computed(() => store.chatHistory)
const input      = ref('')
const isStreaming= ref(false)
const isThinking = ref(false)
const messagesEl = ref(null)
const inputEl    = ref(null)

// ── Panel state ───────────────────────────────────────────────────────────────
const activePanel = ref(null)   // null | 'history' | 'memory'

function openPanel(name) {
  activePanel.value = activePanel.value === name ? null : name
}

// ── History panel ────────────────────────────────────────────────────────────
const historyLoading  = ref(false)
const historyMessages = ref([])

const totalHistoryCount = computed(() => historyMessages.value.length)

const groupedHistory = computed(() => {
  const groups = {}
  for (const msg of historyMessages.value) {
    const date  = new Date(msg.timestamp)
    const key   = date.toDateString()
    if (!groups[key]) groups[key] = { date: key, label: dateLabel(date), messages: [] }
    groups[key].messages.push(msg)
  }
  return Object.values(groups).reverse()
})

function dateLabel(date) {
  const today     = new Date()
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
  if (date.toDateString() === today.toDateString())     return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })
}

async function loadHistory() {
  if (!auth.token) return
  historyLoading.value = true
  try {
    const rows = await auth.getChatHistory()
    // Normalize timestamp field
    historyMessages.value = rows.map(r => ({ ...r, timestamp: r.timestamp }))

    // Pre-load last 12 messages into store so model has context (prevents hallucination)
    if (store.chatHistory.length === 0 && rows.length > 0) {
      const recent = rows.slice(-12)
      for (const r of recent) {
        store.chatHistory.push({ role: r.role, content: r.content, timestamp: new Date(r.timestamp).getTime() })
      }
      await scrollBottom()
    }
  } finally {
    historyLoading.value = false
  }
}

// ── Memory panel ─────────────────────────────────────────────────────────────
const memoryLoading = ref(false)
const memoryEntries = ref([])

const MEMORY_LABELS = {
  learning_style:     'Learning Style',
  expertise_level:    'Expertise Level',
  prefers_concise:    'Response Length',
  prefers_examples:   'Wants Examples',
  prefers_code:       'Wants Code',
  communication_tone: 'Tone Preference',
  interests:          'Topics of Interest',
  struggles:          'Finds Difficult',
}

function memoryKeyLabel(key) {
  return MEMORY_LABELS[key] ?? key.replace(/_/g, ' ')
}

function categoryStyle(cat) {
  const map = {
    style:      'bg-violet-500/5 border-violet-500/20',
    level:      'bg-blue-500/5 border-blue-500/20',
    preference: 'bg-emerald-500/5 border-emerald-500/20',
    behavior:   'bg-amber-500/5 border-amber-500/20',
  }
  return map[cat] ?? 'bg-dark-700/40 border-dark-400/30'
}

function categoryLabelColor(cat) {
  const map = {
    style:      'text-violet-400',
    level:      'text-blue-400',
    preference: 'text-emerald-400',
    behavior:   'text-amber-400',
  }
  return map[cat] ?? 'text-gray-500'
}

async function loadMemory() {
  memoryLoading.value = true
  try { memoryEntries.value = await auth.getMemory() }
  finally { memoryLoading.value = false }
}

async function handleDeleteMemory(key) {
  await auth.deleteMemoryKey(key)
  memoryEntries.value = memoryEntries.value.filter(e => e.key !== key)
}

async function handleClearMemory() {
  await auth.clearMemory()
  memoryEntries.value = []
}

// Reload panel data when switching panels
watch(activePanel, (val) => {
  if (val === 'history') loadHistory()
  if (val === 'memory')  loadMemory()
})

// ── Thinking words ───────────────────────────────────────────────────────────
const thinkingWords = [
  'Thinking', 'Analyzing', 'Processing', 'Reasoning',
  'Reflecting', 'Computing', 'Pondering', 'Considering',
  'Evaluating', 'Calculating', 'Synthesizing', 'Formulating',
]
const thinkingWord    = ref(thinkingWords[0])
let   thinkingInterval = null

watch(isThinking, (val) => {
  if (val) {
    let i = 0
    thinkingWord.value = thinkingWords[0]
    thinkingInterval = setInterval(() => {
      i = (i + 1) % thinkingWords.length
      thinkingWord.value = thinkingWords[i]
    }, 600)
  } else {
    clearInterval(thinkingInterval)
  }
})

// ── On mount: load history for context ───────────────────────────────────────
onMounted(() => loadHistory())

// ── Chat ─────────────────────────────────────────────────────────────────────
const prompts = [
  'Explain neural networks simply',
  'How does gradient descent work?',
  'What is Big O notation?',
  'Help me understand recursion',
]

function clearChat() { store.clearChat() }

function sendQuick(p) {
  input.value = p
  send()
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 144) + 'px'
}

async function send() {
  const text = input.value.trim()
  if (!text || isStreaming.value || isThinking.value) return

  store.addChatMessage('user', text)
  auth.saveChatMessage('user', text)   // persist to DB
  input.value = ''
  if (inputEl.value) inputEl.value.style.height = 'auto'

  isThinking.value = true
  await scrollBottom()

  // Use last 10 messages as context (prevents hallucination by maintaining conversation state)
  const apiMessages = store.chatHistory.slice(-10).map(m => ({
    role: m.role, content: m.content
  }))

  // Add empty assistant slot to stream into
  store.addChatMessage('assistant', '')
  const idx = store.chatHistory.length - 1

  isThinking.value = false
  isStreaming.value = true
  await scrollBottom()

  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}

  await streamFetch(
    '/api/chat',
    { messages: apiMessages },
    (token) => {
      store.chatHistory[idx].content += token
      scrollBottom()
    },
    () => {
      isStreaming.value = false
      const reply = store.chatHistory[idx]?.content
      if (reply) {
        auth.saveChatMessage('assistant', reply)
        // Fire-and-forget memory extraction + activity refresh
        auth.extractMemory(text, reply)
        auth.refreshActivityMap()
      }
    },
    (err) => {
      store.chatHistory[idx].content = `⚠️ Error: ${err}`
      isStreaming.value = false
    },
    authHeader,
  )
}

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function formatTime(ts) {
  const d = typeof ts === 'string' ? new Date(ts) : new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, '[code]')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/^#+\s/gm, '')
    .replace(/^[-•]\s/gm, '')
    .replace(/\n/g, ' ')
    .trim()
}

function renderMarkdown(text) {
  return text
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre class="bg-dark-800 rounded-lg p-3 my-2 overflow-x-auto text-xs font-mono text-brand-300">$2</pre>')
    .replace(/`([^`]+)`/g, '<code class="bg-dark-600 text-brand-300 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*([^*]+)\*/g,     '<em class="text-gray-300">$1</em>')
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-white mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="text-lg font-bold text-white mt-4 mb-1">$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1 class="text-xl font-bold text-white mt-4 mb-2">$1</h1>')
    .replace(/^[-•] (.+)$/gm,'<li class="ml-4 list-disc">$1</li>')
    .replace(/\n/g, '<br/>')
}
</script>

<style scoped>
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

.thinking-word {
  animation: word-fade 0.5s ease-in-out;
}

@keyframes word-fade {
  0%   { opacity: 0; transform: translateY(4px); }
  100% { opacity: 1; transform: translateY(0); }
}

.history-slide-enter-active,
.history-slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.history-slide-enter-from,
.history-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
