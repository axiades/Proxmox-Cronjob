<template>
  <div class="schedules-view">
    <div class="header">
      <h1>Schedules</h1>
      <button @click="openCreateModal" class="btn btn-success">➕ Create Schedule</button>
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
            <th>Schedule (Cron)</th>
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
            <td><span class="action-badge">{{ schedule.action }}</span></td>
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
    
    <!-- Create Modal (User-friendly Date/Time Picker) -->
    <div v-if="showCreateModal" class="modal" @click.self="showCreateModal = false">
      <div class="modal-content modal-large">
        <h2>📅 Create Schedule</h2>
        <form @submit.prevent="createSchedule">
          <!-- Basic Info -->
          <div class="form-section">
            <h3>Basic Information</h3>
            <div class="form-group">
              <label>Schedule Name</label>
              <input v-model="newSchedule.name" placeholder="e.g., Daily VM Restart" required />
            </div>
          </div>

          <!-- Target Selection -->
          <div class="form-section">
            <h3>Target</h3>
            <div class="form-row">
              <div class="form-group">
                <label>Type</label>
                <select v-model="newSchedule.target_type" @change="loadAvailableTargets" required>
                  <option value="vm">Virtual Machine</option>
                  <option value="lxc">LXC Container</option>
                  <option value="group">Group of VMs</option>
                </select>
              </div>
              <div class="form-group">
                <label>Select Target</label>
                <select v-model.number="newSchedule.target_id" required>
                  <option value="">-- Choose {{newSchedule.target_type}} --</option>
                  <option v-for="item in availableTargets" :key="item.id" :value="item.id">
                    {{ item.name }} (ID: {{ item.id }})
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Action Selection -->
          <div class="form-section">
            <h3>Action</h3>
            <div class="action-buttons">
              <button
                v-for="act in ['start', 'stop', 'restart', 'shutdown', 'reboot', 'reset']"
                :key="act"
                type="button"
                :class="`action-btn ${newSchedule.action === act ? 'active' : ''}`"
                @click="newSchedule.action = act"
              >
                {{ act.toUpperCase() }}
              </button>
            </div>
          </div>

          <!-- Schedule Options -->
          <div class="form-section">
            <h3>⏰ Schedule</h3>
            
            <div class="form-group">
              <label>How often should this run?</label>
              <select v-model="newSchedule.frequency" @change="onFrequencyChange" required>
                <option value="daily">🔄 Every day</option>
                <option value="weekly">📆 Every week</option>
                <option value="monthly">📅 Every month</option>
                <option value="once">⌛ Just once (specific date & time)</option>
                <option value="advanced">⚙ Advanced (Cron Expression)</option>
              </select>
            </div>

            <!-- Time Selection (for all modes) -->
            <div class="form-row">
              <div class="form-group">
                <label>What time?</label>
                <input v-model="newSchedule.time" type="time" required />
              </div>
            </div>

            <!-- Once Mode -->
            <div v-if="newSchedule.frequency === 'once'" class="form-row">
              <div class="form-group">
                <label>Date</label>
                <input v-model="newSchedule.date" type="date" required />
              </div>
            </div>

            <!-- Weekly Mode -->
            <div v-if="newSchedule.frequency === 'weekly'" class="form-group">
              <label>Which days?</label>
              <div class="weekday-selector">
                <label v-for="day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']" :key="day" class="checkbox">
                  <input 
                    type="checkbox" 
                    :value="day" 
                    :checked="newSchedule.weekdays.includes(day)"
                    @change="toggleWeekday(day)"
                  />
                  <span>{{ day }}</span>
                </label>
              </div>
            </div>

            <!-- Monthly Mode -->
            <div v-if="newSchedule.frequency === 'monthly'" class="form-row">
              <div class="form-group">
                <label>Day of month (1-31)</label>
                <input v-model.number="newSchedule.monthday" type="number" min="1" max="31" required />
              </div>
            </div>

            <!-- Advanced Mode -->
            <div v-if="newSchedule.frequency === 'advanced'" class="form-group">
              <label>Cron Expression</label>
              <input 
                v-model="newSchedule.cron_expression" 
                placeholder="0 2 * * * (2 AM every day)" 
                required 
              />
              <small>Format: minute hour day month weekday | Examples: <code>0 2 * * *</code> (2 AM daily), <code>0 0 * * 1</code> (Monday midnight)</small>
            </div>

            <!-- Preview -->
            <div class="schedule-preview">
              <strong>📌 Next Run:</strong>
              <p>{{ schedulePreview }}</p>
            </div>
          </div>

          <!-- Enabled Toggle -->
          <div class="form-section">
            <label class="checkbox-large">
              <input v-model="newSchedule.enabled" type="checkbox" />
              <span>✅ Enable this schedule immediately</span>
            </label>
          </div>

          <!-- Actions -->
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">✅ Create Schedule</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import api from '@/api/client'

export default {
  name: 'SchedulesView',
  setup() {
    const schedules = ref([])
    const loading = ref(true)
    const error = ref('')
    const showCreateModal = ref(false)
    const availableTargets = ref([])
    
    const newSchedule = ref({
      name: '',
      target_type: 'vm',
      target_id: null,
      action: 'restart',
      enabled: true,
      frequency: 'daily',
      date: new Date().toISOString().split('T')[0],
      time: '02:00',
      weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      monthday: 1,
      cron_expression: '0 2 * * 1-5',
    })

    // Computed property for schedule preview
    const schedulePreview = computed(() => {
      const { frequency, time, date, weekdays, monthday } = newSchedule.value
      
      switch (frequency) {
        case 'once':
          return `📍 ${new Date(date).toLocaleDateString()} at ${time}`
        case 'daily':
          return `🔄 Every day at ${time}`
        case 'weekly':
          return `📆 Every ${weekdays.join(', ')} at ${time}`
        case 'monthly':
          return `📅 Day ${monthday} of every month at ${time}`
        case 'advanced':
          return `⚙️ Custom: ${newSchedule.value.cron_expression}`
        default:
          return 'Invalid schedule'
      }
    })

    const generateCronExpression = () => {
      const { frequency, time, date, weekdays, monthday } = newSchedule.value
      const [hours, minutes] = time.split(':')
      
      switch (frequency) {
        case 'once':
          const d = new Date(date)
          return `${minutes} ${hours} ${d.getDate()} ${d.getMonth() + 1} *`
        
        case 'daily':
          return `${minutes} ${hours} * * *`
        
        case 'weekly':
          const dayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
          const dayNumbers = weekdays.map(d => dayMap[d]).sort()
          return `${minutes} ${hours} * * ${dayNumbers.join(',')}`
        
        case 'monthly':
          return `${minutes} ${hours} ${monthday} * *`
        
        case 'advanced':
          return newSchedule.value.cron_expression
        
        default:
          return '0 2 * * *'
      }
    }

    const onFrequencyChange = () => {
      newSchedule.value.cron_expression = generateCronExpression()
    }

    const toggleWeekday = (day) => {
      const index = newSchedule.value.weekdays.indexOf(day)
      if (index > -1) {
        newSchedule.value.weekdays.splice(index, 1)
      } else {
        newSchedule.value.weekdays.push(day)
      }
      newSchedule.value.cron_expression = generateCronExpression()
    }
    
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

    const loadAvailableTargets = async () => {
      try {
        if (newSchedule.value.target_type === 'group') {
          const response = await api.get('/groups')
          availableTargets.value = response.data.map(g => ({ id: g.id, name: g.name }))
        } else {
          const response = await api.get('/vms')
          availableTargets.value = response.data.map(vm => ({ id: vm.id, name: vm.name }))
        }
      } catch (err) {
        console.error('Failed to load targets:', err)
        availableTargets.value = []
      }
    }
    
    const createSchedule = async () => {
      try {
        if (!newSchedule.value.name || !newSchedule.value.target_id || !newSchedule.value.action) {
          alert('Please fill in all required fields')
          return
        }

        const scheduleData = {
          name: newSchedule.value.name,
          target_type: newSchedule.value.target_type,
          target_id: newSchedule.value.target_id,
          action: newSchedule.value.action,
          cron_expression: generateCronExpression(),
          enabled: newSchedule.value.enabled,
        }
        
        await api.post('/schedules', scheduleData)
        showCreateModal.value = false
        resetForm()
        await loadSchedules()
        alert('✅ Schedule created successfully!')
      } catch (err) {
        alert('Failed to create schedule: ' + err.message)
      }
    }

    const resetForm = () => {
      newSchedule.value = {
        name: '',
        target_type: 'vm',
        target_id: null,
        action: 'restart',
        enabled: true,
        frequency: 'daily',
        date: new Date().toISOString().split('T')[0],
        time: '02:00',
        weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        monthday: 1,
        cron_expression: '0 2 * * 1-5',
      }
      availableTargets.value = []
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
      } catch (err) {
        alert('Failed to delete schedule: ' + err.message)
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString()
    }

    const openCreateModal = async () => {
      resetForm()
      await loadAvailableTargets()
      showCreateModal.value = true
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
      availableTargets,
      schedulePreview,
      createSchedule,
      toggleSchedule,
      deleteSchedule,
      formatDate,
      onFrequencyChange,
      toggleWeekday,
      openCreateModal,
      loadAvailableTargets,
    }
  },
}
</script>

<style scoped>
.schedules-view { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }

.action-badge { background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: 500; }
code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 12px; color: #d73a49; }

.modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.modal-large { max-width: 600px; max-height: 90vh; overflow-y: auto; }
.modal-content { background: white; padding: 30px; border-radius: 8px; width: 500px; max-width: 90%; }
.modal-content h2 { margin-bottom: 20px; }

.form-section { margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.form-section h3 { margin: 0 0 15px 0; color: #333; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 14px; }
.form-group input, .form-group select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.form-group small { display: block; margin-top: 4px; color: #666; font-size: 12px; }

.action-buttons { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.action-btn { padding: 10px 12px; border: 2px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-weight: 500; font-size: 12px; transition: all 0.2s; }
.action-btn:hover { border-color: #0066cc; color: #0066cc; }
.action-btn.active { background: #0066cc; color: white; border-color: #0066cc; }

.weekday-selector { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.checkbox { display: flex; align-items: center; cursor: pointer; font-size: 13px; }
.checkbox input { margin-right: 8px; cursor: pointer; }
.checkbox span { user-select: none; }

.checkbox-large { display: flex; align-items: center; cursor: pointer; font-size: 14px; font-weight: 500; }
.checkbox-large input { margin-right: 10px; cursor: pointer; width: 18px; height: 18px; }
.checkbox-large span { user-select: none; }

.schedule-preview { background: #e8f4ff; border-left: 4px solid #0066cc; padding: 12px; border-radius: 4px; margin-top: 15px; }
.schedule-preview strong { display: block; color: #0066cc; margin-bottom: 5px; font-size: 12px; }
.schedule-preview p { margin: 0; color: #333; font-size: 13px; }

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
.btn-sm { padding: 6px 10px; font-size: 12px; margin: 0 2px; }
</style>
