import store from '@/store'

/**
 * 权限指令
 * 用法：v-permission="'system:user:edit'"
 * 或者：v-permission="['system:user:edit', 'system:user:query']"
 */
export const permission = {
  mounted(el, binding) {
    const { value } = binding
    const permissions = store.getters.getPermissions
    const roles = store.getters.getCurrentUser.roles || ''

    // 管理员角色拥有所有权限
    if (roles.includes('管理员')) {
      return true
    }

    if (value && value instanceof Array && value.length > 0) {
      // 判断是否拥有指令值中的任意一个权限
      const hasPermission = value.some(permission => {
        return permissions.includes(permission)
      })

      if (!hasPermission) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      // 单个权限判断
      const hasPermission = permissions.includes(value)
      
      if (!hasPermission) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    }
  }
}

/**
 * 角色指令
 * 用法：v-role="'admin'"
 * 或者：v-role="['admin', 'editor']"
 */
export const role = {
  mounted(el, binding) {
    const { value } = binding
    const roles = store.getters.getCurrentUser.roles || ''

    if (value && value instanceof Array && value.length > 0) {
      // 判断是否包含指令值中的任意一个角色
      const hasRole = value.some(role => {
        return roles.includes(role)
      })

      if (!hasRole) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      // 单个角色判断
      const hasRole = roles.includes(value)
      
      if (!hasRole) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    }
  }
}

// 注册指令
export default {
  install(app) {
    app.directive('permission', permission)
    app.directive('role', role)
  }
} 