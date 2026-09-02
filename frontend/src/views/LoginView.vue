<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const showPassword = ref(false)
const error = ref('')
const turnstileWidget = ref(null)
const turnstileToken = ref('')

async function handleLogin() {
  if (!email.value || !password.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    // call to API /api/auth/login
    const payload = { email: email.value, password: password.value }
    if (turnstileToken.value) {
      payload.turnstile_token = turnstileToken.value
    }
    const response = await api.post('/auth/login', payload)
    localStorage.setItem('token', response.data.access_token)
    
    loading.value = false
    router.push('/admin')
    
  } catch (e) {
    error.value = 'Credenciais inválidas'
    loading.value = false
  }
}

onMounted(async () => {
  document.title = 'BNET Contratos - Login'
  try {
    const res = await api.get('/configuracoes')
    store.appConfig = res.data
    
    // Renderiza Turnstile se ativado
    if (store.appConfig?.turnstile_enabled && store.appConfig?.turnstile_site_key) {
      setTimeout(() => {
        if (window.turnstile && turnstileWidget.value) {
          window.turnstile.render(turnstileWidget.value, {
            sitekey: store.appConfig.turnstile_site_key,
            callback: function(token) {
              turnstileToken.value = token
            }
          })
        }
      }, 500)
    }
  } catch(e) {
    console.error('Erro ao buscar configs públicas')
  }
})
</script>

<template>
  <v-container fluid class="fill-height d-flex align-center justify-center bg-grey-darken-4">
    <v-card width="400" elevation="10" rounded="xl" class="pa-6 border-thin">
      <div class="text-center mb-6">
        <v-avatar v-if="store.appConfig?.logo_url" rounded="0" size="80" class="mb-3">
          <v-img :src="store.appConfig.logo_url" alt="Logo"></v-img>
        </v-avatar>
        <v-icon v-else size="60" color="primary" class="mb-3">mdi-city</v-icon>
        <h2 class="text-h5 font-weight-bold">BNET Contratos</h2>
        <p class="text-subtitle-2 text-medium-emphasis">{{ store.appConfig?.nome_orgao || 'Prefeitura Municipal' }}</p>
      </div>

      <v-alert v-if="error" type="error" density="compact" class="mb-4" variant="tonal">
        {{ error }}
      </v-alert>

      <v-form @submit.prevent="handleLogin">
        <v-text-field
          v-model="email"
          label="E-mail"
          type="email"
          variant="outlined"
          prepend-inner-icon="mdi-email"
          required
          class="mb-3"
        ></v-text-field>

        <v-text-field
          v-model="password"
          label="Senha"
          :type="showPassword ? 'text' : 'password'"
          variant="outlined"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          required
          class="mb-6"
        ></v-text-field>

        <!-- Turnstile Widget -->
        <div 
          v-if="store.appConfig?.turnstile_enabled && store.appConfig?.turnstile_site_key"
          ref="turnstileWidget"
          class="mb-4 d-flex justify-center"
        ></div>

        <v-btn
          type="submit"
          color="primary"
          size="large"
          block
          :loading="loading"
          rounded="lg"
        >
          Entrar no Sistema
        </v-btn>
      </v-form>
    </v-card>
    <div class="position-absolute bottom-0 text-center w-100 py-3 text-caption text-medium-emphasis">
      Desenvolvido por SMCTI - Castro - Adriano Lerner Biesek
    </div>
  </v-container>
</template>
