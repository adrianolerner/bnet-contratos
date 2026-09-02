import { reactive } from 'vue'

export const store = reactive({
  setorAtivo: null,
  setoresPermitidos: [],
  usuarioAuth: null,
  appConfig: {},
  favoritos: []
})
