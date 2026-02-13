<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🖥️</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_vms }}</div>
          <div class="stat-label">Total VMs</div>
          <div class="stat-detail">
            {{ stats.running_vms }} running, {{ stats.stopped_vms }} stopped
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⏰</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.active_schedules }}</div>
          <div class="stat-label">Active Schedules</div>
          <div class="stat-detail">
            {{ stats.total_schedules }} total
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_groups }}</div>
          <div class="stat-label">VM Groups</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.recent_executions }}</div>
          <div class="stat-label">Recent Executions</div>
          <div class="stat-detail">
            {{ stats.failed_executions }} failed (24h)
          </div>
        </div>
      </div>
    </div>
    
    <div class="actions-section">
      <h2>Quick Actions</h2>
      <div class="quick-actions">
        <button @click="syncVMs" class="btn btn-primary" :disabled="syncing">
          {{ syncing ? 'Syncing...' : '🔄 Sync VMs' }}
        </button>
        <router-link to="/schedules" class="btn btn-success">
          ➕ Create Schedule
        </router-link>
        <router-link to="/groups" class="btn btn-success">
          ➕ Create Group
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

export default {
  name: 'Dashboard',
  setup() {
    const stats = ref({
      total_vms: 0,
      running_vms: 0,
      stopped_vms: 0,
      total_schedules: 0,
      active_schedules: 0,
      total_groups: 0,
      recent_executions: 0,
      failed_executions: 0,
    })
    const loading = ref(true)
    const error = ref('')
    const syncing = ref(false)
    
    const loadStats = async () => {
      try {
        loading.value = true
        const response = await api.get('/stats')
        stats.value = response.data
      } catch (err) {
        error.value = err.message
      } finally {
        loading.value = false
      }
    }
    
    const syncVMs = async () => {
      try {
        syncing.value = true
        await api.post('/vms/sync')
        await loadStats()
        alert('VMs synchronized successfully')
      } catch (err) {
        alert('Sync failed: ' + err.message)
      } finally {
        syncing.value = false
      }
    }
    
    onMounted(() => {
      loadStats()
    })
    
    return {
      stats,
      loading,
      error,
      syncing,
      syncVMs,
    }
  },
}
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 16px;
}

.stat-icon {
  font-size: 40px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.stat-detail {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.actions-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.actions-section h2 {
  margin-bottom: 16px;
  font-size: 20px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
