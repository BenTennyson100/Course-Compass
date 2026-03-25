<template>
  <div class="min-h-screen flex items-center justify-center bg-mesh">
    <div class="flex flex-col items-center gap-4 text-center">
      <svg class="w-10 h-10 animate-spin text-brand-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
      </svg>
      <p class="text-gray-400 text-sm">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router  = useRouter()
const route   = useRoute()
const auth    = useAuthStore()
const message = ref('Signing you in…')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    router.replace('/login?error=oauth_failed')
    return
  }

  auth.setToken(token)
  const ok = await auth.fetchUser()
  if (ok) {
    router.replace('/')
  } else {
    router.replace('/login?error=oauth_failed')
  }
})
</script>
