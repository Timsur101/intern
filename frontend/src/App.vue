<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-title>Proxy Service</v-app-bar-title>

      <template v-if="isLoggedIn">
        <v-btn to="/profile" variant="text">Профиль</v-btn>
        <v-btn variant="text" @click="logout">Выйти</v-btn>
      </template>
      <template v-else>
        <v-btn to="/login" variant="text">Войти</v-btn>
        <v-btn to="/register" variant="text">Регистрация</v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>
