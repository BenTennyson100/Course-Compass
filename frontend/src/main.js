import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router/index.js'
import './style.css'

// In production, VITE_API_BASE should point to your deployed backend (e.g. https://your-api.railway.app)
if (import.meta.env.VITE_API_BASE) {
  axios.defaults.baseURL = import.meta.env.VITE_API_BASE
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
