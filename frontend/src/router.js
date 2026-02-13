import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/vms',
    name: 'VMs',
    component: () => import('@/views/VMsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('@/views/SchedulesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: () => import('@/views/GroupsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/blackouts',
    name: 'Blackouts',
    component: () => import('@/views/BlackoutsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/LogsView.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('auth_token')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
