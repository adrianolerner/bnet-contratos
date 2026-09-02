<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js'
import { Bar, Pie } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement)

const contratos = ref([])
const totalContratos = ref(0)
const emVigencia = ref(0)
const router = useRouter()
const vencimentoProximo = ref(0)
const vencidos = ref(0)

const situacaoData = ref({
  labels: ['Em vigência', 'Emergencial', 'Em renovação', 'Renovado', 'Encerrado'],
  datasets: [{ label: 'Qtd. Contratos', backgroundColor: '#1867C0', data: [0, 0, 0, 0, 0] }]
})

const prazoData = ref({
  labels: ['> 90 dias', '60-89 dias', '30-59 dias', '< 30 dias'],
  datasets: [{ backgroundColor: ['#4caf50', '#1867c0', '#FDD835', '#E53935'], data: [0, 0, 0, 0] }]
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#FFFFFF' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
    y: { ticks: { color: '#FFFFFF' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
  }
}

const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#FFFFFF' } }
  }
}

async function carregarDados() {
  if (!store.setorAtivo) return
  try {
    const res = await api.get(`/contratos?setor_id=${store.setorAtivo}`)
    contratos.value = res.data
    calcularDashboard()
  } catch (error) {
    console.error('Erro ao carregar contratos', error)
  }
}

watch(() => store.setorAtivo, (newVal) => {
  if (newVal) carregarDados()
})

function calcularDashboard() {
  const hoje = new Date()
  
  totalContratos.value = contratos.value.length
  
  let vigencia = 0
  let vProximo = 0
  let vVencidos = 0

  const mapSituacao = { 'Em vigência': 0, 'Emergencial': 1, 'Em renovação': 2, 'Renovado': 3, 'Encerrado': 4 }
  const countSituacao = [0, 0, 0, 0, 0]
  
  const countPrazo = [0, 0, 0, 0]

  contratos.value.forEach(c => {
    // Contagem de situações
    if (mapSituacao[c.situacao] !== undefined) {
      countSituacao[mapSituacao[c.situacao]]++
    }

    if (c.situacao === 'Em vigência') vigencia++

    // Prazos
    const dataVenc = new Date(c.vencimento)
    const diffTime = dataVenc - hoje
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (c.situacao !== 'Encerrado') {
      if (diffDays < 0) {
        vVencidos++
      }
      
      if (diffDays >= 0 && diffDays <= 30) {
        vProximo++
      }

      if (diffDays >= 90) countPrazo[0]++
      else if (diffDays >= 60 && diffDays < 90) countPrazo[1]++
      else if (diffDays >= 30 && diffDays < 60) countPrazo[2]++
      else countPrazo[3]++
    }
  })

  emVigencia.value = vigencia
  vencimentoProximo.value = vProximo
  vencidos.value = vVencidos

  situacaoData.value = {
    labels: ['Em vigência', 'Emergencial', 'Em renovação', 'Renovado', 'Encerrado'],
    datasets: [{ label: 'Qtd. Contratos', backgroundColor: '#1867C0', data: countSituacao }]
  }

  prazoData.value = {
    labels: ['> 90 dias', '60-89 dias', '30-59 dias', '< 30 dias'],
    datasets: [{ backgroundColor: ['#4caf50', '#1867C0', '#FDD835', '#E53935'], data: countPrazo }]
  }
}

onMounted(() => {
  if (store.setorAtivo) carregarDados()
})
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-h4 font-weight-bold">Dashboard Visão Geral</h2>
      <p class="text-medium-emphasis">Resumo consolidado do sistema</p>
    </div>

    <!-- Cards de Resumo -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card color="primary" rounded="xl" elevation="4" class="cursor-pointer" @click="router.push('/admin/contratos')">
          <v-card-text class="d-flex justify-space-between align-center">
            <div>
              <div class="text-subtitle-1">Total de Contratos</div>
              <div class="text-h3 font-weight-bold mt-2">{{ totalContratos }}</div>
            </div>
            <v-icon size="60" opacity="0.3">mdi-file-document-multiple</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card color="success" rounded="xl" elevation="4" class="cursor-pointer" @click="router.push('/admin/contratos?situacao=Em vigência')">
          <v-card-text class="d-flex justify-space-between align-center">
            <div>
              <div class="text-subtitle-1">Em Vigência</div>
              <div class="text-h3 font-weight-bold mt-2">{{ emVigencia }}</div>
            </div>
            <v-icon size="60" opacity="0.3">mdi-check-decagram</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card color="warning" rounded="xl" elevation="4" class="cursor-pointer" @click="router.push('/admin/contratos?prazo=Vence em 30 dias')">
          <v-card-text class="d-flex justify-space-between align-center">
            <div>
              <div class="text-subtitle-1">Vencimento < 30d</div>
              <div class="text-h3 font-weight-bold mt-2">{{ vencimentoProximo }}</div>
            </div>
            <v-icon size="60" opacity="0.3">mdi-alert</v-icon>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="error" rounded="xl" elevation="4" class="cursor-pointer" @click="router.push('/admin/contratos?prazo=Vencidos')">
          <v-card-text class="d-flex justify-space-between align-center">
            <div>
              <div class="text-subtitle-1">Contratos Vencidos</div>
              <div class="text-h3 font-weight-bold mt-2">{{ vencidos }}</div>
            </div>
            <v-icon size="60" opacity="0.3">mdi-close-octagon</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Gráficos -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card rounded="xl" elevation="4" class="bg-grey-darken-3 h-100">
          <v-card-title class="pa-4 font-weight-bold">Contratos por Situação</v-card-title>
          <v-card-text style="height: 300px;">
            <Bar
              :data="situacaoData"
              :options="barOptions"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card rounded="xl" elevation="4" class="bg-grey-darken-3 h-100">
          <v-card-title class="pa-4 font-weight-bold">Distribuição por Prazo de Vencimento</v-card-title>
          <v-card-text style="height: 300px;" class="pb-6">
            <Pie
              :data="prazoData"
              :options="pieOptions"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
