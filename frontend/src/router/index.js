import { createRouter, createWebHistory } from 'vue-router'
import { store } from '@/store'
import api from '@/api'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      redirect: '/admin'
    },
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      // Adicionar meta: { requiresAuth: true } na vida real
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/HomeDashboardView.vue'),
        },
        {
          path: 'perfil',
          name: 'perfil',
          component: () => import('../views/PerfilView.vue'),
        },
        {
          path: 'contratos',
          name: 'contratos',
          component: () => import('../views/ContratosView.vue'),
        },
        {
          path: 'fornecedores',
          name: 'fornecedores',
          component: () => import('../views/FornecedoresView.vue'),
        },
        {
          path: 'contatos',
          name: 'contatos',
          component: () => import('../views/ContatosView.vue'),
        },
        {
          path: 'pagamentos',
          name: 'pagamentos',
          component: () => import('../views/PagamentosView.vue'),
        },
        {
          path: 'processos',
          name: 'processos',
          component: () => import('../views/ProcessosView.vue'),
        },
        {
          path: 'configuracoes',
          name: 'configuracoes',
          component: () => import('../views/ConfiguracoesView.vue'),
        },
        {
          path: 'sobre',
          name: 'sobre',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'setores',
          name: 'setores',
          component: () => import('../views/SetoresView.vue'),
        },
        {
          path: 'usuarios',
          name: 'admin-usuarios',
          component: () => import('@/views/UsuariosView.vue'),
          meta: { adminOnly: true }
        },
        {
          path: 'backups',
          name: 'admin-backups',
          component: () => import('@/views/BackupView.vue'),
          meta: { adminOnly: true }
        },
        {
          path: 'logs',
          name: 'admin-logs',
          component: () => import('@/views/LogsView.vue'),
          meta: { adminOnly: true }
        },
      ]
    },
  ],
})

// Simples guardião de rotas
router.beforeEach(async (to, from, next) => {
  const publicPages = ['/login']
  const authRequired = !publicPages.includes(to.path)
  const loggedIn = localStorage.getItem('token')

  if (authRequired && !loggedIn) {
    return next('/login')
  }

  // Verifica rotas restritas a admin
  if (to.meta.adminOnly) {
    if (!store.usuarioAuth) {
      try {
        const res = await api.get('/auth/me')
        store.usuarioAuth = res.data
      } catch (err) {
        return next('/login')
      }
    }
    
    if (store.usuarioAuth.privilegio !== 'admin') {
      // Se não for admin, volta de onde veio ou vai pra home
      return next(from.path !== '/' && from.path !== to.path ? from.path : '/admin')
    }
  }

  next()
})

export default router
