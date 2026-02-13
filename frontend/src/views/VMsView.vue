<template>
  <div class="vms-view">
    <div class="header">
      <h1>VMs & Containers</h1>
      <button @click="loadVMs" class="btn btn-primary">🔄 Refresh</button>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="card">
      <div class=" filters">
        <label>
          Type:
          <select v-model="filterType">
            <option value="">All</option>
            <option value="qemu">QEMU VMs</option>
            <option value="lxc">LXC Containers</option>
          </select>
        </label>
        <label>
          Node:
          <select v-model="filterNode">
            <option value="">All Nodes</option>
            <option v-for="node in nodes" :key="node" :value="node">{{ node }}</option>
          </select>
        </label>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>VMID</th>
            <th>Name</th>
            <th>Type</th>
            <th>Node</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="vm in filteredVMs" :key="vm.id">
            <td>{{ vm.vmid }}</td>
            <td>{{ vm.name }}</td>
            <td>{{ vm.type.toUpperCase() }}</td>
            <td>{{ vm.node }}</td>
            <td>
              <span :class="`status-badge status-${vm.status}`">
                {{ vm.status }}
              </span>
            </td>
            <td>
              <button @click="executeAction(vm.vmid, 'start')" class="btn btn-success btn-sm">Start</button>
              <button @click="executeAction(vm.vmid, 'stop')" class="btn btn-danger btn-sm">Stop</button>
              <button @click="executeAction(vm.vmid, 'restart')" class="btn btn-secondary btn-sm">Restart</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'

export default {
  name: 'VMsView',
  setup() {
    const vms = ref([])
    const loading = ref(true)
    const error = ref('')
    const filterType = ref('')
    const filterNode = ref('')
    
    const nodes = computed(() => {
      return [...new Set(vms.value.map(vm => vm.node))]
    })
    
    const filteredVMs = computed(() => {
      return vms.value.filter(vm => {
        if (filterType.value && vm.type !== filterType.value) return false
        if (filterNode.value && vm.node !== filterNode.value) return false
        return true
      })
    })
    
    const loadVMs = async () => {
      try {
        loading.value = true
        const response = await api.get('/vms')
        vms.value = response.data
      } catch (err) {
        error.value = err.message
      } finally {
        loading.value = false
      }
    }
    
    const executeAction = async (vmid, action) => {
      if (!confirm(`Are you sure you want to ${action} VM ${vmid}?`)) return
      
      try {
        await api.post(`/actions/vm/${vmid}`, { action })
        alert(`Action ${action} executed successfully`)
        await loadVMs()
      } catch (err) {
        alert('Action failed: ' + err.message)
      }
    }
    
    onMounted(() => {
      loadVMs()
    })
    
    return {
      vms,
      loading,
      error,
      filterType,
      filterNode,
      nodes,
      filteredVMs,
      loadVMs,
      executeAction,
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

.filters {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.filters label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filters select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
  margin: 0 2px;
}
</style>
