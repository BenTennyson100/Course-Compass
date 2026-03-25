<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="shrink-0 px-6 py-4 border-b border-dark-400/50 glass flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="flex-1">
        <h1 class="text-sm font-semibold text-white">Quiz Generator</h1>
        <p class="text-xs text-gray-500">Test your knowledge with AI-generated MCQs</p>
      </div>
      <button v-if="phase !== 'setup'" @click="resetQuiz" class="btn-ghost text-xs">
        ← New Quiz
      </button>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto">
      <!-- ── Phase: Setup ── -->
      <div v-if="phase === 'setup'" class="p-6 max-w-xl mx-auto space-y-5 animate-fade-in">
        <div class="text-center py-4">
          <h2 class="text-2xl font-bold text-white mb-1">Configure Quiz</h2>
          <p class="text-gray-400 text-sm">Set up your practice session</p>
        </div>

        <div>
          <label class="label">Subject *</label>
          <input v-model="config.subject" class="input" placeholder="e.g. Machine Learning, Data Structures" />
        </div>

        <div>
          <label class="label">Topic <span class="normal-case font-normal text-gray-500">(optional)</span></label>
          <input v-model="config.topic" class="input" placeholder="e.g. Decision Trees, Sorting Algorithms" />
        </div>

        <!-- Number of questions -->
        <div>
          <label class="label">Number of Questions</label>
          <div class="grid grid-cols-4 gap-2">
            <button v-for="n in [5,10,15,20]" :key="n"
              @click="config.numQuestions = n"
              class="py-2.5 rounded-lg text-sm font-semibold border transition-all duration-200"
              :class="config.numQuestions === n
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                : 'bg-dark-600 text-gray-400 border-dark-400 hover:border-dark-300'"
            >{{ n }}</button>
          </div>
        </div>

        <!-- Duration -->
        <div>
          <label class="label">Time Limit (seconds per question)</label>
          <div class="grid grid-cols-4 gap-2">
            <button v-for="d in [30,60,90,120]" :key="d"
              @click="config.duration = d"
              class="py-2.5 rounded-lg text-sm font-semibold border transition-all duration-200"
              :class="config.duration === d
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                : 'bg-dark-600 text-gray-400 border-dark-400 hover:border-dark-300'"
            >{{ d }}s</button>
          </div>
        </div>

        <button @click="generateQuiz" :disabled="!config.subject.trim() || isGenerating" class="btn-primary w-full justify-center py-3"
          style="background: linear-gradient(135deg, #f59e0b, #d97706);">
          <svg v-if="!isGenerating" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3l14 9-14 9V3z"/></svg>
          <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ isGenerating ? 'Generating Questions…' : 'Start Quiz' }}
        </button>

        <p v-if="error" class="text-red-400 text-sm text-center">{{ error }}</p>
      </div>

      <!-- ── Phase: Quiz ── -->
      <div v-if="phase === 'quiz'" class="p-6 max-w-2xl mx-auto animate-fade-in">
        <!-- Timer + Progress -->
        <div class="flex items-center justify-between mb-6">
          <!-- Timer -->
          <div class="flex items-center gap-3">
            <div class="relative w-12 h-12">
              <svg class="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" fill="none" stroke="#1a1a30" stroke-width="3"/>
                <circle cx="24" cy="24" r="20" fill="none"
                  :stroke="timerColor" stroke-width="3"
                  stroke-linecap="round"
                  :stroke-dasharray="`${125.66}`"
                  :stroke-dashoffset="`${125.66 * (1 - timerFraction)}`"
                  style="transition: stroke-dashoffset 0.5s linear, stroke 0.5s"
                />
              </svg>
              <span class="absolute inset-0 flex items-center justify-center text-xs font-bold"
                :class="timeLeft <= 10 ? 'text-red-400' : 'text-gray-200'">{{ timeLeft }}</span>
            </div>
            <div>
              <p class="text-xs text-gray-500">Time left</p>
              <p class="text-sm font-semibold text-white">{{ config.subject }}</p>
            </div>
          </div>
          <!-- Progress -->
          <div class="text-right">
            <p class="text-2xl font-bold text-white">{{ currentQ + 1 }}<span class="text-gray-500 text-base font-normal">/{{ questions.length }}</span></p>
            <div class="flex gap-1 mt-1 justify-end">
              <div v-for="(q, i) in questions" :key="i"
                class="w-2 h-2 rounded-full transition-all duration-200"
                :class="i === currentQ ? 'bg-amber-400' : userAnswers[i] ? 'bg-brand-400' : 'bg-dark-400'"
              />
            </div>
          </div>
        </div>

        <!-- Question Card -->
        <div class="card mb-4">
          <p class="text-xs text-amber-400 font-semibold mb-2">Question {{ currentQ + 1 }}</p>
          <p class="text-white font-medium text-base leading-relaxed">{{ currentQuestion.question }}</p>
        </div>

        <!-- Options -->
        <div class="space-y-2.5 mb-6">
          <button
            v-for="(text, key) in currentQuestion.options" :key="key"
            @click="selectAnswer(key)"
            class="w-full text-left px-4 py-3.5 rounded-xl border transition-all duration-200 flex items-center gap-3"
            :class="optionClass(key)"
          >
            <span class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 border transition-all duration-200"
              :class="optionKeyClass(key)">{{ key }}</span>
            <span class="text-sm leading-relaxed">{{ text }}</span>
          </button>
        </div>

        <!-- Nav Buttons -->
        <div class="flex gap-3">
          <button @click="prevQ" :disabled="currentQ === 0" class="btn-secondary flex-1 justify-center">← Prev</button>
          <button v-if="currentQ < questions.length - 1" @click="nextQ" class="btn-primary flex-1 justify-center">Next →</button>
          <button v-else @click="submitQuiz" class="btn-primary flex-1 justify-center" style="background: linear-gradient(135deg, #10b981, #0d9488);">
            Submit Quiz
          </button>
        </div>
      </div>

      <!-- ── Phase: Results ── -->
      <div v-if="phase === 'results'" class="p-6 max-w-2xl mx-auto animate-fade-in">
        <!-- Score ring -->
        <div class="flex flex-col items-center py-6">
          <div class="relative w-32 h-32 mb-4">
            <svg class="w-32 h-32 -rotate-90" viewBox="0 0 128 128">
              <circle cx="64" cy="64" r="54" fill="none" stroke="#1a1a30" stroke-width="8"/>
              <circle cx="64" cy="64" r="54" fill="none"
                :stroke="scoreGrade.color" stroke-width="8" stroke-linecap="round"
                :stroke-dasharray="`${339.3}`"
                :stroke-dashoffset="`${339.3 * (1 - score / questions.length)}`"
                style="transition: stroke-dashoffset 1s ease-out"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-3xl font-bold text-white">{{ score }}</span>
              <span class="text-xs text-gray-400">/ {{ questions.length }}</span>
            </div>
          </div>
          <div class="badge mb-2" :style="`background:${scoreGrade.color}22; color:${scoreGrade.color}; border-color:${scoreGrade.color}44`">
            {{ scoreGrade.label }}
          </div>
          <p class="text-gray-400 text-sm">{{ Math.round(score/questions.length*100) }}% correct · {{ config.subject }}</p>
        </div>

        <!-- Download -->
        <div class="flex justify-center mb-6">
          <button @click="downloadResults" class="btn-ghost text-xs gap-1.5">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download Results
          </button>
        </div>

        <!-- Question breakdown -->
        <div class="space-y-3">
          <div v-for="(q, i) in questions" :key="i" class="card-sm">
            <div class="flex items-start gap-3">
              <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                :class="userAnswers[i] === q.answer ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'">
                {{ userAnswers[i] === q.answer ? '✓' : '✗' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-gray-200 font-medium mb-1">{{ q.question }}</p>
                <div class="flex flex-wrap gap-x-4 gap-y-0.5 text-xs">
                  <span class="text-gray-500">Your answer: <span :class="userAnswers[i] === q.answer ? 'text-emerald-400' : 'text-red-400'">{{ userAnswers[i] || '—' }}. {{ q.options[userAnswers[i]] }}</span></span>
                  <span v-if="userAnswers[i] !== q.answer" class="text-gray-500">Correct: <span class="text-emerald-400">{{ q.answer }}. {{ q.options[q.answer] }}</span></span>
                </div>
                <!-- Feedback -->
                <div v-if="feedbacks[i]" class="mt-2 p-2.5 rounded-lg bg-dark-600 text-xs text-gray-300 border border-dark-400 leading-relaxed">
                  {{ feedbacks[i] }}
                </div>
                <button v-else-if="userAnswers[i] !== q.answer" @click="getFeedback(i)"
                  :disabled="loadingFeedback[i]"
                  class="mt-2 text-xs text-brand-400 hover:text-brand-300 transition-colors">
                  {{ loadingFeedback[i] ? 'Loading…' : '💡 Explain why' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { apiFetch } from '../utils/stream.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// ── State ──
const phase      = ref('setup')
const config     = reactive({ subject:'', topic:'', numQuestions:10, duration:60 })
const questions  = ref([])
const userAnswers= reactive({})
const currentQ   = ref(0)
const feedbacks  = reactive({})
const loadingFeedback = reactive({})
const isGenerating = ref(false)
const error      = ref('')

// ── Timer ──
const timeLeft   = ref(60)
let   timer      = null

function startTimer() {
  timeLeft.value = config.duration
  clearInterval(timer)
  timer = setInterval(() => {
    if (timeLeft.value <= 1) {
      clearInterval(timer)
      if (phase.value === 'quiz') submitQuiz()
    } else {
      timeLeft.value--
    }
  }, 1000)
}

function resetTimer() {
  timeLeft.value = config.duration
  clearInterval(timer)
  startTimer()
}

onUnmounted(() => clearInterval(timer))

const timerFraction = computed(() => timeLeft.value / config.duration)
const timerColor    = computed(() => {
  if (timerFraction.value > 0.5) return '#34d399'
  if (timerFraction.value > 0.25) return '#f59e0b'
  return '#f87171'
})

// ── Current question ──
const currentQuestion = computed(() => questions.value[currentQ.value] ?? {})

// ── Generate ──
async function generateQuiz() {
  if (!config.subject.trim()) return
  isGenerating.value = true
  error.value = ''

  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}

  try {
    const res = await apiFetch('/api/quiz/generate', {
      subject:       config.subject,
      topic:         config.topic,
      num_questions: config.numQuestions,
      duration:      config.duration,
    }, authHeader)
    if (!res.questions?.length) throw new Error('No questions returned. Try again.')
    questions.value = res.questions
    phase.value     = 'quiz'
    startTimer()
  } catch (e) {
    error.value = e.message
  } finally {
    isGenerating.value = false
  }
}

function selectAnswer(key) {
  userAnswers[currentQ.value] = key
}

function nextQ() {
  if (currentQ.value < questions.value.length - 1) {
    currentQ.value++
    resetTimer()
  }
}

function prevQ() {
  if (currentQ.value > 0) {
    currentQ.value--
    resetTimer()
  }
}

function submitQuiz() {
  clearInterval(timer)
  phase.value = 'results'

  // Extract memory from quiz performance
  const pct = score.value / questions.value.length
  const memUpdates = {
    interests: config.subject,
  }
  if (pct >= 0.8) {
    memUpdates.expertise_level = 'advanced'
  } else if (pct >= 0.5) {
    memUpdates.expertise_level = 'intermediate'
  } else {
    memUpdates.expertise_level = 'beginner'
    memUpdates.struggles = config.subject + (config.topic ? ` (${config.topic})` : '')
  }
  auth.upsertMemory(memUpdates)
  auth.saveQuizResult(config.subject, config.topic, score.value, questions.value.length)
  auth.refreshActivityMap()
  auth.refreshMemoryMap()
}

// ── Scoring ──
const score = computed(() =>
  questions.value.filter((q, i) => userAnswers[i] === q.answer).length
)

const scoreGrade = computed(() => {
  const pct = score.value / questions.value.length
  if (pct >= 0.9) return { label: 'Excellent!', color: '#34d399' }
  if (pct >= 0.7) return { label: 'Good Job',   color: '#818cf8' }
  if (pct >= 0.5) return { label: 'Keep Going', color: '#f59e0b' }
  return { label: 'Need Practice', color: '#f87171' }
})

// ── Option styling ──
function optionClass(key) {
  const selected = userAnswers[currentQ.value] === key
  return selected
    ? 'bg-brand-500/10 border-brand-500/60 text-white'
    : 'bg-dark-700 border-dark-400 text-gray-300 hover:border-dark-300 hover:bg-dark-600'
}

function optionKeyClass(key) {
  const selected = userAnswers[currentQ.value] === key
  return selected
    ? 'bg-brand-500 border-brand-500 text-white'
    : 'bg-dark-600 border-dark-400 text-gray-500'
}

// ── Feedback ──
async function getFeedback(i) {
  loadingFeedback[i] = true
  const q = questions.value[i]
  const authHeader = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
  try {
    const res = await apiFetch('/api/quiz/feedback', {
      question:       q.question,
      user_answer:    `${userAnswers[i]}. ${q.options[userAnswers[i]] || 'No answer'}`,
      correct_answer: `${q.answer}. ${q.options[q.answer]}`,
      subject:        config.subject,
    }, authHeader)
    feedbacks[i] = res.feedback
  } catch (e) {
    feedbacks[i] = 'Could not load explanation.'
  } finally {
    loadingFeedback[i] = false
  }
}

// ── Download ──
function downloadResults() {
  const lines = [
    `Quiz Results — ${config.subject}`,
    `Score: ${score.value}/${questions.value.length} (${Math.round(score.value/questions.value.length*100)}%)`,
    '',
    ...questions.value.map((q, i) => [
      `Q${i+1}. ${q.question}`,
      `  Your answer: ${userAnswers[i] || '—'}. ${q.options[userAnswers[i]] || ''}`,
      `  Correct: ${q.answer}. ${q.options[q.answer]}`,
      feedbacks[i] ? `  Explanation: ${feedbacks[i]}` : '',
    ].join('\n'))
  ]
  const blob = new Blob([lines.join('\n\n')], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'quiz_results.txt'; a.click()
  URL.revokeObjectURL(url)
}

function resetQuiz() {
  clearInterval(timer)
  phase.value = 'setup'
  questions.value = []
  currentQ.value  = 0
  Object.keys(userAnswers).forEach(k => delete userAnswers[k])
  Object.keys(feedbacks).forEach(k => delete feedbacks[k])
}
</script>
