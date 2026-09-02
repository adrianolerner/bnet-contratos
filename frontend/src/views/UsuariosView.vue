<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})
const showPassword = ref(false)

const errorDialog = ref(false)
const errorMessage = ref('')

function showError(msg) {
  errorMessage.value = msg
  errorDialog.value = true
}

const headers = [
  { title: 'Nome', key: 'nome' },
  { title: 'E-mail', key: 'email' },
  { title: 'Telefone', key: 'telefone' },
  { title: 'Privilégio', key: 'privilegio' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const usuarios = ref([])
const setoresList = ref([])
const privilegios = ['admin', 'usuario']

const formData = ref({
  id: null,
  nome: '',
  email: '',
  telefone: '',
  privilegio: 'usuario',
  password: '',
  setores_ids: []
})

function gerarSenha() {
  const letras = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
  const numeros = "0123456789"
  const simbolos = "@#$%&*!?"
  
  let senha = ""
  senha += letras[Math.floor(Math.random() * letras.length)]
  senha += letras[Math.floor(Math.random() * letras.length)]
  senha += letras[Math.floor(Math.random() * letras.length)]
  senha += numeros[Math.floor(Math.random() * numeros.length)]
  senha += numeros[Math.floor(Math.random() * numeros.length)]
  senha += simbolos[Math.floor(Math.random() * simbolos.length)]
  
  // preencher até 8
  const todos = letras + numeros + simbolos
  while (senha.length < 8) {
    senha += todos[Math.floor(Math.random() * todos.length)]
  }
  
  // Embaralhar
  senha = senha.split('').sort(() => 0.5 - Math.random()).join('')
  
  formData.value.password = senha
  showPassword.value = true
}

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
    const [resUsuarios, resSetores] = await Promise.all([
      api.get('/usuarios'),
      api.get('/setores')
    ])
    usuarios.value = resUsuarios.data
    setoresList.value = resSetores.data
  } catch (error) {
    console.error('Erro ao carregar dados', error)
  } finally {
    loading.value = false
  }
}

function viewItem(item) {
  viewData.value = item
  viewDialog.value = true
}

function openNew() {
  isEditing.value = false
  formData.value = { 
    id: null, nome: '', email: '', telefone: '', privilegio: 'usuario', password: '', setores_ids: [] 
  }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { 
    id: item.id, 
    nome: item.nome, 
    email: item.email, 
    telefone: item.telefone, 
    privilegio: item.privilegio, 
    password: '', 
    setores_ids: item.setores.map(s => s.id) 
  }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o usuário ${item.nome}?`)) {
    try {
      await api.delete(`/usuarios/${item.id}`)
      await carregarDados()
    } catch (error) {
      showError(error.response?.data?.detail || 'Erro ao excluir usuário.')
    }
  }
}

async function save() {
  try {
    if (isEditing.value) {
      await api.put(`/usuarios/${formData.value.id}`, formData.value)
    } else {
      await api.post('/usuarios', formData.value)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    showError(error.response?.data?.detail || 'Erro ao salvar usuário.')
  }
}

function printPDF() {
  const columns = ['Nome', 'E-mail', 'Telefone', 'Privilégio']
  const rows = usuarios.value.map(u => [
    u.nome,
    u.email,
    u.telefone,
    u.privilegio
  ])
  exportToPDF('Relatório de Usuários', columns, rows)
}

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div>
    <!-- Modal Erro -->
    <v-dialog v-model="errorDialog" max-width="400px">
      <v-card class="bg-grey-darken-4 rounded-xl text-center pb-4">
        <v-card-text class="pt-6">
          <v-icon size="64" color="error" class="mb-4">mdi-alert-circle-outline</v-icon>
          <div class="text-h6 mb-2">Ops, algo deu errado!</div>
          <div class="text-body-1 text-medium-emphasis">{{ errorMessage }}</div>
        </v-card-text>
        <v-card-actions class="justify-center">
          <v-btn color="error" variant="flat" class="px-6" @click="errorDialog = false">Entendi</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Gerenciamento de Usuários</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-account-plus" class="mr-3" @click="openNew">Novo Usuário</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Buscar usuários..."
          single-line
          hide-details
          variant="solo-filled"
          density="compact"
          class="w-50"
        ></v-text-field>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="usuarios"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.privilegio="{ item }">
          <v-chip 
            :color="item.privilegio === 'admin' ? 'purple' : 'info'"
            size="small"
            class="text-white"
          >
            {{ item.privilegio.toUpperCase() }}
          </v-chip>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-tooltip text="Visualizar" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-eye" size="small" variant="text" color="info" @click="viewItem(item)"></v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="Editar" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-pencil" size="small" variant="text" color="warning" @click="editItem(item)"></v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="Excluir" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"></v-btn>
            </template>
          </v-tooltip>
        </template>
      </v-data-table>
    </v-card>

    <!-- Modal Novo Usuário -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Usuário' : 'Cadastrar Usuário' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12" sm="12">
              <v-text-field v-model="formData.nome" label="Nome Completo" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.email" label="E-mail" type="email" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.telefone" label="Telefone (WhatsApp)" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-select v-model="formData.privilegio" :items="privilegios" label="Nível de Acesso" variant="outlined"></v-select>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field 
                v-model="formData.password" 
                label="Senha" 
                :type="showPassword ? 'text' : 'password'" 
                variant="outlined" 
                :placeholder="isEditing ? 'Preencha para alterar' : ''"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
              >
                <template v-slot:append>
                  <v-tooltip text="Gerar Senha Aleatória">
                    <template v-slot:activator="{ props }">
                      <v-btn icon="mdi-dice-multiple" variant="tonal" color="primary" v-bind="props" @click="gerarSenha"></v-btn>
                    </template>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>
            <v-col cols="12">
              <v-autocomplete
                v-model="formData.setores_ids"
                :items="setoresList"
                item-title="nome"
                item-value="id"
                label="Setores Permitidos"
                variant="outlined"
                multiple
                chips
                closable-chips
              ></v-autocomplete>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn color="grey-lighten-1" variant="text" @click="dialog = false">Cancelar</v-btn>
          <v-btn color="primary" variant="flat" @click="save">Salvar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Modal Visualizar -->
    <v-dialog v-model="viewDialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6 d-flex align-center justify-space-between">
          <span class="text-h5">Detalhes do Usuário</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Nome Completo</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.nome }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">E-mail</div>
              <div class="text-body-1">{{ viewData.email || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Telefone</div>
              <div class="text-body-1">{{ viewData.telefone || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Privilégio</div>
              <v-chip size="small" :color="viewData.privilegio === 'admin' ? 'green' : 'info'">
                {{ viewData.privilegio ? viewData.privilegio.toUpperCase() : '-' }}
              </v-chip>
            </v-col>
            <v-col cols="12" sm="12">
              <v-divider class="my-2"></v-divider>
              <div class="text-caption text-medium-emphasis mb-1">Setores Vinculados</div>
              <div v-if="viewData.setores && viewData.setores.length > 0">
                <v-chip v-for="setor in viewData.setores" :key="setor.id" class="mr-2 mb-2" size="small" variant="tonal">
                  {{ setor.nome }}
                </v-chip>
              </div>
              <div v-else class="text-body-2 text-medium-emphasis">Nenhum setor vinculado.</div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>
