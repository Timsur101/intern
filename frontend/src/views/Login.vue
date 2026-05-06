<template>
  <v-container style="max-width: 420px; margin-top: 80px">
    <v-card elevation="3">
      <v-card-title class="pa-5 pb-2">Вход</v-card-title>
      <v-card-text class="pa-5 pt-2">

        <div v-if="errorMsg" style="color: red; margin-bottom: 12px">
          {{ errorMsg }}
        </div>

        <v-text-field v-model="email" label="Email" type="email" variant="outlined" class="mb-3" />
        <v-text-field v-model="password" label="Пароль" type="password" variant="outlined" class="mb-4" />

        <v-btn color="primary" block :loading="loading" @click="login">
          Войти
        </v-btn>

        <div class="mt-4 text-center">
          Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function login() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await api.post('/auth/login', {
      email: email.value,
      password: password.value,
    })
    localStorage.setItem('token', res.data.access_token)
    router.push('/profile')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Неверный email или пароль'
  }
  loading.value = false
}
</script>
