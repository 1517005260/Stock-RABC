import { createStore } from 'vuex'

export default createStore({
  state: {
    editableTabsValue:'/index',
    editableTabs:[
      {
        title:'首页',
        name:'/index'
      }
    ]
  },
  getters: {},
  mutations: {
    ADD_TABS: (state, tab) => {
      if (state.editableTabs.findIndex(e => e.name === tab.path) === -1) {
        state.editableTabs.push({
          title: tab.name,
          name: tab.path
        });
      }
      state.editableTabsValue = tab.path
    },
    RESET_TABS: (state) => {
      state.editableTabsValue = '/index';
      state.editableTabs = [
        {
          title: '首页',
          name: '/index'
        }
      ]
    }
  },
  actions: {
  },
  modules: {
  }
})
