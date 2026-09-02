<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { store } from '@/store'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})

const moneyConfig = {
  masked: false,
  prefix: 'R$ ',
  suffix: '',
  thousands: '.',
  decimal: ',',
  precision: 2,
  disableNegative: false,
  disabled: false,
  min: null,
  max: null,
  allowBlank: false,
  minimumNumberOfCharacters: 0,
}

const headers = [
  { title: 'Fornecedor', key: 'fornecedor.nome_fantasia' },
  { title: 'Nº Nota', key: 'numero_nota' },
  { title: 'Valor', key: 'valor' },
  { title: 'Vencimento', key: 'data_vencimento' },
  { title: 'Status', key: 'status_pagamento' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const pagamentos = ref([])
const fornecedoresList = ref([])
const setoresList = ref([])

const statusOptions = ['Pago', 'Pendente', 'Em processo', 'Cancelado']

const formData = ref({
  id: null,
  fornecedor_id: null,
  setor_id: null,
  numero_nota: '',
  valor: 0,
  numero_empenho: '',
  numero_ordem_compra: '',
  data_nota: '',
  data_vencimento: '',
  item: '',
  status_pagamento: 'Pendente',
  numero_processo_pagamento: '',
  observacao: ''
})

async function carregarDados() {
  if (!store.setorAtivo) return
  loading.value = true
  try {
    const [resPagamentos, resFornecedores] = await Promise.all([
      api.get(`/pagamentos?setor_id=${store.setorAtivo}`),
      api.get('/fornecedores')
    ])
    pagamentos.value = resPagamentos.data
    fornecedoresList.value = resFornecedores.data
  } catch (error) {
    console.error('Erro ao carregar dados', error)
  } finally {
    loading.value = false
  }
}

watch(() => store.setorAtivo, (newVal) => {
  if (newVal) carregarDados()
})

function formatData(dataStr) {
  if(!dataStr) return ''
  const [y, m, d] = dataStr.split('-')
  return `${d}/${m}/${y}`
}

function formatCurrency(value) {
  if (!value) return 'R$ 0,00'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function viewItem(item) {
  viewData.value = item
  viewDialog.value = true
}

function openNew() {
  isEditing.value = false
  formData.value = { 
    id: null, fornecedor_id: null, setor_id: store.setorAtivo, numero_nota: '', valor: 0, 
    numero_empenho: '', numero_ordem_compra: '', data_nota: '', data_vencimento: '', 
    item: '', status_pagamento: 'Pendente', numero_processo_pagamento: '', observacao: '' 
  }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o pagamento da nota ${item.numero_nota}?`)) {
    try {
      await api.delete(`/pagamentos/${item.id}`)
      await carregarDados()
    } catch (error) {
      console.error('Erro ao deletar', error)
    }
  }
}

async function save() {
  try {
    const payload = { ...formData.value }
    if (typeof payload.valor === 'string') {
      payload.valor = parseFloat(payload.valor.replace(/[R$\s\.]/g, '').replace(',', '.')) || 0
    }
    
    if (isEditing.value) {
      await api.put(`/pagamentos/${payload.id}`, payload)
    } else {
      await api.post('/pagamentos', payload)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    console.error('Erro ao salvar pagamento', error)
  }
}

function printPDF() {
  const columns = ['Fornecedor', 'Nº Nota', 'Valor', 'Vencimento', 'Status']
  const rows = pagamentos.value.map(p => [
    p.fornecedor?.nome_fantasia || '',
    p.numero_nota,
    `R$ ${p.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    formatData(p.data_vencimento),
    p.status_pagamento
  ])
  exportToPDF('Relatório de Pagamentos e Notas', columns, rows)
}

onMounted(() => {
  if (store.setorAtivo) carregarDados()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Pagamentos e Notas</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Registrar Nota</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Buscar pagamentos..."
          single-line
          hide-details
          variant="solo-filled"
          density="compact"
          class="w-50"
        ></v-text-field>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="pagamentos"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.valor="{ item }">
          R$ {{ item.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
        </template>
        <template v-slot:item.data_vencimento="{ item }">
          {{ formatData(item.data_vencimento) }}
        </template>
        <template v-slot:item.status_pagamento="{ item }">
          <v-chip 
            :color="item.status_pagamento === 'Pago' ? 'success' : item.status_pagamento === 'Pendente' ? 'warning' : item.status_pagamento === 'Em processo' ? 'info' : 'error'"
            size="small"
          >
            {{ item.status_pagamento }}
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

    <!-- Modal Nova Nota -->
    <v-dialog v-model="dialog" max-width="800px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Nota Fiscal' : 'Registrar Nota Fiscal' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12" sm="12">
              <v-autocomplete v-model="formData.fornecedor_id" :items="fornecedoresList" item-title="nome_fantasia" item-value="id" label="Fornecedor" variant="outlined"></v-autocomplete>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.numero_nota" label="Nº Nota" variant="outlined" maxlength="25"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.lazy="formData.valor" v-money3="moneyConfig" label="Valor (R$)" variant="outlined" placeholder="0,00"></v-text-field>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.numero_empenho" label="Nº Empenho" variant="outlined" placeholder="0000/0000" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.numero_ordem_compra" label="Nº Ordem Compra" variant="outlined" placeholder="0000/0000" maxlength="12"></v-text-field>
            </v-col>

            <v-col cols="12" sm="4">
              <v-select v-model="formData.status_pagamento" :items="statusOptions" label="Status Pagamento" variant="outlined"></v-select>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.data_nota" label="Data Recebimento" type="date" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.data_vencimento" label="Data Vencimento" type="date" variant="outlined"></v-text-field>
            </v-col>

            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.numero_processo_pagamento" label="Nº Processo Pag." variant="outlined" placeholder="0000/0000" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.item" label="Item" variant="outlined" maxlength="60"></v-text-field>
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
          <span class="text-h5">Detalhes do Pagamento</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Fornecedor</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.fornecedor?.nome_fantasia || viewData.fornecedor?.razao_social || 'Não informado' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Situação</div>
              <v-chip size="small" :color="viewData.status_pagamento === 'Pago' ? 'success' : viewData.status_pagamento === 'Pendente' ? 'warning' : viewData.status_pagamento === 'Em processo' ? 'info' : 'error'">
                {{ viewData.status_pagamento }}
              </v-chip>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Vencimento</div>
              <div class="text-body-1 font-weight-medium">{{ formatData(viewData.data_vencimento) }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Valor da Nota</div>
              <div class="text-body-1 font-weight-bold text-info">{{ formatCurrency(viewData.valor) }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Nº Nota Fiscal</div>
              <div class="text-body-1">{{ viewData.numero_nota || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Data Recebimento</div>
              <div class="text-body-1">{{ formatData(viewData.data_nota) || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Processo de Pagamento</div>
              <div class="text-body-1">{{ viewData.numero_processo_pagamento || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Nº Empenho / Ordem Compra</div>
              <div class="text-body-1">{{ viewData.numero_empenho || '-' }} / {{ viewData.numero_ordem_compra || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Setor</div>
              <div class="text-body-1">{{ viewData.setor?.nome || 'Geral' }}</div>
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
