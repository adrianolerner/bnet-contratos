<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { store } from '@/store'

const formData = ref({
  nome: '',
  email: '',
  telefone: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

watch(() => formData.value.telefone, (newVal) => {
  if (!newVal) return
  let val = newVal.replace(/\D/g, '')
  if (val.length <= 10) {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{4})(\d)/, '$1-$2')
  } else {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{5})(\d)/, '$1-$2')
  }
  formData.value.telefone = val.substring(0, 15)
})

async function carregarDados() {
  loading.value = true
  try {
    const res = await api.get('/auth/me')
    formData.value.nome = res.data.nome
    formData.value.email = res.data.email
    formData.value.telefone = res.data.telefone || ''
  } catch (err) {
    error.value = 'Erro ao carregar os dados do perfil.'
  } finally {
    loading.value = false
  }
}

async function save() {
  error.value = ''
  success.value = ''
  
  if (formData.value.password && formData.value.password !== formData.value.confirmPassword) {
    error.value = 'As senhas não coincidem.'
    return
  }

  loading.value = true
  try {
    const payload = {
      nome: formData.value.nome,
      email: formData.value.email,
      telefone: formData.value.telefone
    }
    
    if (formData.value.password) {
      payload.password = formData.value.password
    }
    
    const res = await api.put('/auth/me', payload)
    store.usuarioAuth = res.data // atualiza no store global
    success.value = 'Perfil atualizado com sucesso!'
    formData.value.password = ''
    formData.value.confirmPassword = ''
  } catch (err) {
    error.value = err.response?.data?.detail || 'Erro ao atualizar o perfil.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div>
    <h2 class="text-h4 font-weight-bold mb-6">Meu Perfil</h2>
    
    <v-card rounded="xl" elevation="4" class="pa-6 mx-auto bg-grey-darken-4" max-width="600">
      <v-alert v-if="error" type="error" density="compact" class="mb-4" variant="tonal">
        {{ error }}
      </v-alert>
      <v-alert v-if="success" type="success" density="compact" class="mb-4" variant="tonal">
        {{ success }}
      </v-alert>

      <v-form @submit.prevent="save">
        <v-text-field
          v-model="formData.nome"
          label="Nome Completo"
          variant="outlined"
          class="mb-3"
          required
        ></v-text-field>

        <v-text-field
          v-model="formData.email"
          label="E-mail"
          type="email"
          variant="outlined"
          class="mb-3"
          required
        ></v-text-field>

        <v-text-field
          v-model="formData.telefone"
          label="Telefone / WhatsApp"
          variant="outlined"
          class="mb-3"
        ></v-text-field>

        <v-divider class="my-4"></v-divider>
        <p class="text-caption text-medium-emphasis mb-3">Preencha apenas se quiser alterar sua senha:</p>

        <v-text-field
          v-model="formData.password"
          label="Nova Senha"
          type="password"
          variant="outlined"
          class="mb-3"
        ></v-text-field>

        <v-text-field
          v-model="formData.confirmPassword"
          label="Confirmar Nova Senha"
          type="password"
          variant="outlined"
          class="mb-6"
        ></v-text-field>

        <div class="d-flex justify-end">
          <v-btn color="primary" type="submit" :loading="loading" size="large">
            Salvar Alterações
          </v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>
