<template>
  <v-container style="max-width: 600px; margin-top: 40px">

    <v-card class="mb-5" elevation="3">
      <v-card-title>Профиль</v-card-title>
      <v-card-text>
        <p><b>Email:</b> {{ user.email }}</p>
        <p>
          <b>Статус:</b>
          <span :style="{ color: user.is_active ? 'green' : 'orange' }">
            {{ user.is_active ? 'Активен' : 'Не активен' }}
          </span>
        </p>

        <div class="mt-4">
          <b>Ключ активации:</b>
          <div v-if="user.activation_key" class="mt-1 pa-2" style="background:#f5f5f5; border-radius:4px; font-family:monospace">
            {{ user.activation_key }}
          </div>
          <div v-else class="mt-1" style="color: gray">Ключ не найден</div>
        </div>

        <v-btn class="mt-4" color="primary" :loading="refreshLoading" @click="refreshKey">
          Обновить ключ
        </v-btn>

        <div v-if="refreshMsg" class="mt-3" :style="{ color: refreshOk ? 'green' : 'red' }">
          {{ refreshMsg }}
        </div>
      </v-card-text>
    </v-card>

    <v-card elevation="3">
      <v-card-title>Сменить пароль</v-card-title>
      <v-card-text>
        <div v-if="pwdMsg" class="mb-3" :style="{ color: pwdOk ? 'green' : 'red' }">
          {{ pwdMsg }}
        </div>

        <v-text-field
          v-model="oldPwd"
          label="Текущий пароль"
          type="password"
          variant="outlined"
          class="mb-2"
        />
        <v-text-field
          v-model="newPwd"
          label="Новый пароль"
          type="password"
          variant="outlined"
          class="mb-3"
        />
        <v-btn color="secondary" :loading="pwdLoading" @click="changePassword">
          Сохранить
        </v-btn>
      </v-card-text>
    </v-card>

  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const user = ref({ email: '', is_active: false, activation_key: null })

const refreshLoading = ref(false)
const refreshMsg = ref('')
const refreshOk = ref(false)

const oldPwd = ref('')
const newPwd = ref('')
const pwdLoading = ref(false)
const pwdMsg = ref('')
const pwdOk = ref(false)

async function loadProfile() {
  try {
    const res = await api.get('/users/me')
    user.value = res.data
  } catch (e) {
    console.log('error loading profile', e)
  }
}

async function refreshKey() {
  refreshMsg.value = ''
  refreshLoading.value = true
  try {
    const res = await api.post('/users/refresh-key')
    refreshMsg.value = res.data.message
    refreshOk.value = true
    await loadProfile()
  } catch (e) {
    refreshMsg.value = 'Ошибка, попробуй ещё раз'
    refreshOk.value = false
  }
  refreshLoading.value = false
}

async function changePassword() {
  pwdMsg.value = ''
  pwdLoading.value = true
  try {
    const res = await api.post('/users/change-password', {
      old_password: oldPwd.value,
      new_password: newPwd.value,
    })
    pwdMsg.value = res.data.message
    pwdOk.value = true
    oldPwd.value = ''
    newPwd.value = ''
  } catch (e) {
    pwdMsg.value = e.response?.data?.detail || 'Что-то пошло не так'
    pwdOk.value = false
  }
  pwdLoading.value = false
}

onMounted(loadProfile)
</script>
