<template>
  <div v-if="visible" class="context-menu" :style="{ left: x + 'px', top: y + 'px' }" >
    <div class="menu-item" @click="emitAction('delete')">删除</div>
    <div v-if="selStartCol !== 1" class="separator"></div>
    <div v-if="selStartCol !== 1" class="menu-item" @click="emitAction('sort-asc')">升序</div>
    <div v-if="selStartCol !== 1" class="menu-item" @click="emitAction('sort-desc')">降序</div>
  </div>
  <!-- 这个用于监视点击外部关闭菜单的事件 -->
  <div v-if="visible" class="overlay" @click="$emit('close')"></div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { storeToRefs } from 'pinia';
import { useMaskStore } from '@/stores/MaskStore';
export default defineComponent({
  name: 'ContextMenu',
  props: {
    visible: { type: Boolean, required: true },
    x: { type: Number, required: true },
    y: { type: Number, required: true }
  },
  emits: ['close', 'action'],
  setup(props, { emit }) {
    const { selStartCol } = storeToRefs(useMaskStore());
    const emitAction = (action: string) => {
      emit('action', action);
      emit('close');
    };
    return { emitAction, selStartCol };
  }
});
</script>
<style scoped>
.context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #ccc;
  box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
  border-radius: 4px;
  padding: 5px 0;
  min-width: 150px;
}
.menu-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}
.menu-item:hover {
  background-color: #f3f4f6;
}
.separator {
  height: 1px;
  background-color: #eee;
  margin: 4px 0;
}
.overlay {
  position: fixed;
  top: 24px;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9998;
  background: transparent;
}
</style>
