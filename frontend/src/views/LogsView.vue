<template>
  <div class="logs-view">
    <h1>Execution Logs</h1>
    
    <div class="card filters">
      <label>
        Status:
        <select v-model="filterStatus">
          <option value="">All</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </select>
      </label>
      <label>
        VM ID:
        <input v-model.number="filterVmid" type="number" placeholder="Filter by VMID" />
      </label>
      <button @click="loadLogs" class="btn btn-primary">Apply Filters</button>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else class="card">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>VM</th>
            <th>Action</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Error/Reason</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ formatDate(log.executed_at) }}</td>
            <td>
              <div>{{ log.vm_name }}</div>
              <small>VMID: {{ log.vmid }}</small>
            </td>
            <td>{{ log.action }}</td>
            <td>
              <span :class="`status-badge status-${log.status}`">
                {{ log.status }}
              </span>
            </td>
            <td>{{ log.duration_seconds ? log.duration_seconds + 's' : '-' }}</td>
            <td>
              <small>{{ log.error_message || log.skipped_reason || '-' }}</small>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div class="pagination">
        <button @click="loadMore" class="btn btn-secondary" :disabled="loading">
          Load More
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

export default {
  name: 'LogsView',
  setup() {
    const logs = ref([])
    const loading = ref(true)
    const filterStatus = ref('')
    const filterVmid = ref(null)
    const limit = ref(50)
    const offset = ref(0)
    
    const loadLogs = async (append = false) => {
      try {
        loading.value = true
        const params = {
          limit: limit.value,
          offset: append ? offset.value : 0,
        }
        if (filterStatus.value) params.status = filterStatus.value
        if (filterVmid.value) params.vmid = filterVmid.value
        
        const response = await api.get('/logs', { params })
        
        if (append) {
          logs.value = [...logs.value, ...response.data]
        } else {
          logs.value = response.data
          offset.value = 0
        }
      } finally {
        loading.value = false
      }
    }
    
    const loadMore = () => {
      offset.value += limit.value
      loadLogs(true)
    }
    
    const formatDate = (dateStr) => {
      return new Date(dateStr).toLocaleString()
    }
    
    onMounted(() => loadLogs())
    
    return { logs, loading, filterStatus, filterVmid, loadLogs, loadMore, formatDate }
  },
}
</script>

<style scoped>
.filters {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
}

.filters label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filters select,
.filters input {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.pagination {
  text-align: center;
  margin-top: 20px;
}
</style>
