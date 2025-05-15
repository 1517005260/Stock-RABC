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
    menuList: []
  },
  getters: {
    getToken: state => state.token || sessionStorage.getItem('token'),
    getCurrentUser: state => state.currentUser || JSON.parse(sessionStorage.getItem('currentUser') || '{}'),
    getMenuList: state => state.menuList || JSON.parse(sessionStorage.getItem('menuList') || '[]')
  },
  mutations: {
    // Tabs 相关操作
    ADD_TABS: (state, tab) => {
      if (!tab || !tab.path) return
      
      if (state.editableTabs.findIndex(e => e.name === tab.path) === -1) {
        state.editableTabs.push({
          title: tab.name,
          name: tab.path
        });
      }
      state.editableTabsValue = tab.path
    },
    UPDATE_TAB_VALUE: (state, path) => {
      if (path) {
        state.editableTabsValue = path
      }
    },
    REMOVE_TAB: (state, targetName) => {
      if (!targetName) return
      
      const tabs = state.editableTabs
      let activeName = state.editableTabsValue
      
      if (activeName === targetName) {
        tabs.forEach((tab, index) => {
          if (tab.name === targetName) {
            const nextTab = tabs[index + 1] || tabs[index - 1]
            if (nextTab) {
              activeName = nextTab.name
            }
          }
        })
      }
      
      state.editableTabsValue = activeName
      state.editableTabs = tabs.filter(tab => tab.name !== targetName)
    },
    RESET_TABS: (state) => {
      state.editableTabsValue = '/index';
      state.editableTabs = [
        {
          title: '首页',
          name: '/index'
        }
      ]
    },
    
    // 用户认证相关操作
    SET_TOKEN: (state, token) => {
      state.token = token
      if (token) {
        sessionStorage.setItem('token', token)
      } else {
        sessionStorage.removeItem('token')
      }
    },
    SET_CURRENT_USER: (state, user) => {
      state.currentUser = user
      if (user) {
        sessionStorage.setItem('currentUser', JSON.stringify(user))
      } else {
        sessionStorage.removeItem('currentUser')
      }
    },
    SET_MENU_LIST: (state, menuList) => {
      state.menuList = menuList
      if (menuList) {
        sessionStorage.setItem('menuList', JSON.stringify(menuList))
      } else {
        sessionStorage.removeItem('menuList')
      }
    },
    LOGOUT: (state) => {
      state.token = null
      state.currentUser = null
      state.menuList = []
      state.editableTabsValue = '/index'
      state.editableTabs = [{title: '首页', name: '/index'}]
      sessionStorage.clear()
    }
  },
  actions: {
    login({ commit }, userData) {
      return new Promise((resolve, reject) => {
        // 这里可以添加实际的登录API调用
        // 目前只是模拟存储数据
        commit('SET_TOKEN', userData.token)
        commit('SET_CURRENT_USER', userData.user)
        commit('SET_MENU_LIST', userData.menuList)
        resolve()
      })
    },
    logout({ commit }) {
      return new Promise((resolve) => {
        commit('LOGOUT')
        resolve()
      })
    }
  },
  modules: {
  }
})