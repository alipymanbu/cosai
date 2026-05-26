<template>
  <div v-if="isVisible" :class="{'copy-mask': true, }" :style="maskStyle"></div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import { useMaskStore } from '@/stores/MaskStore';
import { useCounterStore } from '@/stores/RowColumn';
import { storeToRefs } from 'pinia';

export default defineComponent({
  name: 'CopyMask',
  setup() {
    const maskStore = useMaskStore();
    const rowColumnStore = useCounterStore();
    const { copiedStartRow, copiedStartCol, copiedEndRow, copiedEndCol } = storeToRefs(maskStore);

    const isVisible = computed(() => {
      return copiedStartRow.value >= 0 && copiedStartCol.value >= 0;
    });

    const maskStyle = computed(() => {
      if (!isVisible.value) {
        return { display: 'none' };
      }
      const rect = rowColumnStore.getRect(
        copiedStartRow.value,
        copiedStartCol.value,
        copiedEndRow.value,
        copiedEndCol.value
      );
      return {
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`
      };
    });

    return { isVisible, maskStyle };
  }
});
</script>

<style scoped>
.copy-mask {
  position: absolute;
  pointer-events: none;
  z-index: 6;
  box-sizing: border-box;
  border: 2px dashed #10b981;
  animation: ants 1s linear infinite;
}


@keyframes ants {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>
