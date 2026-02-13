<template>
  <div class="blackouts-view">
    <div class="header">
      <h1>Blackout Windows</h1>
      <button @click="showCreateModal = true" class="btn btn-success">➕ Create Blackout</button>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else class="card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Time Range</th>
            <th>Days</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="blackout in blackouts" :key="blackout.id">
            <td>{{ blackout.name }}</td>
            <td>{{ blackout.start_time }} - {{ blackout.end_time }}</td>
            <td>{{ formatDays(blackout.days_of_week) }}</td>
            <td>
              <span :class="`status-badge ${blackout.enabled ? 'status-success' : 'status-stopped'}`">
                {{ blackout.enabled ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button @click="deleteBlackout(blackout.id)" class="btn btn-sm btn-danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h2>Create Blackout Window</h2>
        <form @submit.prevent="createBlackout">
          <div class="form-group">
            <label>Name</label>
            <input v-model="newBlackout.name" required />
          </div>
          <div class="form-group">
            <label>Start Time</label>
            <input v-model="newBlackout.start_time" type="time" required />
          </div>
          <div class="form-group">
            <label>End Time</label>
            <input v-model="newBlackout.end_time" type="time" required />
          </div>
          <div class="form-group">
            <label>Days (JSON array, e.g., [0,1,2,3,4] for Mon-Fri)</label>
            <input v-model="newBlackout.days_of_week" placeholder='[0,1,2,3,4,5,6]' />
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
  name: 'BlackoutsView',
  setup() {
    const blackouts = ref([])
    const loading = ref(true)
    const showCreateModal = ref(false)
    const newBlackout = ref({
      name: '',
      start_time: '22:00',
      end_time: '06:00',
      days_of_week: '[0,1,2,3,4,5,6]',
      enabled: true
    })
    
    const loadBlackouts = async () => {
      try {
        loading.value = true
        const response = await api.get('/blackouts')
        blackouts.value = response.data
      } finally {
        loading.value = false
      }
    }
    
    const createBlackout = async () => {
      try {
        await api.post('/blackouts', newBlackout.value)
        showCreateModal.value = false
        await loadBlackouts()
        alert('Blackout window created')
      } catch (err) {
        alert('Failed: ' + err.message)
      }
    }
    
    const deleteBlackout = async (id) => {
      if (!confirm('Delete this blackout window?')) return
      try {
        await api.delete(`/blackouts/${id}`)
        await loadBlackouts()
      } catch (err) {
        alert('Failed: ' + err.message)
      }
    }
    
    const formatDays = (daysStr) => {
      if (!daysStr) return 'All days'
      try {
        const days = JSON.parse(daysStr)
        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return days.map(d => dayNames[d]).join(', ')
      } catch {
        return daysStr
      }
    }
    
    onMounted(loadBlackouts)
    
    return { blackouts, loading, showCreateModal, newBlackout, createBlackout, deleteBlackout, formatDays }
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

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
  margin: 0 2px;
}
</style>
