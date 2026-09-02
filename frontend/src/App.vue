<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <v-app>
    <RouterView />
  </v-app>
</template>

<style>
/* Remove default vue CSS if any */
body {
  margin: 0;
  padding: 0;
}
</style>
