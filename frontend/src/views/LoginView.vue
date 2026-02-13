<template>
  <div class="login-page">
    <div class="login-card">
      <h2>Proxmox Cronjob Manager</h2>
      <p class="subtitle">Sign in to manage your schedules</p>
      
      <div v-if="error" class="error-message">{{ error }}</div>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Enter username"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter password"
            required
          />
        </div>
        
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const username = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)
    
    const handleLogin = async () => {
      error.value = ''
      loading.value = true
      
      try {
        const response = await api.post('/auth/login', {
          username: username.value,
          password: password.value,
        })
        
        const token = response.data.access_token
        localStorage.setItem('auth_token', token)
        
        router.push('/')
      } catch (err) {
        error.value = err.message || 'Login failed'
      } finally {
        loading.value = false
      }
    }
    
    return {
      username,
      password,
      error,
      loading,
      handleLogin,
    }
  },
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
}

.login-card h2 {
  margin-bottom: 10px;
  color: #2c3e50;
  text-align: center;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  margin-top: 10px;
}
</style>
