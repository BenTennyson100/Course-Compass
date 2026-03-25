<template>
  <div class="min-h-screen flex items-center justify-center bg-mesh px-4">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="flex flex-col items-center mb-10">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-glow mb-4">
          <svg class="w-9 h-9 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-white">Course Compass</h1>
        <p class="text-sm text-gray-400 mt-1">AI-Powered Study Assistant</p>
      </div>

      <!-- Card -->
      <div class="rounded-2xl p-8" style="background: rgba(15,15,25,0.95); border: 1px solid rgba(99,102,241,0.15);">
        <h2 class="text-lg font-semibold text-white mb-1">Welcome back</h2>
        <p class="text-sm text-gray-400 mb-8">Sign in to save your chat history, quiz scores, and progress.</p>

        <!-- Error -->
        <div v-if="error" class="mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {{ error }}
        </div>

        <!-- Google Button -->
        <button
          @click="handleLogin"
          :disabled="loading"
          class="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200
                 bg-white text-gray-800 hover:bg-gray-100 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed shadow"
        >
          <svg v-if="!loading" class="w-5 h-5 shrink-0" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          <svg v-else class="w-5 h-5 animate-spin text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <span>{{ loading ? 'Redirecting…' : 'Continue with Google' }}</span>
        </button>

        <p class="mt-6 text-center text-xs text-gray-600">
          Your data is stored securely and only visible to you.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth    = useAuthStore()
const route   = useRoute()
const loading = ref(false)
const error   = ref(route.query.error === 'oauth_failed' ? 'Google sign-in failed. Please try again.' : '')

function handleLogin() {
  loading.value = true
  auth.login()
}
</script>
