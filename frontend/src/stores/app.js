import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // ── Chat ──────────────────────────────────────────────────────────────────
  const chatHistory = ref([])  // [{role, content, timestamp}]

  function addChatMessage(role, content) {
    chatHistory.value.push({ role, content, timestamp: Date.now() })
  }

  function clearChat() {
    chatHistory.value = []
  }

  // ── Progress ──────────────────────────────────────────────────────────────
  const terms = ref([
    { id: 1, name: 'Term 1', scores: {} },
    { id: 2, name: 'Term 2', scores: {} },
  ])

  function addTerm() {
    const id = Date.now()
    terms.value.push({ id, name: `Term ${terms.value.length + 1}`, scores: {} })
  }

  function removeTerm(id) {
    terms.value = terms.value.filter(t => t.id !== id)
  }

  function updateTerm(id, data) {
    const t = terms.value.find(t => t.id === id)
    if (t) Object.assign(t, data)
  }

  // ── Quiz ──────────────────────────────────────────────────────────────────
  const quizState = ref({
    phase: 'setup',        // setup | quiz | results
    questions: [],
    userAnswers: {},
    subject: '',
    startTime: null,
    duration: 60,
  })

  function resetQuiz() {
    quizState.value = {
      phase: 'setup',
      questions: [],
      userAnswers: {},
      subject: '',
      startTime: null,
      duration: 60,
    }
  }

  // ── Sidebar ───────────────────────────────────────────────────────────────
  const sidebarOpen = ref(true)
  function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value }

  return {
    chatHistory, addChatMessage, clearChat,
    terms, addTerm, removeTerm, updateTerm,
    quizState, resetQuiz,
    sidebarOpen, toggleSidebar,
  }
})
