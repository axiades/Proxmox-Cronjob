<template>
  <nav class="navbar">
    <div class="navbar-brand">
      <h1>Proxmox Cronjob Manager</h1>
    </div>
    <div class="navbar-menu">
      <router-link to="/" class="nav-link">Dashboard</router-link>
      <router-link to="/vms" class="nav-link">VMs</router-link>
      <router-link to="/schedules" class="nav-link">Schedules</router-link>
      <router-link to="/groups" class="nav-link">Groups</router-link>
      <router-link to="/blackouts" class="nav-link">Blackouts</router-link>
      <router-link to="/logs" class="nav-link">Logs</router-link>
    </div>
    <div class="navbar-actions">
      <span class="user-name">Admin</span>
      <button @click="logout" class="btn btn-secondary">Logout</button>
    </div>
  </nav>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'Navbar',
  setup() {
    const router = useRouter()
    
    const logout = () => {
      localStorage.removeItem('auth_token')
      router.push('/login')
    }
    
    return {
      logout,
    }
  },
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.navbar-brand h1 {
  font-size: 20px;
  margin: 0;
}

.navbar-menu {
  display: flex;
  gap: 10px;
  margin-left: 40px;
  flex: 1;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  font-size: 14px;
}
</style>
