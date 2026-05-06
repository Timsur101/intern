<template>
  <v-container style="max-width: 420px; margin-top: 80px">
    <v-card elevation="3">
      <v-card-title class="pa-5 pb-2">Регистрация</v-card-title>
      <v-card-text class="pa-5 pt-2">

        <div v-if="successMsg" style="color: green; margin-bottom: 12px">
          {{ successMsg }}
        </div>
        <div v-if="errorMsg" style="color: red; margin-bottom: 12px">
          {{ errorMsg }}
        </div>

        <v-text-field v-model="email" label="Email" type="email" variant="outlined" class="mb-3" />
        <v-text-field v-model="password" label="Пароль" type="password" variant="outlined" class="mb-3" />
        <v-text-field v-model="passwordConfirm" label="Подтвердите пароль" type="password" variant="outlined" class="mb-4" />

        <v-btn color="primary" block :loading="loading" @click="register">
          Зарегистрироваться
        </v-btn>

        <div class="mt-4 text-center">
          Уже есть аккаунт? <router-link to="/login">Войти</router-link>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

async function register() {
  errorMsg.value = ''
  successMsg.value = ''

  if (!email.value || !password.value) {
    errorMsg.value = 'Заполни все поля'
    return
  }

  loading.value = true
  try {
    const res = await api.post('/auth/register', {
      email: email.value,
      password: password.value,
      password_confirm: passwordConfirm.value,
    })
    successMsg.value = res.data.message
    email.value = ''
    password.value = ''
    passwordConfirm.value = ''
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Ошибка регистрации'
  }
  loading.value = false
}
</script>
