<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})

const headers = [
  { title: 'ID', key: 'id' },
  { title: 'Nome do Setor', key: 'nome' },
  { title: 'Observação', key: 'observacao' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const setores = ref([])

const formData = ref({
  id: null,
  nome: '',
  observacao: ''
})

async function carregarDados() {
  loading.value = true
  try {
    const res = await api.get('/setores')
    setores.value = res.data
  } catch (error) {
    console.error('Erro ao carregar setores', error)
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
  formData.value = { id: null, nome: '', observacao: '' }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o setor ${item.nome}?`)) {
    try {
      await api.delete(`/setores/${item.id}`)
      await carregarDados()
    } catch (error) {
      console.error('Erro ao deletar', error)
    }
  }
}

async function save() {
  try {
    if (isEditing.value) {
      await api.put(`/setores/${formData.value.id}`, formData.value)
    } else {
      await api.post('/setores', formData.value)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    console.error('Erro ao salvar setor', error)
  }
}

function printPDF() {
  const columns = ['ID', 'Nome do Setor', 'Observação']
  const rows = setores.value.map(s => [s.id, s.nome, s.observacao || ''])
  exportToPDF('Relatório de Setores', columns, rows)
}

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Gestão de Setores</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Novo Setor</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Buscar setores..."
          single-line
          hide-details
          variant="solo-filled"
          density="compact"
          class="w-50"
        ></v-text-field>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="setores"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
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

    <!-- Modal Novo Setor -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Setor' : 'Cadastrar Setor' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12">
              <v-text-field v-model="formData.nome" label="Nome do Setor" variant="outlined" maxlength="100"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="formData.observacao" label="Observações" variant="outlined" rows="3"></v-textarea>
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
          <span class="text-h5">Detalhes do Setor</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Nome do Setor</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.nome }}</div>
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
