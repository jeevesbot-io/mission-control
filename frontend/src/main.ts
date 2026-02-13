import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import App from './App.vue'
import router from './router'
import './styles/base.css'
import 'primeicons/primeicons.css'

const MissionControlPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#eef0ff',
      100: '#dfe2ff',
      200: '#c5c7ff',
      300: '#a2a0ff',
      400: '#8a7fff',
      500: '#7c6aff',
      600: '#6f4cf7',
      700: '#603fdb',
      800: '#4e35b1',
      900: '#42338b',
      950: '#271d52',
    },
    colorScheme: {
      dark: {
        surface: {
          0: '#ffffff',
          50: '#e2e4ed',
          100: '#6b7084',
          200: '#363a52',
          300: '#282c42',
          400: '#1c2035',
          500: '#10131e',
          600: '#0e1119',
          700: '#0c0e16',
          800: '#0a0c14',
          900: '#070910',
          950: '#04050a',
        },
      },
      light: {
        surface: {
          0: '#ffffff',
          50: '#f4f5f9',
          100: '#ebedf3',
          200: '#dddfe8',
          300: '#c9cbd7',
          400: '#a1a3b3',
          500: '#7c7e91',
          600: '#6b7280',
          700: '#4b5563',
          800: '#374151',
          900: '#1f2937',
          950: '#111827',
        },
      },
    },
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: MissionControlPreset,
    options: {
      darkModeSelector: '.dark-mode',
    },
  },
})

app.mount('#app')
