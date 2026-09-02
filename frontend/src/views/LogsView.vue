<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const search = ref('')
const loading = ref(false)
const logs = ref([])

const headers = [
  { title: 'Data/Hora', key: 'data_hora', value: item => formatDate(item.data_hora) },
  { title: 'Usuário', key: 'usuario_id', value: item => item.usuario?.nome || item.usuario?.email || String(item.usuario_id) },
  { title: 'Ação', key: 'acao' },
  { title: 'Entidade', key: 'entidade' },
  { title: 'Registro ID', key: 'registro_id' },
  { title: 'Detalhes', key: 'detalhes' },
]

async function loadLogs() {
  loading.value = true
  try {
    const res = await api.get('/logs')
    logs.value = res.data
  } catch (error) {
    console.error('Erro ao carregar logs:', error)
  } finally {
    loading.value = false
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '-'
  try {
    return new Date(isoStr).toLocaleString('pt-BR')
  } catch {
    return isoStr
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Logs de Auditoria</h2>
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="loadLogs">Atualizar</v-btn>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Buscar nos logs..."
          single-line
          hide-details
          variant="solo-filled"
          density="compact"
          class="w-50"
        ></v-text-field>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="logs"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.data_hora="{ item }">
          {{ formatDate(item.data_hora) }}
        </template>
        <template v-slot:item.usuario_id="{ item }">
          {{ item.usuario?.nome || item.usuario?.email || item.usuario_id }}
        </template>
        <template v-slot:item.acao="{ item }">
          <v-chip 
            size="small" 
            :color="item.acao === 'CRIOU' ? 'success' : item.acao === 'ATUALIZOU' ? 'info' : item.acao === 'DELETOU' ? 'error' : 'default'"
          >
            {{ item.acao }}
          </v-chip>
        </template>
        <template v-slot:item.registro_id="{ item }">
          {{ item.registro_id || '-' }}
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>
