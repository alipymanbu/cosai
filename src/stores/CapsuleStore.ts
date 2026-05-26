import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CapsuleItem {
  id: number
  name: string
  componentName: string
}

export const useCapsuleStore = defineStore('capsule', () => {
  // 当前选中的组件 ID
  const selectedId = ref<string>('1')
  
  // 选中的组件名称
  const selectedComponentName = computed(() => {
    // 这里可以后续添加从 items 中查找的逻辑
    return ''
  })
  
  // 设置选中的组件 ID
  function setSelectedId(id: string) {
    selectedId.value = id
    // 同步保存到 localStorage
    localStorage.setItem('capsule_selected_id', id)
    console.log('📦 CapsuleStore: 已设置选中 ID:', id)
  }
  
  // 从 localStorage 恢复选中的 ID
  function restoreFromStorage() {
    const savedId = localStorage.getItem('capsule_selected_id')
    if (savedId) {
      selectedId.value = savedId
      console.log('📦 CapsuleStore: 从 localStorage 恢复选中 ID:', savedId)
    }
  }
  
  return {
    selectedId,
    selectedComponentName,
    setSelectedId,
    restoreFromStorage
  }
})
