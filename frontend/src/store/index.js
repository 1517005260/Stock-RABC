import { createStore } from 'vuex'

export default createStore({
  state: {
    editableTabsValue:'/index',
    editableTabs:[
      {
        title:'首页',
        name:'/index'
      }
    ],
    currentUser: null,
    token: null,
    permissions: []
  },
  getters: {
    getToken: state => state.token || sessionStorage.getItem('token'),
    getCurrentUser: state => state.currentUser || JSON.parse(sessionStorage.getItem('currentUser') || '{}'),
    getPermissions: state => {
      if (state.permissions && state.permissions.length > 0) {
        return state.permissions
      }
      
      const storedPermissions = sessionStorage.getItem('permissions')
      return storedPermissions ? JSON.parse(storedPermissions) : []
    },
    hasPermission: (state, getters) => (permission) => {
      const permissions = getters.getPermissions
      const userRoles = getters.getCurrentUser.roles || ''
      
      // 超级管理员拥有所有权限
      if (userRoles.includes('超级管理员')) {
        return true
      }
      
      // 管理员拥有用户管理相关权限和角色列表查看权限
      if (userRoles.includes('管理员')) {
        if (permission.startsWith('system:user:') || permission === 'system:role:list') {
          // 管理员不能删除用户
          if (permission === 'system:user:remove') {
            return false
          }
          return true
        }
      }
      
      // 检查用户的具体权限
      return permissions.includes(permission)
    }
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token
      sessionStorage.setItem('token', token)
    },
    SET_CURRENT_USER(state, user) {
      state.currentUser = user
      sessionStorage.setItem('currentUser', JSON.stringify(user))
    },
    SET_PERMISSIONS(state, permissions) {
      state.permissions = permissions
      sessionStorage.setItem('permissions', JSON.stringify(permissions))
    },
    SET_EDITABLE_TABS(state, tabs) {
      state.editableTabs = tabs
    },
    SET_EDITABLE_TABS_VALUE(state, tabValue) {
      state.editableTabsValue = tabValue
    },
    RESET_TABS(state) {
      state.editableTabs = [{title: '首页', name: '/index'}]
      state.editableTabsValue = '/index'
    },
    LOGOUT(state) {
      state.token = null
      state.currentUser = null
      state.permissions = []
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('currentUser')
      sessionStorage.removeItem('permissions')
      state.editableTabs = [{title: '首页', name: '/index'}]
      state.editableTabsValue = '/index'
    }
  },
  actions: {
    login({ commit }, data) {
      commit('SET_TOKEN', data.token)
      commit('SET_CURRENT_USER', data.user)
      if (data.permissions) {
        commit('SET_PERMISSIONS', data.permissions)
      }
    },
    logout({ commit }) {
      commit('LOGOUT')
    }
  },
  modules: {
  }
})