<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'
import { exportToPDF } from '@/utils/pdf'
const search = ref('')
const dialog = ref(false)
const router = useRouter()
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})
const showFavorites = ref(false)

const errorDialog = ref(false)
const errorMessage = ref('')

function showError(msg) {
  errorMessage.value = msg
  errorDialog.value = true
}

const headers = [
  { title: 'Nome Fantasia', key: 'nome_fantasia' },
  { title: 'Razão Social', key: 'razao_social' },
  { title: 'CNPJ', key: 'cnpj' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const fornecedores = ref([])

const filteredFornecedores = computed(() => {
  if (!showFavorites.value) return fornecedores.value
  return fornecedores.value.filter(f => isFavorito(f.id))
})

function isFavorito(id) {
  return store.favoritos?.some(fav => fav.tipo === 'fornecedor' && fav.entidade_id === id)
}

async function toggleFavorito(item) {
  const fav = store.favoritos?.find(f => f.tipo === 'fornecedor' && f.entidade_id === item.id)
  try {
    if (fav) {
      await api.delete(`/favoritos/fornecedor/${item.id}`)
      store.favoritos = store.favoritos.filter(f => f.id !== fav.id)
    } else {
      const res = await api.post('/favoritos', { tipo: 'fornecedor', entidade_id: item.id })
      store.favoritos.push(res.data)
    }
  } catch (error) {
    console.error('Erro ao alternar favorito', error)
  }
}

const formData = ref({
  id: null,
  nome_fantasia: '',
  razao_social: '',
  cnpj: '',
  observacoes: ''
})

watch(() => formData.value.cnpj, (newVal) => {
  if (!newVal) return
  let val = newVal.replace(/\D/g, '')
  if (val.length > 2) val = val.substring(0, 2) + '.' + val.substring(2)
  if (val.length > 6) val = val.substring(0, 6) + '.' + val.substring(6)
  if (val.length > 10) val = val.substring(0, 10) + '/' + val.substring(10)
  if (val.length > 15) val = val.substring(0, 15) + '-' + val.substring(15)
  formData.value.cnpj = val.substring(0, 18)
})

async function carregarFornecedores() {
  loading.value = true
  try {
    const res = await api.get('/fornecedores')
    fornecedores.value = res.data
  } catch (error) {
    console.error('Erro ao carregar fornecedores', error)
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
  formData.value = { id: null, nome_fantasia: '', razao_social: '', cnpj: '', observacoes: '' }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir ${item.nome_fantasia}?`)) {
    try {
      await api.delete(`/fornecedores/${item.id}`)
      await carregarFornecedores()
    } catch (error) {
      showError(error.response?.data?.detail || 'Erro ao excluir fornecedor.')
    }
  }
}

async function save() {
  try {
    if (isEditing.value) {
      await api.put(`/fornecedores/${formData.value.id}`, formData.value)
    } else {
      await api.post('/fornecedores', formData.value)
    }
    dialog.value = false
    await carregarFornecedores()
  } catch (error) {
    showError(error.response?.data?.detail || 'Erro ao salvar fornecedor.')
  }
}

function printPDF() {
  const columns = ['Nome Fantasia', 'Razão Social', 'CNPJ']
  const rows = filteredFornecedores.value.map(f => [f.nome_fantasia, f.razao_social, f.cnpj])
  exportToPDF('Relatório de Fornecedores', columns, rows)
}

onMounted(() => {
  carregarFornecedores()
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
      <h2 class="text-h4 font-weight-bold">Fornecedores</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Novo Fornecedor</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-row class="ma-0 w-100 d-flex align-center">
          <v-col cols="12" sm="6" class="pa-1">
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Buscar fornecedores..."
              single-line
              hide-details
              variant="solo-filled"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6" class="pa-1 d-flex align-center">
            <v-switch
              v-model="showFavorites"
              label="Apenas Favoritos"
              color="amber-darken-2"
              hide-details
              density="compact"
            ></v-switch>
          </v-col>
        </v-row>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="filteredFornecedores"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.actions="{ item }">
          <v-tooltip :text="isFavorito(item.id) ? 'Remover Favorito' : 'Favoritar'" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon size="small" variant="text" :color="isFavorito(item.id) ? 'amber-darken-2' : 'grey'" @click="toggleFavorito(item)">
                <v-icon>{{ isFavorito(item.id) ? 'mdi-star' : 'mdi-star-outline' }}</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
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

    <!-- Modal Novo Fornecedor -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Fornecedor' : 'Cadastrar Fornecedor' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12">
              <v-text-field v-model="formData.nome_fantasia" label="Nome Fantasia" variant="outlined" maxlength="90"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="formData.razao_social" label="Razão Social" variant="outlined" maxlength="90"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.cnpj" label="CNPJ (Alfanumérico)" variant="outlined" maxlength="18"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="formData.observacoes" label="Observações" variant="outlined" rows="3" maxlength="120"></v-textarea>
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
          <span class="text-h5">Detalhes do Fornecedor</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Nome Fantasia</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.nome_fantasia }}</div>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Razão Social</div>
              <div class="text-body-1">{{ viewData.razao_social || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">CNPJ</div>
              <div class="text-body-1">{{ viewData.cnpj || '-' }}</div>
            </v-col>
            <v-col cols="12">
              <v-divider class="my-2"></v-divider>
              <div class="text-caption text-medium-emphasis mb-1">Observações</div>
              <div class="text-body-2 text-pre-wrap">{{ viewData.observacoes || 'Nenhuma observação cadastrada.' }}</div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn
            color="info"
            variant="tonal"
            prepend-icon="mdi-account-group"
            @click="router.push(`/admin/contatos?fornecedor_id=${viewData.id}`)"
            class="mr-2"
          >
            Contatos deste fornecedor
          </v-btn>
          <v-btn color="grey-lighten-1" variant="text" @click="viewDialog = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
