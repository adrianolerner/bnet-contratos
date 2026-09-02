<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { useRoute } from 'vue-router'
import { store } from '@/store'
import { computed } from 'vue'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const errorDialog = ref(false)
const errorMessage = ref('')
const snackbar = ref({ show: false, text: '' })

function showError(msg) {
  errorMessage.value = msg
  errorDialog.value = true
}

function copyToClipboard(text, fieldName) {
  if (!text) return
  navigator.clipboard.writeText(text)
  snackbar.value = { show: true, text: `${fieldName} copiado para a área de transferência!` }
}

const viewData = ref({})
const showFavorites = ref(false)
const filtroFornecedor = ref(null)

const route = useRoute()

const headers = [
  { title: 'Fornecedor', key: 'fornecedor.nome_fantasia' },
  { title: 'Nome do Contato', key: 'nome' },
  { title: 'Setor', key: 'setor' },
  { title: 'Telefone', key: 'telefone' },
  { title: 'E-mail', key: 'email' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const contatos = ref([])
const fornecedoresList = ref([])

const filteredContatos = computed(() => {
  let result = contatos.value
  
  if (showFavorites.value) {
    result = result.filter(c => isFavorito(c.id))
  }
  
  if (filtroFornecedor.value) {
    result = result.filter(c => c.fornecedor_id === filtroFornecedor.value)
  }
  
  return result
})

function isFavorito(id) {
  return store.favoritos?.some(fav => fav.tipo === 'contato' && fav.entidade_id === id)
}

async function toggleFavorito(item) {
  const fav = store.favoritos?.find(f => f.tipo === 'contato' && f.entidade_id === item.id)
  try {
    if (fav) {
      await api.delete(`/favoritos/contato/${item.id}`)
      store.favoritos = store.favoritos.filter(f => f.id !== fav.id)
    } else {
      const res = await api.post('/favoritos', { tipo: 'contato', entidade_id: item.id })
      store.favoritos.push(res.data)
    }
  } catch (error) {
    console.error('Erro ao alternar favorito', error)
  }
}

const formData = ref({
  id: null,
  fornecedor_id: null,
  nome: '',
  setor: '',
  telefone: '',
  email: '',
  observacao: ''
})

async function carregarDados() {
  loading.value = true
  try {
    const [resContatos, resFornecedores] = await Promise.all([
      api.get('/contatos'),
      api.get('/fornecedores')
    ])
    contatos.value = resContatos.data
    fornecedoresList.value = resFornecedores.data
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
  formData.value = { id: null, fornecedor_id: null, nome: '', setor: '', telefone: '', email: '', observacao: '' }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o contato ${item.nome}?`)) {
    try {
      await api.delete(`/contatos/${item.id}`)
      await carregarDados()
    } catch (error) {
      showError(error.response?.data?.detail || 'Erro ao excluir contato.')
    }
  }
}

function formatPhone() {
  let val = formData.value.telefone.replace(/\D/g, '')
  if (val.length <= 10) {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{4})(\d)/, '$1-$2')
  } else {
    val = val.replace(/^(\d{2})(\d)/, '($1) $2')
    val = val.replace(/(\d{5})(\d)/, '$1-$2')
  }
  formData.value.telefone = val.substring(0, 15)
}

async function save() {
  try {
    if (isEditing.value) {
      await api.put(`/contatos/${formData.value.id}`, formData.value)
    } else {
      await api.post('/contatos', formData.value)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    showError(error.response?.data?.detail || 'Erro ao salvar contato.')
  }
}

function printPDF() {
  const columns = ['Fornecedor', 'Nome do Contato', 'Setor', 'Telefone', 'E-mail']
  const rows = filteredContatos.value.map(c => [
    c.fornecedor?.nome_fantasia || '',
    c.nome,
    c.setor,
    c.telefone,
    c.email
  ])
  exportToPDF('Relatório de Contatos', columns, rows)
}

watch(() => route.query, (newQuery) => {
  if (newQuery.fornecedor_id) filtroFornecedor.value = Number(newQuery.fornecedor_id)
  else filtroFornecedor.value = null
}, { immediate: true })

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div>
    <!-- Snackbar para cópia -->
    <v-snackbar v-model="snackbar.show" :timeout="2000" color="success">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="snackbar.show = false">Fechar</v-btn>
      </template>
    </v-snackbar>

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
      <h2 class="text-h4 font-weight-bold">Contatos dos Fornecedores</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Novo Contato</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-row class="ma-0 w-100 d-flex align-center">
          <v-col cols="12" sm="4" class="pa-1">
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Buscar contatos..."
              single-line
              hide-details
              variant="solo-filled"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="4" class="pa-1">
            <v-autocomplete
              v-model="filtroFornecedor"
              :items="[{ id: null, nome_fantasia: 'Todos os Fornecedores' }, ...fornecedoresList]"
              item-title="nome_fantasia"
              item-value="id"
              label="Filtrar por Fornecedor"
              variant="solo-filled"
              density="compact"
              hide-details
            ></v-autocomplete>
          </v-col>
          <v-col cols="12" sm="4" class="pa-1 d-flex align-center">
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
        :items="filteredContatos"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.telefone="{ item }">
          <div class="d-flex align-center">
            {{ item.telefone }}
            <v-btn v-if="item.telefone" icon="mdi-content-copy" size="x-small" variant="text" class="ml-1" color="grey" @click.stop="copyToClipboard(item.telefone, 'Telefone')" title="Copiar"></v-btn>
          </div>
        </template>
        <template v-slot:item.email="{ item }">
          <div class="d-flex align-center">
            {{ item.email }}
            <v-btn v-if="item.email" icon="mdi-content-copy" size="x-small" variant="text" class="ml-1" color="grey" @click.stop="copyToClipboard(item.email, 'E-mail')" title="Copiar"></v-btn>
          </div>
        </template>
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

    <!-- Modal Novo Contato -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Contato' : 'Cadastrar Contato' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12">
              <v-autocomplete
                v-model="formData.fornecedor_id"
                :items="fornecedoresList"
                item-title="nome_fantasia"
                item-value="id"
                label="Fornecedor Vinculado"
                variant="outlined"
              ></v-autocomplete>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.nome" label="Nome" variant="outlined" maxlength="60"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.setor" label="Setor do Contato" variant="outlined" maxlength="60"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field 
                v-model="formData.telefone" 
                label="Telefone" 
                variant="outlined" 
                @input="formatPhone"
                placeholder="(42) 99999-9999"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.email" label="E-mail" type="email" variant="outlined" maxlength="90"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="formData.observacao" label="Observações" variant="outlined" rows="2" maxlength="120"></v-textarea>
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
          <span class="text-h5">Detalhes do Contato</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Nome do Contato</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.nome }}</div>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Fornecedor Vinculado</div>
              <div class="text-body-1">{{ viewData.fornecedor?.nome_fantasia || viewData.fornecedor?.razao_social || 'Nenhum' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Setor</div>
              <div class="text-body-1">{{ viewData.setor || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Telefone</div>
              <div class="text-body-1 d-flex align-center">
                {{ viewData.telefone || '-' }}
                <v-btn v-if="viewData.telefone" icon="mdi-content-copy" size="x-small" variant="text" class="ml-1" color="grey" @click="copyToClipboard(viewData.telefone, 'Telefone')" title="Copiar"></v-btn>
              </div>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">E-mail</div>
              <div class="text-body-1 d-flex align-center">
                {{ viewData.email || '-' }}
                <v-btn v-if="viewData.email" icon="mdi-content-copy" size="x-small" variant="text" class="ml-1" color="grey" @click="copyToClipboard(viewData.email, 'E-mail')" title="Copiar"></v-btn>
              </div>
            </v-col>
            <v-col cols="12">
              <v-divider class="my-2"></v-divider>
              <div class="text-caption text-medium-emphasis mb-1">Observações</div>
              <div class="text-body-2 text-pre-wrap">{{ viewData.observacao || 'Nenhuma observação cadastrada.' }}</div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>
