<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/api'
import { store } from '@/store'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})

const headers = [
  { title: 'Nome', key: 'nome' },
  { title: 'Nº Processo', key: 'numero_processo' },
  { title: 'Responsável', key: 'responsavel.nome' },
  { title: 'Status', key: 'status' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const processos = ref([])
const usuariosList = ref([])

const showFavorites = ref(false)
const filtroUsuario = ref(null)
const filtroMeusProcessos = ref(false)

const filteredProcessos = computed(() => {
  let result = processos.value

  if (showFavorites.value) {
    result = result.filter(p => isFavorito(p.id))
  }

  if (filtroMeusProcessos.value) {
    result = result.filter(p => p.responsavel_id === store.usuarioAuth?.id)
  } else if (filtroUsuario.value) {
    result = result.filter(p => p.responsavel_id === filtroUsuario.value)
  }

  return result
})

function isFavorito(id) {
  return store.favoritos?.some(fav => fav.tipo === 'processo' && fav.entidade_id === id)
}

async function toggleFavorito(item) {
  const fav = store.favoritos?.find(f => f.tipo === 'processo' && f.entidade_id === item.id)
  try {
    if (fav) {
      await api.delete(`/favoritos/processo/${item.id}`)
      store.favoritos = store.favoritos.filter(f => f.id !== fav.id)
    } else {
      const res = await api.post('/favoritos', { tipo: 'processo', entidade_id: item.id })
      store.favoritos.push(res.data)
    }
  } catch (error) {
    console.error('Erro ao alternar favorito', error)
  }
}

const statusOptions = ['Não inciada', 'Em execução', 'Bloqueada', 'Concluido', 'Cancelada']

const formData = ref({
  id: null,
  setor_id: null,
  nome: '',
  numero_processo: '',
  responsavel_id: null,
  status: 'Não inciada',
  observacoes: ''
})

async function carregarUsuarios() {
  if (!store.setorAtivo) return
  try {
    const res = await api.get(`/setores/${store.setorAtivo}/usuarios`)
    usuariosList.value = res.data
  } catch (e) {
    console.error('Erro ao carregar usuários do setor', e)
  }
}

async function carregarDados() {
  if (!store.setorAtivo) return
  loading.value = true
  try {
    const [resProcessos] = await Promise.all([
      api.get(`/processos?setor_id=${store.setorAtivo}`)
    ])
    processos.value = resProcessos.data
  } catch (error) {
    console.error('Erro ao carregar dados', error)
  } finally {
    loading.value = false
  }
}

watch(() => store.setorAtivo, (newVal) => {
  if (newVal) {
    carregarDados()
    carregarUsuarios()
  }
})

function viewItem(item) {
  viewData.value = item
  viewDialog.value = true
}

function openNew() {
  isEditing.value = false
  formData.value = { 
    id: null, setor_id: store.setorAtivo, nome: '', numero_processo: '', responsavel_id: null, status: 'Não inciada', observacoes: '' 
  }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o processo ${item.numero_processo}?`)) {
    try {
      await api.delete(`/processos/${item.id}`)
      await carregarDados()
    } catch (error) {
      console.error('Erro ao deletar', error)
    }
  }
}

async function save() {
  try {
    if (isEditing.value) {
      await api.put(`/processos/${formData.value.id}`, formData.value)
    } else {
      await api.post('/processos', formData.value)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    console.error('Erro ao salvar processo', error)
  }
}

function printPDF() {
  const columns = ['Nº Processo', 'Nome', 'Status', 'Observações']
  const rows = processos.value.map(p => [
    p.numero_processo,
    p.nome,
    p.status,
    p.observacoes || ''
  ])
  exportToPDF('Relatório de Processos', columns, rows)
}

onMounted(() => {
  if (store.setorAtivo) {
    carregarDados()
    carregarUsuarios()
  }
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Controle de Processos</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Novo Processo</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-row no-gutters class="w-100">
          <v-col cols="12" sm="4" class="pa-1">
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Buscar processos..."
              single-line
              hide-details
              variant="solo-filled"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="3" class="pa-1">
            <v-autocomplete
              v-model="filtroUsuario"
              :items="[{ id: null, nome: 'Todos os Responsáveis' }, ...usuariosList]"
              item-title="nome"
              item-value="id"
              label="Filtrar por Responsável"
              variant="solo-filled"
              density="compact"
              hide-details
              :disabled="filtroMeusProcessos"
            ></v-autocomplete>
          </v-col>
          <v-col cols="12" sm="5" class="pa-1 d-flex align-center justify-end">
            <v-switch
              v-model="showFavorites"
              color="amber-darken-2"
              hide-details
              density="compact"
              label="Apenas Favoritos"
              class="mr-4"
            ></v-switch>

            <v-switch
              v-model="filtroMeusProcessos"
              color="amber-darken-2"
              hide-details
              density="compact"
              label="Meus Processos"
            ></v-switch>
          </v-col>
        </v-row>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="filteredProcessos"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.status="{ item }">
          <v-chip 
            :color="item.status === 'Concluido' ? 'success' : item.status === 'Em execução' ? 'info' : item.status === 'Bloqueada' ? 'error' : 'grey'"
            size="small"
          >
            {{ item.status }}
          </v-chip>
        </template>
        <template v-slot:item.responsavel.nome="{ item }">
          {{ item.responsavel?.nome || '-' }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn 
            icon 
            variant="text" 
            size="small"
            :color="isFavorito(item.id) ? 'warning' : 'grey'"
            @click="toggleFavorito(item)"
          >
            <v-icon>{{ isFavorito(item.id) ? 'mdi-star' : 'mdi-star-outline' }}</v-icon>
          </v-btn>
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

    <!-- Modal Novo Processo -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Processo' : 'Novo Processo' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12" sm="8">
              <v-text-field v-model="formData.nome" label="Nome do Processo" variant="outlined" maxlength="60"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.numero_processo" label="Nº Processo" variant="outlined" placeholder="0000/0000" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-autocomplete
                v-model="formData.responsavel_id"
                :items="usuariosList"
                item-title="nome"
                item-value="id"
                label="Responsável"
                variant="outlined"
                clearable
              ></v-autocomplete>
            </v-col>
            <v-col cols="12" sm="6">
              <v-select v-model="formData.status" :items="statusOptions" label="Status" variant="outlined"></v-select>
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
          <span class="text-h5">Detalhes do Processo</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="8">
              <div class="text-caption text-medium-emphasis mb-1">Nome do Processo</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.nome }}</div>
            </v-col>
            <v-col cols="12" sm="4">
              <div class="text-caption text-medium-emphasis mb-1">Nº Processo</div>
              <div class="text-body-1 font-weight-bold">{{ viewData.numero_processo || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="8">
              <div class="text-caption text-medium-emphasis mb-1">Situação</div>
              <v-chip size="small" :color="viewData.status === 'Concluido' ? 'success' : viewData.status === 'Em execução' ? 'info' : viewData.status === 'Bloqueada' ? 'error' : 'grey'">
                {{ viewData.status }}
              </v-chip>
            </v-col>
            <v-col cols="12" sm="4">
              <div class="text-caption text-medium-emphasis mb-1">Setor</div>
              <div class="text-body-1">{{ viewData.setor?.nome || 'Geral' }}</div>
            </v-col>
            <v-col cols="12" sm="4">
              <div class="text-caption text-medium-emphasis mb-1">Responsável</div>
              <div class="text-body-1">{{ viewData.responsavel?.nome || '-' }}</div>
            </v-col>
            <v-col cols="12">
              <v-divider class="my-2"></v-divider>
              <div class="text-caption text-medium-emphasis mb-1">Observações</div>
              <div class="text-body-2 text-pre-wrap">{{ viewData.observacoes || 'Nenhuma observação cadastrada.' }}</div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>
