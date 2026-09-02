<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'
import { exportToPDF } from '@/utils/pdf'

const search = ref('')
const dialog = ref(false)
const viewDialog = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const viewData = ref({})

const route = useRoute()
const router = useRouter()

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
  { title: 'Nº Contrato', key: 'numero' },
  { title: 'Empenho', key: 'numero_empenho' },
  { title: 'Nº Processo', key: 'numero_processo_digital' },
  { title: 'Fornecedor', key: 'fornecedor.nome_fantasia' },
  { title: 'Serviço', key: 'servico' },
  { title: 'Vencimento', key: 'vencimento' },
  { title: 'Prazo Restante', key: 'prazo_restante' },
  { title: 'Situação', key: 'situacao' },
  { title: 'Ações', key: 'actions', sortable: false },
]

const contratos = ref([])
const fornecedoresList = ref([])
const setoresList = ref([])

const filtroSituacao = ref('Todas')
const filtroFornecedor = ref(null)
const filtroPrazo = ref('Todos')

const filteredContratos = computed(() => {
  let result = contratosComPrazo.value

  if (filtroSituacao.value !== 'Todas') {
    result = result.filter(c => c.situacao === filtroSituacao.value)
  }

  if (filtroFornecedor.value) {
    result = result.filter(c => c.fornecedor_id === filtroFornecedor.value)
  }

  if (filtroPrazo.value !== 'Todos') {
    const hoje = new Date()
    hoje.setHours(0,0,0,0)
    
    result = result.filter(c => {
      if (!c.vencimento) return false
      const [y, m, d] = c.vencimento.split('-')
      const venc = new Date(y, m - 1, d)
      
      const diffTime = venc - hoje
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (filtroPrazo.value === 'Vencidos') return diffDays < 0 && c.situacao !== 'Encerrado'
      if (filtroPrazo.value === 'Vence em 30 dias') return diffDays >= 0 && diffDays <= 30 && c.situacao !== 'Encerrado'
      if (filtroPrazo.value === 'Vence em 60 dias') return diffDays >= 0 && diffDays <= 60 && c.situacao !== 'Encerrado'
      if (filtroPrazo.value === 'Vence em 90 dias') return diffDays >= 0 && diffDays <= 90 && c.situacao !== 'Encerrado'
      
      return true
    })
  }

  return result
})

const formData = ref({
  id: null,
  numero: '',
  fornecedor_id: null,
  setor_id: null,
  servico: '',
  fiscal: '',
  vencimento: '',
  numero_empenho: '',
  numero_ordem_compra: '',
  numero_processo_digital: '',
  valor_total: 0,
  numero_licitacao: '',
  situacao: 'Em vigência',
  observacao: ''
})

const situacoesList = ['Emergencial', 'Em renovação', 'Renovado', 'Em vigência', 'Encerrado']

const contratosComPrazo = computed(() => {
  const hoje = new Date()
  return contratos.value.map(c => {
    if (c.situacao === 'Encerrado') {
      return { ...c, prazo_restante: 'N/A', color: 'grey' }
    }
    
    const dataVenc = new Date(c.vencimento)
    const diffTime = dataVenc - hoje
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    let color = 'grey'
    if (diffDays >= 90) color = '#4caf50'
    else if (diffDays >= 60 && diffDays < 90) color = '#1867c0'
    else if (diffDays >= 30 && diffDays < 60) color = 'yellow'
    else color = 'red'

    return { ...c, prazo_restante: diffDays, color }
  })
})

async function carregarDados() {
  if (!store.setorAtivo) return
  loading.value = true
  try {
    const [resContratos, resFornecedores] = await Promise.all([
      api.get(`/contratos?setor_id=${store.setorAtivo}`),
      api.get('/fornecedores')
    ])
    contratos.value = resContratos.data
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
    id: null, numero: '', fornecedor_id: null, setor_id: store.setorAtivo, servico: '', 
    fiscal: '', vencimento: '', numero_empenho: '', numero_ordem_compra: '', 
    numero_processo_digital: '', valor_total: 0, numero_licitacao: '', situacao: 'Em vigência', observacao: ''
  }
  dialog.value = true
}

function editItem(item) {
  isEditing.value = true
  formData.value = { ...item }
  dialog.value = true
}

async function deleteItem(item) {
  if(confirm(`Tem certeza que deseja excluir o contrato ${item.numero}?`)) {
    try {
      await api.delete(`/contratos/${item.id}`)
      await carregarDados()
    } catch (error) {
      console.error('Erro ao deletar', error)
    }
  }
}

async function save() {
  try {
    const payload = { ...formData.value }
    if (typeof payload.valor_total === 'string') {
      payload.valor_total = parseFloat(payload.valor_total.replace(/[R$\s\.]/g, '').replace(',', '.')) || 0
    }
    
    if (isEditing.value) {
      await api.put(`/contratos/${payload.id}`, payload)
    } else {
      await api.post('/contratos', payload)
    }
    dialog.value = false
    await carregarDados()
  } catch (error) {
    console.error('Erro ao salvar contrato', error)
  }
}

function printPDF() {
  const columns = ['Nº Contrato', 'Fornecedor', 'Serviço', 'Vencimento', 'Situação']
  const rows = filteredContratos.value.map(c => [
    c.numero, 
    c.fornecedor?.nome_fantasia || '', 
    c.servico, 
    formatData(c.vencimento), 
    c.situacao
  ])
  exportToPDF('Relatório de Contratos', columns, rows)
}

watch(() => route.query, (newQuery) => {
  if (newQuery.situacao) filtroSituacao.value = newQuery.situacao
  else filtroSituacao.value = 'Todas'
  
  if (newQuery.prazo) filtroPrazo.value = newQuery.prazo
  else filtroPrazo.value = 'Todos'
  
  if (newQuery.fornecedor_id) filtroFornecedor.value = Number(newQuery.fornecedor_id)
  else filtroFornecedor.value = null
}, { immediate: true })

onMounted(() => {
  if(store.setorAtivo) carregarDados()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Lista de Contratos</h2>
      <div>
        <v-btn color="primary" prepend-icon="mdi-plus" class="mr-3" @click="openNew">Novo Contrato</v-btn>
        <v-btn color="secondary" prepend-icon="mdi-printer" variant="tonal" @click="printPDF">Exportar PDF</v-btn>
      </div>
    </div>

    <v-card rounded="xl" elevation="4">
      <v-card-title class="pa-4 bg-grey-darken-4">
        <v-row class="ma-0 w-100 d-flex align-center">
          <v-col cols="12" sm="3" class="pa-1">
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Buscar contratos..."
              single-line
              hide-details
              variant="solo-filled"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="3" class="pa-1">
            <v-select
              v-model="filtroSituacao"
              :items="['Todas', 'Em vigência', 'Renovado', 'Emergencial', 'Em renovação', 'Encerrado']"
              label="Filtrar por Situação"
              variant="solo-filled"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" sm="3" class="pa-1">
            <v-select
              v-model="filtroPrazo"
              :items="['Todos', 'Vencidos', 'Vence em 30 dias', 'Vence em 60 dias', 'Vence em 90 dias']"
              label="Filtrar por Prazo"
              variant="solo-filled"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" sm="3" class="pa-1">
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
        </v-row>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="filteredContratos"
        :search="search"
        :loading="loading"
        class="bg-grey-darken-3"
      >
        <template v-slot:item.vencimento="{ item }">
          {{ formatData(item.vencimento) }}
        </template>
        
        <template v-slot:item.prazo_restante="{ item }">
          <v-chip
            :color="item.color"
            class="font-weight-bold"
            variant="flat"
          >
            {{ item.prazo_restante }}{{ item.prazo_restante !== 'N/A' ? ' dias' : '' }}
          </v-chip>
        </template>
        
        <template v-slot:item.situacao="{ item }">
          <v-chip variant="outlined" size="small">{{ item.situacao }}</v-chip>
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

    <!-- Modal Novo Contrato -->
    <v-dialog v-model="dialog" max-width="900px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6">
          <span class="text-h5">{{ isEditing ? 'Editar Contrato' : 'Cadastrar Contrato' }}</span>
        </v-card-title>
        <v-card-text class="px-6">
          <v-row>
            <v-col cols="12" sm="3">
              <v-text-field v-model="formData.numero" label="Nº Contrato" variant="outlined" placeholder="0000/0000"></v-text-field>
            </v-col>
            <v-col cols="12" sm="9">
              <v-text-field v-model="formData.servico" label="Serviço" variant="outlined" maxlength="90"></v-text-field>
            </v-col>
            
            <v-col cols="12" sm="12">
              <v-autocomplete
                v-model="formData.fornecedor_id"
                :items="fornecedoresList"
                item-title="nome_fantasia"
                item-value="id"
                label="Fornecedor"
                variant="outlined"
              ></v-autocomplete>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.fiscal" label="Fiscal do Contrato" variant="outlined" maxlength="90"></v-text-field>
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field v-model="formData.vencimento" label="Vencimento" type="date" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field v-model.lazy="formData.valor_total" v-money3="moneyConfig" label="Valor Total (R$)" variant="outlined" placeholder="0,00"></v-text-field>
            </v-col>
            
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.numero_empenho" label="Nº Empenho" variant="outlined" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.numero_ordem_compra" label="Nº Ordem Compra" variant="outlined" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field v-model="formData.numero_processo_digital" label="Nº Proc. Digital" variant="outlined" maxlength="12"></v-text-field>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.numero_licitacao" label="Nº Licitação" variant="outlined" maxlength="12"></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="formData.situacao"
                :items="situacoesList"
                label="Situação"
                variant="outlined"
              ></v-select>
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
          <span class="text-h5">Detalhes do Contrato</span>
          <v-btn icon="mdi-close" variant="text" @click="viewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text class="px-6 pb-6">
          <v-row>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Nº Contrato</div>
              <div class="text-body-1 font-weight-medium">{{ viewData.numero }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Situação</div>
              <v-chip size="small" :color="viewData.situacao === 'Em vigência' ? 'success' : viewData.situacao === 'Encerrado' ? 'error' : viewData.situacao === 'Emergencial' ? 'warning' : 'info'">
                {{ viewData.situacao }}
              </v-chip>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Fornecedor</div>
              <div class="text-body-1">{{ viewData.fornecedor?.nome_fantasia || viewData.fornecedor?.razao_social || 'Não informado' }}</div>
            </v-col>
            <v-col cols="12" sm="12">
              <div class="text-caption text-medium-emphasis mb-1">Objeto/Serviço</div>
              <div class="text-body-1">{{ viewData.servico || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Fiscal</div>
              <div class="text-body-1">{{ viewData.fiscal || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Valor Total</div>
              <div class="text-body-1 font-weight-bold text-success">{{ formatCurrency(viewData.valor_total) }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Vencimento</div>
              <div class="text-body-1">{{ formatData(viewData.vencimento) }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Setor</div>
              <div class="text-body-1">{{ viewData.setor?.nome || 'Geral' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Prazo Restante</div>
              <div class="text-body-1" :class="viewData.prazo_restante < 0 ? 'text-error' : 'text-success'">
                {{ viewData.prazo_restante }} dias
              </div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Processo Digital / Licitação</div>
              <div class="text-body-1">{{ viewData.numero_processo_digital || '-' }} / {{ viewData.numero_licitacao || '-' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-medium-emphasis mb-1">Empenho / OC</div>
              <div class="text-body-1">{{ viewData.numero_empenho || '-' }} / {{ viewData.numero_ordem_compra || '-' }}</div>
            </v-col>
            <v-col cols="12">
              <v-divider class="my-2"></v-divider>
              <div class="text-caption text-medium-emphasis mb-1">Observações</div>
              <div class="text-body-2 text-pre-wrap">{{ viewData.observacao || 'Nenhuma observação cadastrada.' }}</div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pb-6 px-6">
          <v-spacer></v-spacer>
          <v-btn
            v-if="viewData.fornecedor_id"
            color="info"
            variant="tonal"
            prepend-icon="mdi-account-group"
            @click="router.push(`/admin/contatos?fornecedor_id=${viewData.fornecedor_id}`)"
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
