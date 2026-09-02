<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'

const router = useRouter()
const drawer = ref(true)

const notificacoes = ref([])
const menuNotificacoes = ref(false)

const allMenuItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/admin' },
  { title: 'Contratos', icon: 'mdi-file-document-outline', to: '/admin/contratos' },
  { title: 'Fornecedores', icon: 'mdi-domain', to: '/admin/fornecedores' },
  { title: 'Contatos', icon: 'mdi-account-group', to: '/admin/contatos' },
  { title: 'Pagamentos', icon: 'mdi-cash-multiple', to: '/admin/pagamentos' },
  { title: 'Processos', icon: 'mdi-folder-open', to: '/admin/processos' },
  { title: 'Configurações', icon: 'mdi-cog', to: '/admin/configuracoes', adminOnly: true },
  { title: 'Setores', icon: 'mdi-office-building', to: '/admin/setores', adminOnly: true },
  { title: 'Usuários', icon: 'mdi-shield-account', to: '/admin/usuarios', adminOnly: true },
  { title: 'Logs de Auditoria', icon: 'mdi-history', to: '/admin/logs', adminOnly: true },
  { title: 'Backups', icon: 'mdi-database', to: '/admin/backups', adminOnly: true },
  { title: 'Sobre o Sistema', icon: 'mdi-information-outline', to: '/admin/sobre' },
]

const menu = computed(() => {
  if (store.usuarioAuth?.privilegio === 'admin') {
    return allMenuItems
  }
  return allMenuItems.filter(item => !item.adminOnly)
})

async function carregarDadosGlobais() {
  try {
    const [resSetores, resMe, resConfig, resFavs] = await Promise.all([
      api.get('/setores'),
      api.get('/auth/me'),
      api.get('/configuracoes'),
      api.get('/favoritos')
    ])
    
    store.setoresPermitidos = resSetores.data
    store.usuarioAuth = resMe.data
    store.appConfig = resConfig.data
    store.favoritos = resFavs.data
    
    if (resSetores.data.length > 0 && !store.setorAtivo) {
      store.setorAtivo = resSetores.data[0].id
    }
    
    carregarNotificacoes()
  } catch (error) {
    console.error('Erro ao carregar dados globais no menu', error)
  }
}

async function carregarNotificacoes() {
  try {
    const res = await api.get('/notificacoes')
    notificacoes.value = res.data
  } catch (err) {
    console.error('Erro ao carregar notificações', err)
  }
}

async function marcarLida(id) {
  try {
    await api.put(`/notificacoes/${id}/lida`)
    notificacoes.value = notificacoes.value.filter(n => n.id !== id)
  } catch (err) {
    console.error('Erro ao marcar notificação como lida', err)
  }
}

onMounted(() => {
  carregarDadosGlobais()
})

watch(() => store.appConfig, (newConfig) => {
  if (newConfig?.nome_orgao) {
    document.title = `BNET Contratos - ${newConfig.nome_orgao}`
  } else {
    document.title = 'BNET Contratos'
  }
}, { deep: true, immediate: true })

const formForcePassword = ref({
  password: '',
  confirmPassword: ''
})
const loadingForcePassword = ref(false)
const errorForcePassword = ref('')

const showForcePasswordModal = computed(() => {
  return store.usuarioAuth?.deve_trocar_senha === true
})

async function saveForcedPassword() {
  errorForcePassword.value = ''
  if (!formForcePassword.value.password || formForcePassword.value.password.length < 6) {
    errorForcePassword.value = 'A senha deve ter pelo menos 6 caracteres.'
    return
  }
  if (formForcePassword.value.password !== formForcePassword.value.confirmPassword) {
    errorForcePassword.value = 'As senhas não conferem.'
    return
  }

  loadingForcePassword.value = true
  try {
    const res = await api.put('/auth/me', {
      password: formForcePassword.value.password
    })
    store.usuarioAuth = res.data
    formForcePassword.value.password = ''
    formForcePassword.value.confirmPassword = ''
  } catch (err) {
    errorForcePassword.value = 'Erro ao alterar a senha. Tente novamente.'
    console.error(err)
  } finally {
    loadingForcePassword.value = false
  }
}

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <v-layout>
    <v-navigation-drawer v-model="drawer" color="grey-darken-4">
      <v-list-item
        title="BNET Contratos"
        :subtitle="store.appConfig?.nome_orgao || 'Prefeitura Municipal'"
        class="py-4 text-center"
      >
        <template v-slot:prepend>
          <v-avatar v-if="store.appConfig?.logo_url" rounded="0" size="40">
            <v-img :src="store.appConfig.logo_url" alt="Logo"></v-img>
          </v-avatar>
          <v-icon v-else size="40" color="primary">mdi-city</v-icon>
        </template>
      </v-list-item>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          v-for="item in menu"
          :key="item.title"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          active-color="primary"
          exact
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar color="grey-darken-4" elevation="1">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-toolbar-title>Gestão de Contratos</v-toolbar-title>

      <v-spacer></v-spacer>

      <div style="width: 250px; margin-right: 20px;">
        <v-select
          v-model="store.setorAtivo"
          :items="store.setoresPermitidos"
          item-title="nome"
          item-value="id"
          label="Setor Ativo"
          variant="solo-filled"
          density="compact"
          hide-details
          prepend-inner-icon="mdi-domain"
        ></v-select>
      </div>

      <v-menu v-model="menuNotificacoes" :close-on-content-click="false" location="bottom end">
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-badge :content="notificacoes.length" :model-value="notificacoes.length > 0" color="error" overlap>
              <v-icon>mdi-bell</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <v-card min-width="300" max-width="400" bg-color="grey-darken-3">
          <v-list bg-color="transparent" lines="two">
            <v-list-subheader class="text-subtitle-1 font-weight-bold">Notificações</v-list-subheader>
            <template v-if="notificacoes.length > 0">
              <v-list-item v-for="n in notificacoes" :key="n.id" class="mb-1">
                <v-list-item-title class="text-caption text-wrap">{{ n.mensagem }}</v-list-item-title>
                <v-list-item-subtitle class="text-caption text-medium-emphasis mt-1">
                  {{ new Date(n.data_criacao).toLocaleDateString('pt-BR') }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon="mdi-check" variant="text" size="small" color="primary" @click="marcarLida(n.id)" title="Marcar como lida"></v-btn>
                </template>
              </v-list-item>
            </template>
            <v-list-item v-else>
              <v-list-item-title class="text-caption text-center text-medium-emphasis py-4">Nenhuma notificação nova.</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-menu>

      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list bg-color="grey-darken-3">
          <v-list-item to="/admin/perfil" prepend-icon="mdi-account">Meu Perfil</v-list-item>
          <v-list-item @click="logout" prepend-icon="mdi-logout" color="error">Sair</v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main style="background-color: #121212; min-height: 100vh; padding-bottom: 50px;">
      <v-container fluid class="pa-6">
        <router-view></router-view>
      </v-container>
    </v-main>

    <v-footer app color="grey-darken-4" border class="text-center d-flex justify-center text-caption text-medium-emphasis py-2">
      <div>Desenvolvido por SMCTI - Castro - Adriano Lerner Biesek</div>
    </v-footer>

    <!-- Modal Obrigatório de Troca de Senha -->
    <v-dialog v-model="showForcePasswordModal" persistent max-width="500px">
      <v-card class="bg-grey-darken-4 rounded-xl">
        <v-card-title class="pt-6 px-6 text-h5 text-center text-error">
          <v-icon size="large" class="mr-2 mb-1">mdi-alert-circle</v-icon>
          Troca de Senha Obrigatória
        </v-card-title>
        <v-card-text class="px-6 text-center">
          <p class="mb-4 text-body-1 text-medium-emphasis">
            Por motivos de segurança, você precisa alterar sua senha genérica antes de continuar a utilizar o sistema.
          </p>
          <v-alert v-if="errorForcePassword" type="error" variant="tonal" class="mb-4 text-left">
            {{ errorForcePassword }}
          </v-alert>
          <v-text-field
            v-model="formForcePassword.password"
            label="Nova Senha"
            type="password"
            variant="outlined"
            class="mb-2"
          ></v-text-field>
          <v-text-field
            v-model="formForcePassword.confirmPassword"
            label="Confirmar Nova Senha"
            type="password"
            variant="outlined"
            @keyup.enter="saveForcedPassword"
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pb-6 px-6 justify-center">
          <v-btn color="error" variant="text" @click="logout" class="mr-4">Sair do Sistema</v-btn>
          <v-btn color="primary" variant="flat" :loading="loadingForcePassword" @click="saveForcedPassword">
            Confirmar e Acessar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-layout>
</template>
