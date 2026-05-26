<template>
    <div class="capsule">
        <ul>
            <li v-for="item in items" :key="item.id">
                <div class="context">
                    <div class="left">
                        <span 
                            v-if="editingId !== item.id" 
                            @dblclick="startEditing(item)"
                            class="item-name"
                            :title="item.name"
                        >
                            {{ item.name }}
                        </span>
                        <input 
                            v-else 
                            ref="editInputRef"
                            v-model="editingName"
                            @blur.stop="saveEditing(item)"
                            @keyup.enter.stop="saveEditing(item)"
                            @keyup.escape.stop="cancelEditing"
                            class="edit-input"
                        />
                    </div>
                        
                    <div class="right">
                        <component :is="item.component" v-if="item.component" />
                    </div>
                </div>
                <div class="radio-wrapper">
                    <button 
                      @click="handleAI(item)" 
                      class="ai-btn"
                      :title="'🤖 AI 生成'"
                    >
                      🤖 AI
                    </button>
                    <button @click="handleDelete(item)" class="delete-btn">删除</button>
                    <button @click="handleEdit(item)">编辑</button>
                    <label class="radio-button">
                        <input 
                          type="radio" 
                          :value="item.id.toString()" 
                          v-model="selectedId"
                          @change="handleSelectionChange"
                        >
                        <span class="radio-mark"></span>
                    </label>
                </div>
            </li>
            <li class="add-item">
                <button @click="addNewItem" class="add-button">
                    <span class="plus-icon">+</span>
                    <span>新增</span>
                </button>
            </li>
        </ul>
    </div>
</template>

<script lang="ts" setup>
import { ref, defineAsyncComponent, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCapsuleStore } from '@/stores/CapsuleStore'

const router = useRouter()
const capsuleStore = useCapsuleStore()

interface CapsuleItem {
  id: number
  name: string
  component: any
  componentName: string
}

const items = ref<CapsuleItem[]>([])
const itemCount = ref(0)
const API_BASE_URL = 'http://localhost:8000/api'
const loading = ref(true)
const hasLoaded = ref(false)

// 使用 Pinia store 的 selectedId
const selectedId = ref(capsuleStore.selectedId)

// 监听 selectedId 变化，同步到 store
watch(selectedId, (newVal) => {
  capsuleStore.setSelectedId(newVal)
  
  // 找到选中的项并获取 componentName
  const selectedItem = items.value.find(item => item.id.toString() === newVal)
  if (selectedItem) {
    console.log('✅ 选中项变化:', selectedItem.componentName)
  }
})

// 监听单选框变化
const handleSelectionChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  console.log('单选框变化:', target.value);
  console.log('当前 items:', items.value);
  
  if (target && target.value) {
    selectedId.value = target.value;
    console.log('✅ 已更新选中 ID:', target.value);
  }
}

// 自定义消息提示
const showMessage = (message: string, type: 'success' | 'error' = 'success') => {
  // 查找是否已有消息容器
  let container = document.getElementById('message-container')
  if (!container) {
    // 创建消息容器
    container = document.createElement('div')
    container.id = 'message-container'
    container.style.cssText = `
      position: fixed;
      top: 1.25rem;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: .625rem;
    `
    document.body.appendChild(container)
  }
  
  // 创建消息元素
  const messageEl = document.createElement('div')
  
  // 设置图标和颜色
  const icon = type === 'success' ? '✓' : '✕'
  const bgColor = type === 'success' ? '#eff6ff' : '#fef2f2'
  const borderColor = type === 'success' ? '#3b82f6' : '#ef4444'
  const textColor = type === 'success' ? '#1e40af' : '#991b1b'
  
  messageEl.innerHTML = `
    <span style="
      display: inline-flex;
      align-items: center;
      gap: .5rem;
      padding: .75rem 1.25rem;
      background: ${bgColor};
      border: .0625rem solid ${borderColor};
      border-radius: .5rem;
      color: ${textColor};
      font-size: .875rem;
      font-weight: 500;
      box-shadow: 0 .25rem .375rem -0.0625rem rgba(0, 0, 0, 0.1), 0 .125rem .25rem -0.0625rem rgba(0, 0, 0, 0.06);
    ">
      <span style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.25rem;
        height: 1.25rem;
        border-radius: 50%;
        background: ${borderColor};
        color: white;
        font-size: .75rem;
        font-weight: bold;
      ">${icon}</span>
      ${message}
    </span>
  `
  
  // 设置初始样式（用于动画）
  messageEl.style.cssText = `
    opacity: 0;
    transform: translateY(-1.25rem);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  `
  
  // 添加到容器
  container!.appendChild(messageEl)
  
  // 下一帧执行出现动画
  requestAnimationFrame(() => {
    messageEl.style.opacity = '1'
    messageEl.style.transform = 'translateY(0)'
  })
  
  // 3 秒后移除
  setTimeout(() => {
    // 执行消失动画
    messageEl.style.opacity = '0'
    messageEl.style.transform = 'translateY(-1.25rem)'
    
    // 等待动画完成后移除
    setTimeout(() => {
      container!.removeChild(messageEl)
      // 如果容器为空，移除容器
      if (container!.children.length === 0) {
        document.body.removeChild(container!)
      }
    }, 400)
  }, 3000)
}

// 重命名相关
const editingId = ref<number | null>(null)
const editingName = ref('')
const editInputRef = ref<HTMLInputElement | null>(null)

// 开始编辑
const startEditing = async (item: CapsuleItem) => {
  editingId.value = item.id
  editingName.value = item.name
  // 等待 DOM 更新后聚焦到输入框
  await nextTick()
  setTimeout(() => {
    if (editInputRef.value) {
      editInputRef.value.focus()
      // 将光标定位到末尾
      const length = editInputRef.value.value.length
      editInputRef.value.setSelectionRange(length, length)
    }
  }, 50)
}

// 保存编辑 - 调用后端修改文件，但只在本地数组更新
const saveEditing = async (item: CapsuleItem) => {
  const newName = editingName.value.trim()
  
  if (!newName) {
    console.error('名称不能为空')
    editingId.value = null
    editingName.value = ''
    return
  }
  
  if (newName === item.name) {
    editingId.value = null
    editingName.value = ''
    return
  }
  
  try {
    // 调用后端 API 修改文件夹名称
    const response = await fetch(`${API_BASE_URL}/rename-component`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        oldComponentName: item.componentName,
        newComponentName: newName,
        newName: newName
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      console.log('后端重命名成功:', result.message)
      // 直接在本地数组更新，不重新加载
      item.name = newName
      item.componentName = result.newComponentName || newName
      console.log(`本地数组已更新：${item.componentName}`)
      showMessage('重命名成功', 'success')
    } else {
      console.error('后端重命名失败:', result.error)
      showMessage(`重命名失败：${result.error}`, 'error')
    }
  } catch (error) {
    console.error('请求失败:', error)
    showMessage(`重命名失败：${error}`, 'error')
  } finally {
    editingId.value = null
    editingName.value = ''
  }
}

// 取消编辑
const cancelEditing = () => {
  editingId.value = null
  editingName.value = ''
}

// 从服务器加载已有的组件列表
const loadExistingComponents = async () => {
  if (hasLoaded.value) {
    console.log('数据已加载，跳过重复请求')
    return
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/components`)
    const result = await response.json()
    
    if (result.components && result.components.length > 0) {
      console.log('找到的组件:', result.components)
      
      for (const componentName of result.components) {
        itemCount.value++
        const id = itemCount.value
        
        let name = componentName
        if (componentName.startsWith('TopNav')) {
          const numPart = componentName.replace('TopNav', '')
          name = numPart ? `分析${numPart}` : '分析'
        }
        
        const component = defineAsyncComponent(() => {
          return import(`@/components/ToolsNavs/${componentName}/index.vue`)
        })
        
        items.value.push({
          id,
          name,
          component,
          componentName
        })
        
        console.log(`加载组件：${componentName}, 显示名称：${name}`)
      }
      
      // 加载完成后，从 store 恢复选中的项
      nextTick(() => {
        capsuleStore.restoreFromStorage()
        const savedSelectedId = capsuleStore.selectedId
        console.log('📦 从 store 恢复选中 ID:', savedSelectedId)
        
        if (savedSelectedId) {
          // 检查保存的 ID 是否存在于当前列表中
          const exists = items.value.some(item => item.id.toString() === savedSelectedId)
          if (exists) {
            selectedId.value = savedSelectedId
            console.log('✅ 已恢复选中项:', savedSelectedId)
          } else {
            // 如果保存的 ID 不存在，选中第一个
            selectedId.value = '1'
            capsuleStore.setSelectedId('1')
            console.log('⚠️ 保存的 ID 不存在，已选中第一个项')
          }
        } else {
          // 如果没有保存的 ID，默认选中第一个
          selectedId.value = '1'
          capsuleStore.setSelectedId('1')
          console.log('ℹ️ 没有保存的选中项，默认选中第一个')
        }
      })
    }
    
    hasLoaded.value = true
    loading.value = false
  } catch (error) {
    console.error('加载组件列表失败:', error)
    loading.value = false
  }
}

const handleEdit = (item: CapsuleItem) => {
  console.log('编辑:', item.name)
  console.log('组件名:', item.componentName)
  console.log('准备跳转到:', `/editor/${item.componentName}`)
  // 跳转到编辑器页面，传递组件名
  router.push(`/editor/${item.componentName}`)
  console.log('跳转已执行')
}

// AI 生成（预留功能）
const handleAI = async (item: CapsuleItem) => {
  console.log('🤖 AI 生成功能暂未启用')
  showMessage('🤖 AI 生成功能开发中...', 'success')
}

// 删除组件 - 调用后端删除文件，但只在本地数组更新
const handleDelete = async (item: CapsuleItem) => {
  if (!confirm(`确定要删除组件 "${item.name}" 吗？此操作不可恢复！`)) {
    return
  }
  
  try {
    // 调用后端 API 删除文件夹
    const response = await fetch(`${API_BASE_URL}/delete-component`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        componentName: item.componentName
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      console.log('后端删除成功:', result.message)
      // 直接在本地数组中移除，不重新加载
      const index = items.value.findIndex(i => i.id === item.id)
      if (index !== -1) {
        items.value.splice(index, 1)
      }
      showMessage(`组件 "${item.name}" 已删除`, 'success')
    } else {
      console.error('后端删除失败:', result.error)
      showMessage(`删除失败：${result.error}`, 'error')
    }
  } catch (error) {
    console.error('请求失败:', error)
    showMessage(`删除失败：${error}`, 'error')
  }
}

const addNewItem = async () => {
  try {
    itemCount.value++
    const newId = itemCount.value
    const componentName = `TopNav${newId - 1}`
    
    // 调用 Flask API 创建组件文件
    const response = await fetch(`${API_BASE_URL}/create-component`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        componentName: componentName
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      console.log(result.message)
      console.log('文件路径:', result.path)
      
      // 动态导入新创建的组件
      const newComponent = defineAsyncComponent(() => {
        return import(`@/components/ToolsNavs/${componentName}/index.vue`)
      })
      
      // 添加新的列表项
      items.value.push({
        id: newId,
        name: `分析${newId - 1}`,
        component: newComponent,
        componentName: componentName
      })
      
      console.log(`新增组件：${componentName}`)
      showMessage(`组件 "${componentName}" 创建成功`, 'success')
    } else {
      console.error('创建组件失败:', result.error)
      showMessage(`创建失败：${result.error}`, 'error')
    }
  } catch (error) {
    console.error('请求失败:', error)
    showMessage(`创建失败：${error}`, 'error')
  }
}

// 组件挂载时加载已有组件
onMounted(() => {
  loadExistingComponents()
})
</script>

<style scoped lang="scss">
.item-name {
  cursor: pointer;
  padding: .25rem .5rem;
  border-radius: .25rem;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  &:active {
    background-color: rgba(0, 0, 0, 0.1);
  }
}

.edit-input {
  padding: .25rem .5rem;
  border: .125rem solid #3b82f6;
  border-radius: .25rem;
  font-size: inherit;
  font-family: inherit;
  outline: none;
  background: #fff;
  min-width: 6.25rem;
  
  &:focus {
    box-shadow: 0 0 0 .1875rem rgba(59, 130, 246, 0.2);
  }
}

.add-item {
  margin-top: .625rem;
  padding: 1.25rem;
  
  .add-button {
    width: 100%;
    height: 3.125rem;
    border-radius: .625rem;
    border: .125rem dashed #ccc;
    background: #fff;
    color: #666;
    font-size: .875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .5rem;
    box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.05);
    
    &:hover {
      border-color: #3b82f6;
      background: #f0f7ff;
      color: #3b82f6;
      box-shadow: 0 .25rem .5rem rgba(59, 130, 246, 0.2);
      transform: translateY(-0.125rem);
      
      .plus-icon {
        transform: rotate(90deg);
      }
    }
    
    &:active {
      transform: translateY(0);
      box-shadow: 0 .125rem .25rem rgba(59, 130, 246, 0.15);
    }
    
    .plus-icon {
      font-size: 1.25rem;
      font-weight: bold;
      transition: transform 0.3s ease;
      line-height: 1;
    }
  }
}

.capsule {
    width: 100%;
    height: 100vh;
    background-color: #f5f5f5;
    border-right: .0625rem solid #ccc;
    padding: .625rem;
    overflow-y: auto;
    overflow-x: hidden;
    
    ul {
        li {
            align-items: center;
            border: .0625rem solid #ccc;
            display: flex;
            justify-content: space-between;
            padding: 1.25rem;
            border-left: .0625rem solid #ccc;
            
            .context {
                display: flex;
                align-items: center;
                .left {
                    padding-right: 1.25rem;
                    border-right: .0625rem solid #978b8b;
                }
                .right {
                    flex: 1;
                    margin-left: .625rem;
                }
             
            }
            .radio-wrapper {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                flex-direction: row;
                gap: 1.25rem;
                margin-top: .625rem;
                .delete-btn {
                    width: 2.8125rem;
                    height: 2.8125rem;
                    border-radius: .5rem;
                    border: .0625rem solid #e0e0e0;
                    background: #fff;
                    color: #f44336;
                    font-size: .75rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.05);
                    &:hover {
                        background: #ffebee;
                        border-color: #f44336;
                        box-shadow: 0 .1875rem .375rem rgba(244, 67, 54, 0.2);
                    }
                    &:active {
                        transform: scale(0.95);
                    }
                }
                .ai-btn {
                    width: 2.8125rem;
                    height: 2.8125rem;
                    border-radius: .5rem;
                    border: .0625rem solid #e0e0e0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #fff;
                    font-size: .75rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 .125rem .25rem rgba(102, 126, 234, 0.3);
                    
                    &:hover {
                        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                        border-color: #667eea;
                        box-shadow: 0 .1875rem .375rem rgba(102, 126, 234, 0.4);
                        transform: translateY(-0.125rem);
                    }
                    
                    &:active {
                        transform: translateY(0) scale(0.95);
                    }
                    
                    // 加载状态：变灰且不可点击
                    &.loading {
                        background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
                        cursor: not-allowed;
                        opacity: 0.6;
                        transform: none;
                        box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.1);
                        
                        &:hover {
                            background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
                            border-color: #e0e0e0;
                            box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.1);
                            transform: none;
                        }
                        
                        &:active {
                            transform: none;
                        }
                    }
                }
                button {
                    width: 2.8125rem;
                    height: 2.8125rem;
                    border-radius: .5rem;
                    border: .0625rem solid #e0e0e0;
                    background: #fff;
                    color: #333;
                    font-size: .75rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.05);
                    &:hover {
                        background: #f5f5f5;
                        border-color: #d0d0d0;
                        box-shadow: 0 .1875rem .375rem rgba(0, 0, 0, 0.1);
                    }
                    &:active {
                        transform: scale(0.95);
                    }
                }
                .radio-button {
                    width: 2.8125rem;
                    height: 2.8125rem;
                    border-radius: .5rem;
                    border: .0625rem solid #e0e0e0;
                    background: #fff;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 .125rem .25rem rgba(0, 0, 0, 0.05);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    &:hover {
                        background: #f5f5f5;
                        border-color: #d0d0d0;
                        box-shadow: 0 .1875rem .375rem rgba(0, 0, 0, 0.1);
                    }
                    input {
                        position: absolute;
                        opacity: 0;
                        cursor: pointer;
                        width: 100%;
                        height: 100%;
                        &:checked + .radio-mark {
                            background: #3b82f6;
                            &::after {
                                content: '✓';
                                color: #fff;
                                font-size: 1.125rem;
                                font-weight: bold;
                            }
                        }
                    }
                    .radio-mark {
                        width: 100%;
                        height: 100%;
                        border-radius: .5rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: all 0.2s ease;
                    }
                }
            }
        }
        
        li:first-child {
            border-radius: .625rem .625rem 0rem 0rem;
        }
    }
}
</style>