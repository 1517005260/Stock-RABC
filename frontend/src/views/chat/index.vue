<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>AI聊天助手</h2>
      <div class="header-actions">
        <div class="usage-info">
          <el-tag v-if="usage.is_admin" type="success">管理员账号</el-tag>
          <el-tag v-else type="info">普通账号：今日已用 {{ usage.today_count }}/{{ usage.daily_limit }} 次</el-tag>
        </div>
        <el-button 
          type="default" 
          size="small" 
          icon="Delete" 
          @click="clearChatHistory"
          :disabled="chatHistory.length === 0"
        >
          清除记录
        </el-button>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <template v-if="chatHistory.length === 0 && !currentMessage">
        <div class="welcome-message">
          <el-empty description="暂无聊天记录" />
          <p v-if="historyCleared">聊天记录已清除，您可以开始新的对话</p>
          <p v-else>您可以在下方输入框发送消息开始聊天</p>
        </div>
      </template>
      
      <!-- 历史聊天记录 -->
      <div v-for="(message, index) in chatHistory" :key="`history-${index}`" class="message-group">
        <div class="user-message">
          <div class="avatar">
            <el-avatar :size="40" :src="currentUserAvatar" />
          </div>
          <div class="message-content">
            <p>{{ message.content }}</p>
            <span class="message-time">{{ message.created_time }}</span>
          </div>
        </div>
        <div class="ai-message">
          <div class="avatar">
            <el-avatar :size="40" :icon="ChatDotRound" />
          </div>
          <div class="message-content">
            <p v-html="formatMessage(message.response)"></p>
            <span class="message-time">{{ message.created_time }} · {{ message.model }}</span>
          </div>
        </div>
      </div>
      
      <!-- 当前正在进行的对话 -->
      <div v-if="currentMessage" class="message-group current-message">
        <div class="user-message">
          <div class="avatar">
            <el-avatar :size="40" :src="currentUserAvatar" />
          </div>
          <div class="message-content">
            <p>{{ currentMessage }}</p>
            <span class="message-time">刚刚</span>
          </div>
        </div>
        <div v-if="isWaitingResponse || currentResponse" class="ai-message">
          <div class="avatar">
            <el-avatar :size="40" :icon="ChatDotRound" />
          </div>
          <div class="message-content">
            <p v-if="currentResponse" v-html="formatMessage(currentResponse)"></p>
            <p v-else><span class="typing-indicator"></span></p>
            <span class="message-time">正在回复...</span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="messageInput"
        type="textarea"
        :rows="3"
        placeholder="请输入消息..."
        :disabled="isWaitingResponse || !usage.can_chat"
        @keyup.enter.exact.prevent="sendMessage"
      ></el-input>
      <div class="input-actions">
        <el-button 
          type="primary" 
          @click="sendMessage" 
          :disabled="isWaitingResponse || !messageInput.trim() || !usage.can_chat"
        >
          发送
        </el-button>
        <el-tooltip v-if="!usage.can_chat && !usage.is_admin" content="您今日的对话次数已达上限" placement="top">
          <el-button type="info" icon="InfoFilled"></el-button>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/util/request'
import { ChatDotRound, InfoFilled, Delete } from '@element-plus/icons-vue'

export default {
  name: 'ChatView',
  setup() {
    const messageInput = ref('')
    const chatHistory = ref([])
    const currentMessage = ref('')
    const currentResponse = ref('')
    const isWaitingResponse = ref(false)
    const messagesContainer = ref(null)
    const eventSource = ref(null)
    const usage = ref({
      is_admin: false,
      today_count: 0,
      daily_limit: 5,
      can_chat: true
    })
    const historyCleared = ref(false)
    
    // 获取当前用户头像
    const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
    const currentUserAvatar = computed(() => {
      const avatar = currentUser.avatar || ''
      // 如果avatarUrl是相对路径，添加服务器前缀
      if (avatar && !avatar.startsWith('http')) {
        return `${request.getServerUrl()}${avatar}`;
      }
      return avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
    })
    
    // 加载聊天历史
    const loadChatHistory = async () => {
      try {
        const response = await request.get('chat/')
        if (response.data && response.data.code === 200) {
          // 清除当前对话，以避免重复显示
          currentMessage.value = ''
          currentResponse.value = ''
          historyCleared.value = false
          
          // 检查聊天历史是否为数组
          if (Array.isArray(response.data.chat_history)) {
            try {
              // 设置聊天历史并按照时间顺序排列（从早到晚）
              chatHistory.value = response.data.chat_history.sort((a, b) => {
                try {
                  return new Date(a.created_time) - new Date(b.created_time);
                } catch (e) {
                  console.error('排序聊天历史时出错:', e);
                  return 0; // 保持原始顺序
                }
              });
            } catch (sortError) {
              console.error('对聊天历史排序失败:', sortError);
              chatHistory.value = response.data.chat_history;
            }
          } else {
            console.error('聊天历史不是有效的数组');
            chatHistory.value = [];
          }
          
          // 更新使用信息
          if (response.data.usage) {
            usage.value = response.data.usage;
          }
          
          // 滚动到底部
          await nextTick()
          scrollToBottom()
        }
      } catch (error) {
        console.error('加载聊天历史失败:', error)
        ElMessage.error('加载聊天历史失败')
      }
    }
    
    // 发送消息
    const sendMessage = async () => {
      const message = messageInput.value.trim()
      if (!message) return
      
      // 保存当前消息并清空输入框
      currentMessage.value = message
      messageInput.value = ''
      currentResponse.value = ''
      isWaitingResponse.value = true
      
      try {
        // 发送消息到服务器
        const response = await request.post('chat/', { message })
        
        if (response.data && response.data.code === 200) {
          // 更新使用情况
          usage.value = response.data.usage
          
          // 建立SSE连接获取流式响应
          const chatId = response.data.chat_id
          connectEventSource(chatId)
        } else {
          ElMessage.error(response.data.message || '发送消息失败')
          isWaitingResponse.value = false
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error(error.response?.data?.message || '发送消息失败')
        isWaitingResponse.value = false
      }
      
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
    
    // 连接SSE事件流
    const connectEventSource = (chatId) => {
      // 关闭之前的连接
      if (eventSource.value) {
        eventSource.value.close()
      }
      
      // 获取token
      const token = sessionStorage.getItem('token')
      
      try {
        // 创建新的SSE连接，带上token
        const url = `${request.getServerUrl()}chat/stream/${chatId}/`
        console.log('连接SSE URL:', url)
        
        // 创建URL对象
        const eventUrl = new URL(url)
        
        // 添加token作为URL参数
        if (token) {
          eventUrl.searchParams.append('token', token)
        }
        
        console.log('带token的SSE URL:', eventUrl.toString())
        
        // 创建事件源
        eventSource.value = new EventSource(eventUrl.toString())
        
        // 监听连接打开
        eventSource.value.onopen = () => {
          console.log('SSE连接已打开')
        }
        
        // 监听消息
        eventSource.value.onmessage = (event) => {
          console.log('收到SSE消息:', event.data)
          
          try {
            // 确保数据有效
            if (!event || !event.data) {
              console.warn('接收到无效的SSE消息数据')
              return
            }
            
            if (event.data === '[DONE]') {
              // 响应完成
              console.log('SSE响应完成')
              isWaitingResponse.value = false
              eventSource.value.close()
              
              // 重新加载聊天历史
              loadChatHistory()
            } else {
              // 添加到当前响应
              currentResponse.value += event.data
              
              // 滚动到底部
              nextTick(() => {
                scrollToBottom()
              })
            }
          } catch (error) {
            console.error('处理SSE消息时出错:', error)
            ElMessage.error('处理响应失败')
          }
        }
        
        // 监听错误
        eventSource.value.onerror = (error) => {
          console.error('SSE连接错误:', error)
          ElMessage.error('获取响应失败，请重试')
          isWaitingResponse.value = false
          
          if (eventSource.value) {
            eventSource.value.close()
          }
          
          // 短暂延迟后尝试重新加载聊天历史
          setTimeout(() => {
            currentMessage.value = ''
            currentResponse.value = ''
            loadChatHistory()
          }, 2000)
        }
      } catch (error) {
        console.error('创建SSE连接失败:', error)
        ElMessage.error('连接服务器失败')
        isWaitingResponse.value = false
      }
    }
    
    // 格式化消息文本（处理换行和代码块）
    const formatMessage = (text) => {
      if (!text) return ''
      
      // 将换行符转换为<br>
      let formatted = text.replace(/\n/g, '<br>')
      
      // 简单处理代码块
      formatted = formatted.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
      
      return formatted
    }
    
    // 滚动到底部
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
    
    // 清除聊天历史（更新后端标记）
    const clearChatHistory = () => {
      // 对话仍在进行中时提供额外警告
      const message = isWaitingResponse.value
        ? '你有一个正在进行的对话，清除记录会中断当前对话。确定要清除聊天记录吗？'
        : '确定要清除聊天记录吗？';

      ElMessageBox.confirm(
        message,
        '清除聊天记录',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
        .then(async () => {
          try {
            // 调用后端API标记所有消息为隐藏
            const response = await request.put('chat/', { 
              action: 'hide_all' 
            });
            
            if (response.data && response.data.code === 200) {
              // 清除本地聊天历史
              chatHistory.value = [];
              historyCleared.value = true;
              
              // 如果有正在进行的对话，也清除它
              if (isWaitingResponse.value) {
                currentMessage.value = '';
                currentResponse.value = '';
                isWaitingResponse.value = false;
                
                // 关闭SSE连接
                if (eventSource.value) {
                  eventSource.value.close();
                  eventSource.value = null;
                }
              }
              
              ElMessage({
                type: 'success',
                message: response.data.message || '聊天记录已清除',
              });
            } else {
              ElMessage.error(response.data?.message || '清除记录失败');
            }
          } catch (error) {
            console.error('清除记录失败:', error);
            ElMessage.error(error.response?.data?.message || '清除记录失败');
          }
        })
        .catch(() => {
          // 用户取消
        });
    }
    
    // 组件挂载时加载聊天历史
    onMounted(() => {
      loadChatHistory()
    })
    
    return {
      messageInput,
      chatHistory,
      currentMessage,
      currentResponse,
      isWaitingResponse,
      messagesContainer,
      usage,
      currentUserAvatar,
      historyCleared,
      sendMessage,
      formatMessage,
      scrollToBottom,
      clearChatHistory,
      ChatDotRound,
      InfoFilled,
      Delete
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f9f9f9;
}

.welcome-message {
  text-align: center;
  color: #909399;
  margin-top: 80px;
}

.message-group {
  margin-bottom: 24px;
}

.current-message {
  border-top: 1px dashed #dcdfe6;
  padding-top: 20px;
  margin-top: 20px;
}

.user-message, .ai-message {
  display: flex;
  margin-bottom: 8px;
}

.ai-message {
  background-color: #f0f9ff;
  border-radius: 8px;
  padding: 8px;
}

.avatar {
  margin-right: 12px;
  align-self: flex-start;
}

.message-content {
  flex: 1;
}

.message-content p {
  margin: 0;
  padding: 8px 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.user-message .message-content p {
  background-color: #ecf5ff;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: inline-block;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #eaeaea;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.typing-indicator::after {
  content: "...";
  animation: typing 1s infinite;
}

@keyframes typing {
  0% { content: "."; }
  33% { content: ".."; }
  66% { content: "..."; }
}

/* 代码块样式 */
:deep(pre) {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

:deep(code) {
  font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
  font-size: 14px;
}

.usage-info {
  display: flex;
  align-items: center;
}
</style> 