import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token       = ref(localStorage.getItem('cc_token'))
  const user        = ref(null)
  const memoryMap   = ref({})   // key → value  (loaded on login)
  const activityMap = ref({})   // date → { count, types }

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  function setToken(t) {
    token.value = t
    if (t) localStorage.setItem('cc_token', t)
    else    localStorage.removeItem('cc_token')
  }

  function authHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function fetchUser() {
    if (!token.value) return false
    try {
      const res  = await axios.get('/api/auth/me', { headers: authHeaders() })
      user.value = res.data
      // Load memory and activity in background
      _loadMemoryMap()
      _loadActivity()
      return true
    } catch {
      setToken(null)
      user.value = null
      return false
    }
  }

  async function _loadMemoryMap() {
    try {
      const entries = await getMemory()
      const map = {}
      for (const e of entries) map[e.key] = e.value
      memoryMap.value = map
    } catch {}
  }

  async function _loadActivity() {
    try {
      const res = await axios.get('/api/activity', { headers: authHeaders() })
      const map = {}
      for (const r of res.data) map[r.date] = { count: r.count, types: r.types }
      activityMap.value = map
    } catch {}
  }

  function refreshActivityMap() { _loadActivity() }
  function refreshMemoryMap()   { _loadMemoryMap() }

  function login() {
    window.location.href = '/api/auth/google'
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  // ── History helpers ──────────────────────────────────────────────────────

  async function saveChatMessage(role, content) {
    if (!token.value) return
    try {
      await axios.post('/api/history/chat', { role, content }, { headers: authHeaders() })
    } catch (e) {
      console.warn('Could not save chat message', e)
    }
  }

  async function getChatHistory() {
    if (!token.value) return []
    try {
      const res = await axios.get('/api/history/chat', { headers: authHeaders() })
      return res.data
    } catch {
      return []
    }
  }

  async function saveQuizResult(subject, topic, score, total) {
    if (!token.value) return
    try {
      await axios.post('/api/history/quiz', { subject, topic, score, total }, { headers: authHeaders() })
    } catch (e) {
      console.warn('Could not save quiz result', e)
    }
  }

  async function getQuizHistory() {
    if (!token.value) return []
    try {
      const res = await axios.get('/api/history/quiz', { headers: authHeaders() })
      return res.data
    } catch {
      return []
    }
  }

  // ── Memory helpers ───────────────────────────────────────────────────────

  async function getMemory() {
    if (!token.value) return []
    try {
      const res = await axios.get('/api/memory', { headers: authHeaders() })
      return res.data
    } catch {
      return []
    }
  }

  async function deleteMemoryKey(key) {
    if (!token.value) return
    await axios.delete(`/api/memory/${key}`, { headers: authHeaders() })
  }

  async function clearMemory() {
    if (!token.value) return
    await axios.delete('/api/memory', { headers: authHeaders() })
  }

  async function upsertMemory(updates) {
    if (!token.value || !Object.keys(updates).length) return
    try {
      await axios.post('/api/memory/upsert', { updates }, { headers: authHeaders() })
    } catch (e) {
      console.warn('Memory upsert failed', e)
    }
  }

  async function extractMemory(userMessage, assistantMessage) {
    if (!token.value) return
    try {
      await axios.post(
        '/api/memory/extract',
        { user_message: userMessage, assistant_message: assistantMessage },
        { headers: authHeaders() }
      )
    } catch (e) {
      console.warn('Memory extraction failed', e)
    }
  }

  return {
    token, user, isAuthenticated,
    setToken, fetchUser, login, logout,
    authHeaders,
    saveChatMessage, getChatHistory,
    saveQuizResult, getQuizHistory,
    memoryMap, activityMap, refreshMemoryMap, refreshActivityMap,
    getMemory, deleteMemoryKey, clearMemory, extractMemory, upsertMemory,
  }
})
