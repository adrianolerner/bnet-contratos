import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { pt } from 'vuetify/locale'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  locale: {
    locale: 'pt',
    fallback: 'pt',
    messages: { pt }
  },
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#1867C0',
          secondary: '#5CBBF6',
          success: '#4CAF50',
          warning: '#FB8C00',
          error: '#FF5252',
          info: '#2196F3',
          'green-light': '#81C784',
          'green-dark': '#2E7D32',
          'yellow': '#FDD835',
          'red': '#E53935',
        },
      },
    },
  },
})

import App from './App.vue'
import router from './router'

const app = createApp(App)

import money from 'v-money3'

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(money)

app.mount('#app')
