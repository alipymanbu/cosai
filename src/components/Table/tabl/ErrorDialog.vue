<template>
  <div v-if="isVisible">
    <div class="overlay"></div>
    <div class="excel-dialog">
      <div class="dialog-header">
        <span class="dialog-title">erro</span>
        <button class="close-btn" @click="closeDialog">×</button>
      </div>
      <div class="dialog-body">
        <div class="warning-icon">⚠️</div>
        <div class="message">
          无法在此处粘贴此内容，因为 复制 区域和粘贴区域的大小不同。<br>
          请选择粘贴区域中的一个单元格，或是相同大小的区域，然后再次尝试粘贴。
        </div>
      </div>
      <div class="dialog-footer">
        <button class="confirm-btn" @click="closeDialog">确定(O)</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useMaskStore } from '@/stores/store/SelectionStore';
import { storeToRefs } from 'pinia';

export default defineComponent({
  setup() {
    const maskStore = useMaskStore();
    const { error: isVisible } = storeToRefs(maskStore);
    
    const closeDialog = () => {
      maskStore.error = false;
    };
    
    return {
      isVisible,
      closeDialog
    }
  }
})
// 控制弹窗显示状态

</script>

<style scoped>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.excel-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 400px;
  background-color: #666;
  color: #fff;
  border: 1px solid #333;
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  z-index: 1000;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #444;
  background-color: #555;
}

.dialog-title {
  font-weight: bold;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  width: 24px;
  height: 24px;
  text-align: center;
  line-height: 24px;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background-color: #777;
}

.dialog-body {
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.warning-icon {
  font-size: 24px;
  min-width: 24px;
  text-align: center;
}

.message {
  line-height: 1.5;
  font-size: 14px;
  white-space: pre-line;
}

.dialog-footer {
  padding: 10px 15px;
  text-align: right;
  border-top: 1px solid #444;
  background-color: #555;
}

.confirm-btn {
  background-color: #008000;
  color: white;
  border: none;
  padding: 6px 15px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.confirm-btn:hover {
  background-color: #00a000;
}
</style>
