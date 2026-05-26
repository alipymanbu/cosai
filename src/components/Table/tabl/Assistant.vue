<template>
  <div class="builder-container" ref="containerRef">
    <!-- 关闭按钮 -->
    <button class="close-btn" @click="hide" title="关闭">
      <span class="close-icon">×</span>
    </button>
    
    <!-- 清空历史按钮 -->
    <button 
      v-if="messages.length > 0" 
      class="clear-history-btn" 
      @click="clearHistory" 
      title="清空历史记录"
    >

      <span>清空历史</span>
    </button>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="messages-container">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="builder-logo">
            <div class="logo-icon">
              <div class="logo-square">
                <div class="logo-dots">
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
            </div>
            <h1 class="builder-title">AI 助手</h1>
            <p class="builder-subtitle">定制化 AI 助手，为用户提供智能助手。</p>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div v-else class="messages-list">
          <div 
            v-for="msg in messages" 
            :key="msg.id" 
            :class="['message-item', msg.sender === 'user' ? 'user-message' : 'ai-message']"
          >
            <div class="message-content">
              <div class="message-text" v-html="parseMarkdown(msg.content)"></div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>
          
          <!-- 加载动画 -->
          <div v-if="isLoading" class="message-item ai-message loading-message">
            <div class="message-content">
              <div class="loading-spinner"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 聊天输入区域 -->
    <div class="chat-input-area">
      <div class="chat-input-container">
    
        <div class="chat-input-wrapper">
          <input 
            ref="chatInputRef"
            type="text" 
            class="chat-input" 
            placeholder="开始聊天吧" 
            v-model="message"
            @keydown.enter="sendMessage"
          />
          <div class="input-actions">
        
            <button class="action-icon attachment-btn">
              <img src="../../../../public/dividers.png" alt="选择" />
            </button>
            <div class="divider"></div>
       
            <button class="send-btn" @click="sendMessage" v-if="!isLoading">
              <span class="send-icon">↑</span>
            </button>
            <button class="pause-btn" @click="cancelRequest" v-else>
              <span class="pause-icon">⏸</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 调整宽度的拖拽手柄 -->
    <div class="resize-handle" @mousedown="startResize"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useAiStore } from '@/stores/store/AssistantStore';
import { useMaskStore } from '@/stores/store/SelectionStore';

const maskStore = useMaskStore();
const aiStore = useAiStore();
const message = ref('');
const chatInputRef = ref<HTMLInputElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);
const isResizing = ref(false);
const minWidth = 300;

let initialWidth = 0;
let initialX = 0;

// 消息类型定义
interface Message {
  id: number;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

// 消息列表
const messages = ref<Message[]>([]);
let messageId = 0;
const isLoading = ref(false);

// localStorage 键名
const STORAGE_KEY = 'ai_chat_history';

// 保存聊天记录到 localStorage
const saveMessages = () => {
  try {
    const messagesToSave = messages.value.map(msg => ({
      ...msg,
      timestamp: msg.timestamp.toISOString()
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messagesToSave));
  } catch (e) {
    console.error('保存聊天记录失败:', e);
  }
};

// 从 localStorage 加载聊天记录
const loadMessages = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      messages.value = parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
      // 更新 messageId 以避免 ID 冲突
      if (messages.value.length > 0) {
        messageId = Math.max(...messages.value.map(m => m.id)) + 1;
      }
    }
  } catch (e) {
    console.error('加载聊天记录失败:', e);
  }
};

// 清空历史记录
const clearHistory = () => {
  if (confirm('确定要清空所有聊天记录吗？')) {
    messages.value = [];
    messageId = 0;
    localStorage.removeItem(STORAGE_KEY);
  }
};

const sendMessage = async () => {
  if (message.value.trim()) {
    const userMessage: Message = {
      id: messageId++,
      content: message.value.trim(),
      sender: 'user',
      timestamp: new Date()
    };
    messages.value.push(userMessage);
    
    message.value = '';
    isLoading.value = true;
    
    try {
      const response = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          message: userMessage.content
        })
      });
      
      if (response.ok) {
        let data = await response.json();
        data = JSON.parse(data.response);
        let content = '';
        
        if (data.type == 41 || data.type == 31) {
          content = data.content;
        } else {
          content = data.content;
        }
        
        const aiMessage: Message = {
          id: messageId++,
          content: content,
          sender: 'ai',
          timestamp: new Date()
        };

        messages.value.push(aiMessage);
      } else {
        const errorMessage: Message = {
          id: messageId++,
          content: '抱歉，AI 回复失败，请稍后重试。',
          sender: 'ai',
          timestamp: new Date()
        };
        messages.value.push(errorMessage);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: messageId++,
        content: '网络错误，请检查后端服务是否运行。',
        sender: 'ai',
        timestamp: new Date()
      };
      messages.value.push(errorMessage);
    } finally {
      isLoading.value = false;
      saveMessages();
    }
  }
};

const cancelRequest = () => {
  isLoading.value = false;
};

const hide = () => {
  aiStore.hide();
};

const handleClickOutside = (e: MouseEvent) => {
  if (containerRef.value && chatInputRef.value && !containerRef.value.contains(e.target as Node)) {
    chatInputRef.value.blur();
  }
};

// 格式化时间
const formatTime = (date: Date) => {
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
};


const startResize = (e: MouseEvent) => {
  e.preventDefault();
  const container = containerRef.value;
  if (container) {
    initialWidth = container.offsetWidth;
    initialX = e.clientX;
  }
  isResizing.value = true;
  document.body.style.cursor = 'ew-resize';
};

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return;
  
  const container = containerRef.value;
  if (!container) return;
  
  const maxWidthPercent = window.innerWidth * 0.5;
  const deltaX = initialX - e.clientX;


  const newWidth = initialWidth + deltaX;

  
  if (newWidth >= minWidth && newWidth <= maxWidthPercent) {
    maskStore.aiInput = newWidth;
    container.style.width = `${newWidth}px`;
  }
};

const stopResize = () => {
  isResizing.value = false;
  document.body.style.cursor = 'default';
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  loadMessages();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
});

const parseMarkdown = (text: string) => {
  if (!text) return '';
  return text;
};
</script>

<style scoped>
.builder-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 350px;
  background: #ffffff;
  color: #333333;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  border: 1px solid #e0e0e0;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: transparent;
  border: none;
  color: #6b7280;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.close-icon {
  font-size: 18px;
  font-weight: bold;
  line-height: 1;
}

/* 清空历史按钮 */
.clear-history-btn {
  position: absolute;
  top: 8px;
  left: 16px;
  background: transparent;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  transition: all 0.2s;
  z-index: 10;
}

.clear-history-btn:hover {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #ef4444;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e0e0e0;
  overflow-y: auto;
}

.messages-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  margin: 0;
}

.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.builder-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-square {
  width: 60px;
  height: 60px;
  background: #ffffff;
  border: 2px solid #3b82f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo-dots {
  display: flex;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  background: #3b82f6;
  border-radius: 50%;
}

.builder-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #333333;
}

.builder-subtitle {
  font-size: 12px;
  color: #6b7280;
  max-width: 300px;
  margin: 0;
  line-height: 1.5;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.message-item {
  display: flex;
  margin: 0;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 13px;
  line-height: 1.4;
}

.user-message .message-content {
  background: #3b82f6;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.ai-message .message-content {
  background: #ffffff;
  color: #333333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

/* 加载动画 */
.loading-message .message-content {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 20px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.message-time {
  font-size: 10px;
  opacity: 0.7;
  margin-top: 4px;
  text-align: right;
}

/* 聊天输入区域 */
.chat-input-area {
  background: #ffffff;
  padding: 12px;
}

.chat-input-container {
  background: #ffffff;
  border-radius: 6px;
  padding: 8px;
  border: 1px solid #d1d5db;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.chat-label {
  font-size: 11px;
  font-weight: 500;
  color: #333333;
}

.chat-status {
  font-size: 11px;
  color: #10b981;
}

.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-input {
  flex: 1;
  background: #ffffff;

  padding: 6px 10px;
  color: #333333;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
}

.chat-input:focus {
  border-color: #d1d5db;
  box-shadow: none;
}

.chat-input::placeholder {
  color: #9ca3af;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.divider {
  width: 1px;
  height: 18px;
  background: #d1d5db;
  margin: 0 2px;
}

.action-icon {
  background: transparent;
  border: none;
  color: #6b7280;
  padding: 3px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.action-icon:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.attachment-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-btn img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.send-btn {
  background: #3b82f6;
  border: none;
  color: #ffffff;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.send-btn:hover {
  background: #2563eb;
}

.send-icon {
  font-size: 12px;
  font-weight: bold;
}

.pause-btn {
  background: #ef4444;
  border: none;
  color: #ffffff;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.pause-btn:hover {
  background: #dc2626;
}

.pause-icon {
  color: #000000;
  font-size: 12px;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {

  
  .builder-title {
    font-size: 16px;
  }
  
  .builder-subtitle {
    font-size: 11px;

  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
  }
  
  .logo-square {
    width: 45px;
    height: 45px;
  }
  
  .chat-input-area {
    padding: 10px;
  }
  
  .chat-input-container {
    padding: 6px;
  }
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: ew-resize;
  z-index: 20;
  background: transparent;
  transition: background 0.2s ease;
}

.resize-handle:hover {
  background: rgba(59, 130, 246, 0.2);
}

.resize-handle:active {
  background: rgba(59, 130, 246, 0.4);
}

/* Markdown 内容样式 - 使用 :deep() 穿透 scoped */
:deep(.message-text) h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 12px 0;
  color: #333333;
}

:deep(.message-text) h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 14px 0 10px 0;
  color: #333333;
}

:deep(.message-text) h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  color: #333333;
}
/* :deep(.message-text) p {
  margin: 8px 0;
  line-height: 1.6;
} */

:deep(.message-text) ul,
:deep(.message-text) ol {
  margin: 8px 0;
  padding-left: 20px;
}

:deep(.message-text) li {
  margin: 4px 0;
}

:deep(.message-text) code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

:deep(.message-text) pre {
  background: #f3f4f6;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

:deep(.message-text) pre code {
  background: transparent;
  padding: 0;
}

:deep(.message-text) strong {
  font-weight: 600;
  color: #1f2937;
}

:deep(.message-text) blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 12px;
  margin: 12px 0;
  color: #6b7280;
}

:deep(.message-text) table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

:deep(.message-text) th,
:deep(.message-text) td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

:deep(.message-text) th {
  background: #f9fafb;
  font-weight: 600;
}
</style>