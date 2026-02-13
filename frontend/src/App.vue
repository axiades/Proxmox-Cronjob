<template>
  <div id="app">
    <Navbar v-if="isAuthenticated" />
    <main :class="{ 'with-navbar': isAuthenticated }">
      <router-view />
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'

export default {
  name: 'App',
  components: {
    Navbar,
  },
  setup() {
    const route = useRoute()
    const isAuthenticated = computed(() => route.path !== '/login')
    
    return {
      isAuthenticated,
    }
  },
}
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

main.with-navbar {
  margin-top: 60px;
}

/* Common styles */
.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #218838;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
}

table th,
table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

table th {
  font-weight: 600;
  background-color: #f8f9fa;
}

table tr:hover {
  background-color: #f8f9fa;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-running {
  background-color: #d4edda;
  color: #155724;
}

.status-stopped {
  background-color: #f8d7da;
  color: #721c24;
}

.status-paused {
  background-color: #fff3cd;
  color: #856404;
}

.status-success {
  background-color: #d4edda;
  color: #155724;
}

.status-failed {
  background-color: #f8d7da;
  color: #721c24;
}

.status-skipped {
  background-color: #fff3cd;
  color: #856404;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}

.success-message {
  background-color: #d4edda;
  color: #155724;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}
</style>
