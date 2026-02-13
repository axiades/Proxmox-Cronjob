<template>
  <div class="schedules-view">
    <div class="header">
      <h1>Schedules</h1>
      <button @click="showCreateModal = true" class="btn btn-success">➕ Create Schedule</button>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Target</th>
            <th>Action</th>
            <th>Schedule</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Next Run</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="schedule in schedules" :key="schedule.id">
            <td>{{ schedule.name }}</td>
            <td>{{ schedule.target_type }} #{{ schedule.target_id }}</td>
            <td>{{ schedule.action }}</td>
            <td><code>{{ schedule.cron_expression }}</code></td>
            <td>
              <span :class="`status-badge ${schedule.enabled ? 'status-success' : 'status-stopped'}`">
                {{ schedule.enabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td>{{ formatDate(schedule.last_run) }}</td>
            <td>{{ formatDate(schedule.next_run) }}</td>
            <td>
              <button @click="toggleSchedule(schedule.id)" class="btn btn-sm btn-secondary">
                {{ schedule.enabled ? 'Disable' : 'Enable' }}
              </button>
              <button @click="deleteSchedule(schedule.id)" class="btn btn-sm btn-danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Create Modal (simplified) -->
    <div v-if="showCreateModal" class="modal" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h2>Create Schedule</h2>
        <form @submit.prevent="createSchedule">
          <div class="form-group">
            <label>Name</label>
            <input v-model="newSchedule.name" required />
          </div>
          <div class="form-group">
            <label>Target Type</label>
            <select v-model="newSchedule.target_type" required>
              <option value="vm">VM</option>
              <option value="group">Group</option>
            </select>
          </div>
          <div class="form-group">
            <label>Target ID</label>
            <input v-model.number="newSchedule.target_id" type="number" required />
          </div>
          <div class="form-group">
            <label>Action</label>
            <select v-model="newSchedule.action" required>
              <option value="start">Start</option>
              <option value="stop">Stop</option>
              <option value="restart">Restart</option>
              <option value="shutdown">Shutdown</option>
            </select>
          </div>
          <div class="form-group">
            <label>Cron Expression</label>
            <input v-model="newSchedule.cron_expression" placeholder="*/5 * * * *" required />
            <small>Example: */30 * * * * (every 30 minutes)</small>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

export default {
  name: 'SchedulesView',
  setup() {
    const schedules = ref([])
    const loading = ref(true)
    const error = ref('')
    const showCreateModal = ref(false)
    const newSchedule = ref({
      name: '',
      target_type: 'vm',
      target_id: null,
      action: 'restart',
      cron_expression: '0 2 * * *',
      enabled: true,
    })
    
    const loadSchedules = async () => {
      try {
        loading.value = true
        const response = await api.get('/schedules')
        schedules.value = response.data
      } catch (err) {
        error.value = err.message
      } finally {
        loading.value = false
      }
    }
    
    const createSchedule = async () => {
      try {
        await api.post('/schedules', newSchedule.value)
        showCreateModal.value = false
        await loadSchedules()
        alert('Schedule created successfully')
      } catch (err) {
        alert('Failed to create schedule: ' + err.message)
      }
    }
    
    const toggleSchedule = async (id) => {
      try {
        await api.post(`/schedules/${id}/toggle`)
        await loadSchedules()
      } catch (err) {
        alert('Failed to toggle schedule: ' + err.message)
      }
    }
    
    const deleteSchedule = async (id) => {
      if (!confirm('Are you sure you want to delete this schedule?')) return
      
      try {
        await api.delete(`/schedules/${id}`)
        await loadSchedules()
        alert('Schedule deleted successfully')
      } catch (err) {
        alert('Failed to delete schedule: ' + err.message)
      }
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString()
    }
    
    onMounted(() => {
      loadSchedules()
    })
    
    return {
      schedules,
      loading,
      error,
      showCreateModal,
      newSchedule,
      loadSchedules,
      createSchedule,
      toggleSchedule,
      deleteSchedule,
      formatDate,
    }
  },
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

code {
  background-color: #f4f4f4;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
}

.modal-content h2 {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
  margin: 0 2px;
}
</style>
