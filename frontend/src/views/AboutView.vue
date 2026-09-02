<script setup>
</script>

<template>
  <div class="h-100 d-flex flex-column">
    <div class="d-flex justify-space-between align-center mb-6">
      <h2 class="text-h4 font-weight-bold">Sobre o Sistema</h2>
    </div>

    <v-card class="bg-grey-darken-4 rounded-xl flex-grow-1" elevation="4">
      <v-card-text class="pa-8 text-center d-flex flex-column justify-center align-center h-100">
        <v-icon size="80" color="primary" class="mb-4">mdi-information-outline</v-icon>
        <h3 class="text-h4 font-weight-bold mb-2">BNET Contratos</h3>
        <p class="text-h6 text-medium-emphasis mb-6">Sistema de Gestão e Fiscalização de Contratos e Fornecedores</p>
        
        <v-chip color="info" size="large" class="mb-8 px-6 text-h6 font-weight-bold text-white">
          Versão 1.0
        </v-chip>

        <div class="text-body-1 text-left w-100" style="max-width: 600px;">
          <p class="mb-4 text-center">
            O <strong>BNET Contratos</strong> é uma solução moderna para órgãos públicos e empresas gerenciarem o ciclo de vida de seus contratos, fornecedores e processos de pagamento.
          </p>

          <v-divider class="mb-6"></v-divider>

          <p class="mb-2"><strong>Autor e Desenvolvedor:</strong> Adriano Lerner Biesek</p>
          <p class="mb-6"><strong>Licença:</strong> MIT License</p>

          <div class="text-caption text-medium-emphasis text-center">
            Este software é de código aberto sob a licença MIT, permitindo o uso, cópia, modificação e distribuição de forma livre, desde que mantida a atribuição original.
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>
