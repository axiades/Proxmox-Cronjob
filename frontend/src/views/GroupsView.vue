<template>
  <div class="groups-view">
    <div class="header">
      <h1>VM Groups</h1>
      <button @click="showCreateModal = true" class="btn btn-success">➕ Create Group</button>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else class="card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Members</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="group in groups" :key="group.id">
            <td>{{ group.name }}</td>
            <td>{{ group.description || '-' }}</td>
            <td>{{ group.member_count }} VMs</td>
            <td>
              <button @click="viewGroup(group.id)" class="btn btn-sm btn-primary">View</button>
              <button @click="deleteGroup(group.id)" class="btn btn-sm btn-danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h2>Create Group</h2>
        <form @submit.prevent="createGroup">
          <div class="form-group">
            <label>Group Name</label>
            <input v-model="newGroup.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newGroup.description" rows="3"></textarea>
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
  name: 'GroupsView',
  setup() {
    const groups = ref([])
    const loading = ref(true)
    const showCreateModal = ref(false)
    const newGroup = ref({ name: '', description: '' })
    
    const loadGroups = async () => {
      try {
        loading.value = true
        const response = await api.get('/groups')
        groups.value = response.data
      } finally {
        loading.value = false
      }
    }
    
    const createGroup = async () => {
      try {
        await api.post('/groups', newGroup.value)
        showCreateModal.value = false
        newGroup.value = { name: '', description: '' }
        await loadGroups()
        alert('Group created successfully')
      } catch (err) {
        alert('Failed to create group: ' + err.message)
      }
    }
    
    const viewGroup = (id) => {
      alert(`View group ${id} - implement group details modal`)
    }
    
    const deleteGroup = async (id) => {
      if (!confirm('Delete this group?')) return
      try {
        await api.delete(`/groups/${id}`)
        await loadGroups()
      } catch (err) {
        alert('Failed: ' + err.message)
      }
    }
    
    onMounted(loadGroups)
    
    return { groups, loading, showCreateModal, newGroup, createGroup, viewGroup, deleteGroup }
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

.form-group input,
.form-group textarea {
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
