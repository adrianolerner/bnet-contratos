<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'

const loading = ref(false)
const saved = ref(false)
const testLoading = ref(false)
const testEmailDialog = ref(false)
const testWahaDialog = ref(false)
const testEmailTarget = ref('')
const testWahaTarget = ref('')

watch(testWahaTarget, (newVal) => {
  if (!newVal) return
  let val = newVal.replace(/\D/g, '')
  if (val.length <= 10) {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{4})(\d)/, '$1-$2')
  } else {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{5})(\d)/, '$1-$2')
  }
  testWahaTarget.value = val.substring(0, 15)
})

const config = ref({
  nome_orgao: 'Prefeitura Municipal',
  logo_url: '',
  smtp_host: 'smtp.mail.com',
  smtp_port: 587,
  smtp_user: 'admin@prefeitura.gov',
  smtp_pass: '',
  waha_api_url: 'http://waha:3000',
  waha_api_key: '',
  waha_chat_id: '',
  waha_session: 'default',
  turnstile_enabled: false,
  turnstile_site_key: '',
  turnstile_secret_key: ''
})

async function carregarConfiguracoes() {
  try {
    const res = await api.get('/configuracoes')
    if (res.data) {
      Object.assign(config.value, res.data)
    }
  } catch (error) {
    console.error('Erro ao carregar configurações', error)
  }
}

async function save() {
  loading.value = true
  try {
    await api.put('/configuracoes', config.value)
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (error) {
    console.error('Erro ao salvar', error)
  } finally {
    loading.value = false
  }
}

function handleLogoUpload(event) {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      config.value.logo_url = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

async function testEmail() {
  if (!testEmailTarget.value) return
  testLoading.value = true
  try {
    await api.post('/configuracoes/test-email', {
      ...config.value,
      target_email: testEmailTarget.value
    })
    alert('E-mail enviado com sucesso!')
    testEmailDialog.value = false
  } catch (error) {
    alert('Erro ao enviar e-mail: ' + (error.response?.data?.detail || error.message))
  } finally {
    testLoading.value = false
  }
}

async function testWaha() {
  if (!testWahaTarget.value) return
  testLoading.value = true
  try {
    await api.post('/configuracoes/test-waha', {
      ...config.value,
      target_phone: testWahaTarget.value
    })
    alert('Mensagem enviada com sucesso!')
    testWahaDialog.value = false
  } catch (error) {
    alert('Erro ao enviar mensagem: ' + (error.response?.data?.detail || error.message))
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
  carregarConfiguracoes()
})
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-h4 font-weight-bold">Configurações do Sistema</h2>
      <p class="text-medium-emphasis">Gerencie variáveis globais e integrações</p>
    </div>

    <v-alert v-if="saved" type="success" variant="tonal" class="mb-4" closable>
      Configurações salvas com sucesso!
    </v-alert>

    <v-form @submit.prevent="save">
      <!-- Órgão -->
      <v-card rounded="xl" elevation="4" class="mb-6 bg-grey-darken-4">
        <v-card-title class="pa-4 bg-grey-darken-3 border-bottom">
          <v-icon class="mr-2">mdi-office-building</v-icon> Informações do Órgão
        </v-card-title>
        <v-card-text class="pa-6">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.nome_orgao" label="Nome do Órgão" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-file-input @change="handleLogoUpload" label="Logo / Brasão (PNG, JPG)" accept="image/*" variant="outlined" prepend-icon="mdi-image"></v-file-input>
              <div v-if="config.logo_url" class="mt-2 text-caption text-success">
                <v-icon size="small">mdi-check</v-icon> Imagem carregada ({{ config.logo_url.substring(0, 30) }}...)
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- SMTP -->
      <v-card rounded="xl" elevation="4" class="mb-6 bg-grey-darken-4">
        <v-card-title class="pa-4 bg-grey-darken-3 border-bottom d-flex align-center">
          <v-icon class="mr-2">mdi-email</v-icon> Servidor de E-mail (SMTP)
          <v-spacer></v-spacer>
          <v-btn size="small" variant="tonal" color="info" prepend-icon="mdi-send" @click="testEmailDialog = true">Testar Envio</v-btn>
        </v-card-title>
        <v-card-text class="pa-6">
          <v-row>
            <v-col cols="12" md="8">
              <v-text-field v-model="config.smtp_host" label="Host SMTP" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="config.smtp_port" label="Porta" type="number" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.smtp_user" label="Usuário SMTP" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.smtp_pass" label="Senha SMTP" type="password" variant="outlined"></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- WAHA (WhatsApp) -->
      <v-card rounded="xl" elevation="4" class="mb-6 bg-grey-darken-4">
        <v-card-title class="pa-4 bg-grey-darken-3 border-bottom d-flex align-center">
          <v-icon class="mr-2">mdi-whatsapp</v-icon> Integração WhatsApp (WAHA)
          <v-spacer></v-spacer>
          <v-btn size="small" variant="tonal" color="success" prepend-icon="mdi-send" @click="testWahaDialog = true">Testar Disparo</v-btn>
        </v-card-title>
        <v-card-text class="pa-6">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.waha_api_url" label="URL da API (WAHA)" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.waha_api_key" label="Chave da API" type="password" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.waha_chat_id" label="Chat ID (ex: 123456@c.us)" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.waha_session" label="Nome da Sessão" variant="outlined"></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Turnstile -->
      <v-card rounded="xl" elevation="4" class="mb-6 bg-grey-darken-4">
        <v-card-title class="pa-4 bg-grey-darken-3 border-bottom d-flex align-center">
          <v-icon class="mr-2">mdi-shield-check</v-icon> Cloudflare Turnstile
          <v-spacer></v-spacer>
          <v-switch v-model="config.turnstile_enabled" color="success" hide-details density="compact"></v-switch>
        </v-card-title>
        <v-card-text class="pa-6" v-if="config.turnstile_enabled">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.turnstile_site_key" label="Site Key" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="config.turnstile_secret_key" label="Secret Key" type="password" variant="outlined"></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <div class="d-flex justify-end mb-6">
        <v-btn type="submit" color="primary" size="large" :loading="loading" prepend-icon="mdi-content-save">
          Salvar Configurações
        </v-btn>
      </div>
    </v-form>

    <!-- Modal Teste Email -->
    <v-dialog v-model="testEmailDialog" max-width="400px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">Testar Configuração SMTP</v-card-title>
        <v-card-text class="px-6 pb-2">
          <p class="text-caption mb-4">Insira um e-mail de destino para testar. Lembre-se de verificar sua caixa de spam.</p>
          <v-text-field v-model="testEmailTarget" label="E-mail de Teste" variant="outlined" density="compact" type="email"></v-text-field>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn color="grey-lighten-1" variant="text" @click="testEmailDialog = false">Cancelar</v-btn>
          <v-btn color="info" variant="flat" :loading="testLoading" @click="testEmail">Enviar Teste</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Modal Teste WAHA -->
    <v-dialog v-model="testWahaDialog" max-width="400px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">Testar Configuração WAHA</v-card-title>
        <v-card-text class="px-6 pb-2">
          <p class="text-caption mb-4">Insira um número de telefone com DDD (somente números, ex: 5511999999999) para testar o envio de mensagem.</p>
          <v-text-field v-model="testWahaTarget" label="Telefone de Teste" variant="outlined" density="compact" type="text"></v-text-field>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn color="grey-lighten-1" variant="text" @click="testWahaDialog = false">Cancelar</v-btn>
          <v-btn color="success" variant="flat" :loading="testLoading" @click="testWaha">Enviar Teste</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
