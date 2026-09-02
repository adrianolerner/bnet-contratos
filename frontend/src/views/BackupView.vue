<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const backups = ref([])
const loading = ref(false)
const search = ref('')

const headers = [
  { title: 'Arquivo', key: 'filename' },
  { title: 'Data', key: 'created_at' },
  { title: 'Tamanho', key: 'size' },
  { title: 'Ações', key: 'actions', sortable: false, align: 'end' }
]

async function loadBackups() {
  loading.value = true
  try {
    const res = await api.get('/backups')
    backups.value = res.data
  } catch (error) {
    console.error('Erro ao carregar backups', error)
  } finally {
    loading.value = false
  }
}

async function createBackup() {
  if (!confirm('Deseja gerar um novo backup do banco de dados agora?')) return
  loading.value = true
  try {
    await api.post('/backups')
    alert('Backup gerado com sucesso!')
    await loadBackups()
  } catch (error) {
    alert('Erro ao gerar backup: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

async function restoreBackup(item) {
  if (!confirm(`ATENÇÃO: Restaurar o backup ${item.filename} irá sobrescrever os dados atuais. Tem certeza?`)) return
  loading.value = true
  try {
    await api.post(`/backups/${item.filename}/restore`)
    alert('Backup restaurado com sucesso! O sistema pode precisar de alguns instantes para estabilizar as conexões.')
  } catch (error) {
    alert('Erro ao restaurar backup: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

async function deleteBackup(item) {
  if (!confirm(`Tem certeza que deseja excluir o backup ${item.filename}?`)) return
  try {
    await api.delete(`/backups/${item.filename}`)
    await loadBackups()
  } catch (error) {
    alert('Erro ao excluir: ' + (error.response?.data?.detail || error.message))
  }
}

function downloadBackup(item) {
  window.open(`${api.defaults.baseURL}/backups/${item.filename}/download?token=${localStorage.getItem('token')}`, '_blank')
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const date = new Date(isoStr)
  return date.toLocaleString('pt-BR')
}

// Upload modal
const uploadDialog = ref(false)
const uploadFile = ref(null)
const uploadLoading = ref(false)

async function doUpload() {
  if (!uploadFile.value) return
  uploadLoading.value = true
  const formData = new FormData()
  formData.append('file', uploadFile.value)
  
  try {
    await api.post('/backups/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    alert('Upload concluído com sucesso!')
    uploadDialog.value = false
    uploadFile.value = null
    await loadBackups()
  } catch(error) {
    alert('Erro no upload: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploadLoading.value = false
  }
}

onMounted(() => {
  loadBackups()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h2 class="text-h4 font-weight-bold">Gerenciador de Backups</h2>
        <p class="text-medium-emphasis">Exporte e restaure bancos de dados do sistema</p>
      </div>
      <div>
        <v-btn color="secondary" prepend-icon="mdi-upload" variant="tonal" class="mr-3" @click="uploadDialog = true">Fazer Upload</v-btn>
        <v-btn color="primary" prepend-icon="mdi-database-plus" @click="createBackup" :loading="loading">Gerar Novo Backup</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Buscar backups..."
          single-line
          hide-details
          variant="outlined"
          density="compact"
        ></v-text-field>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="backups"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-4 text-body-1"
      >
        <template v-slot:item.filename="{ item }">
          <div class="d-flex align-center">
            <v-icon color="info" class="mr-2">mdi-database</v-icon>
            {{ item.filename }}
          </div>
        </template>
        <template v-slot:item.size="{ item }">
          {{ formatBytes(item.size) }}
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-tooltip text="Baixar" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-download" size="small" variant="text" color="info" @click="downloadBackup(item)" title="Baixar Backup"></v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="Restaurar" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-restore" size="small" variant="text" color="warning" @click="restoreBackup(item)" title="Restaurar Banco de Dados"></v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="Excluir" location="top">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon="mdi-delete" size="small" variant="text" color="error" @click="deleteBackup(item)" title="Excluir Backup"></v-btn>
            </template>
          </v-tooltip>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="uploadDialog" max-width="500px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">Upload de Backup (.sql)</v-card-title>
        <v-card-text class="px-6 pb-2">
          <p class="text-caption mb-4">Selecione um arquivo de backup previamente exportado pelo sistema.</p>
          <v-file-input
            v-model="uploadFile"
            label="Arquivo de Banco de Dados"
            accept=".sql"
            variant="outlined"
            prepend-icon="mdi-database-import"
          ></v-file-input>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn color="grey-lighten-1" variant="text" @click="uploadDialog = false">Cancelar</v-btn>
          <v-btn color="primary" variant="flat" :loading="uploadLoading" @click="doUpload" :disabled="!uploadFile">Enviar Arquivo</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
