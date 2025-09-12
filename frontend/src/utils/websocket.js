/**
 * WebSocket服务封装 - 用于实时股票数据推送
 */
class WebSocketService {
  constructor() {
    this.ws = null
    this.isConnected = false
    this.reconnectTimer = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.heartbeatTimer = null
    this.heartbeatInterval = 30000
    this.subscriptions = new Set() // 存储订阅的股票代码
    this.messageHandlers = new Map() // 消息处理器
    this.token = sessionStorage.getItem('token')
    this.baseUrl = process.env.NODE_ENV === 'production' 
      ? 'wss://your-domain.com/ws' 
      : 'ws://localhost:8000/ws'
  }

  /**
   * 连接WebSocket服务器
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.baseUrl}/stock/realtime/general/?token=${this.token}`
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket连接成功')
          this.isConnected = true
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event)
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          this.isConnected = false
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭')
          this.isConnected = false
          this.stopHeartbeat()
          this.handleReconnect()
        }
      } catch (error) {
        console.error('创建WebSocket连接失败:', error)
        reject(error)
      }
    })
  }

  /**
   * 处理接收到的消息
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'connection_established':
          console.log('WebSocket连接建立成功')
          this.resubscribeAll()
          break
        case 'market_data':
          this.notifyHandlers('market_data', data.data)
          break
        case 'realtime_data':
          this.notifyHandlers('realtime_data', data.data)
          break
        case 'news_update':
          this.notifyHandlers('news_update', data.data)
          break
        case 'pong':
          // 心跳响应，不需要处理
          break
        default:
          console.log('未知消息类型:', data.type)
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  /**
   * 通知消息处理器
   */
  notifyHandlers(type, data) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error('消息处理器执行失败:', error)
        }
      })
    }
  }

  /**
   * 订阅股票实时数据
   */
  subscribe(tsCodes) {
    if (!Array.isArray(tsCodes)) {
      tsCodes = [tsCodes]
    }

    tsCodes.forEach(code => {
      this.subscriptions.add(code)
    })

    if (this.isConnected) {
      this.sendMessage({
        type: 'subscribe',
        ts_codes: tsCodes
      })
    }
  }

  /**
   * 取消订阅股票实时数据
   */
  unsubscribe(tsCodes) {
    if (!Array.isArray(tsCodes)) {
      tsCodes = [tsCodes]
    }

    tsCodes.forEach(code => {
      this.subscriptions.delete(code)
    })

    if (this.isConnected) {
      this.sendMessage({
        type: 'unsubscribe',
        ts_codes: tsCodes
      })
    }
  }

  /**
   * 重新订阅所有股票
   */
  resubscribeAll() {
    if (this.subscriptions.size > 0) {
      this.sendMessage({
        type: 'subscribe',
        ts_codes: Array.from(this.subscriptions)
      })
    }
  }

  /**
   * 添加消息处理器
   */
  addMessageHandler(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }
    this.messageHandlers.get(type).add(handler)
  }

  /**
   * 移除消息处理器
   */
  removeMessageHandler(type, handler) {
    if (this.messageHandlers.has(type)) {
      this.messageHandlers.get(type).delete(handler)
    }
  }

  /**
   * 发送消息
   */
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，消息发送失败')
    }
  }

  /**
   * 开启心跳检测
   */
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.sendMessage({ type: 'ping' })
      }
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳检测
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理重连
   */
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限，停止重连')
      return
    }

    this.reconnectTimer = setTimeout(() => {
      console.log(`WebSocket重连中... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
      this.reconnectAttempts++
      this.connect().catch(() => {
        // 重连失败，继续下次重连
      })
    }, this.reconnectInterval)
  }

  /**
   * 关闭连接
   */
  disconnect() {
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.isConnected = false
    this.subscriptions.clear()
    this.messageHandlers.clear()
  }

  /**
   * 更新认证令牌
   */
  updateToken(token) {
    this.token = token
    // 如果当前已连接，需要重新连接以使用新token
    if (this.isConnected) {
      this.disconnect()
      this.connect()
    }
  }
}

// 创建全局WebSocket服务实例
const wsService = new WebSocketService()

export default wsService