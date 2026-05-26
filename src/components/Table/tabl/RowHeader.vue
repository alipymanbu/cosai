<template>
  <div
    class="row-header"
    :style="{ height: `var(--row-height-${index}, 19px)` }"
    @mousedown="onSelectRow"
    @contextmenu.prevent="onContextMenu"
    :class="{ 'selected-header': isSelected }"
  >
    <div class="header-content">
      {{ index }}
    </div>

  </div>
</template>
<script lang="ts">
import { defineComponent, computed } from 'vue';
import { useCounterStore } from '@/stores/store/GridStore';
import { useMaskStore } from '@/stores/store/SelectionStore';


export default defineComponent({
  name: 'RowHeader',
  components: {},
  props: {
    index: {
      type: Number,
      required: true
    }
  },
  emits: ['row-contextmenu'],
  setup(props, { emit }) {
    const store = useCounterStore();
    const maskStore = useMaskStore();
  

    const onSelectRow = (e: MouseEvent) => {
      if (e.shiftKey) e.preventDefault();
 
      const isCtrl = e.ctrlKey || e.metaKey;
      const isShift = e.shiftKey;

      maskStore.copiedRows = false;
      maskStore.copiedCols = false;
      maskStore.copiedX = false;
      maskStore.copiedCopy = false;
      maskStore.selStartRow = -1;
      maskStore.selEndRow = -1;
      maskStore.selStartCol = -1;
      maskStore.selEndCol = -1;
      maskStore.selectedCols = new Set();
      
      if (isShift) {
        const anchor = maskStore.selStartRow > 0 ? maskStore.selStartRow : props.index;
        const start = Math.min(anchor, props.index);
        const end = Math.max(anchor, props.index);

        const newSet = new Set<number>();
        for (let i = start; i <= end; i++) {
          newSet.add(i);
        }
        maskStore.selectedRows = newSet;
        maskStore.isShow = true;
        
      } else if (isCtrl) {
        const newSet = new Set(maskStore.selectedRows);
        if (newSet.has(props.index)) {
          newSet.delete(props.index);
        } else {
          newSet.add(props.index);
        }
        maskStore.selectedRows = newSet; 
        maskStore.isShow = true;
      } else {
 
         const newSet = new Set<number>();
         newSet.add(props.index);
         maskStore.selectedRows = newSet;

         maskStore.selStartRow = props.index;
         maskStore.selEndRow = props.index;
         maskStore.selStartCol = 1;
         maskStore.selEndCol = store.MAX_COLS;
         maskStore.isShow = true;
      }
    };

    const onContextMenu = (e: MouseEvent) => {
      emit('row-contextmenu', { index: props.index, x: e.clientX, y: e.clientY, nativeEvent: e });
    };

    const isSelected = computed(() => {
      if (!maskStore.isShow) return false;

      if (maskStore.selectedRows.size > 0) {
        return maskStore.selectedRows.has(props.index);
      }
      
      const r1 = Math.min(maskStore.selStartRow, maskStore.selEndRow);
      const r2 = Math.max(maskStore.selStartRow, maskStore.selEndRow);

      const isWholeWidth = (maskStore.selStartCol === 1 && maskStore.selEndCol === store.MAX_COLS);
      
      return props.index >= r1 && props.index <= r2 && isWholeWidth;
    });

    return { onSelectRow, isSelected, onContextMenu };
  }
});
</script>
<style scoped>
.row-header {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 44px;
  border-bottom: 1px solid #ccc;
  border-right: 1px solid #ccc;
  background-color: #f3f4f6;
  position: relative;
  box-sizing: border-box;
  user-select: none;
}
.row-header:hover {
  background-color: #e5e7eb;
  cursor: pointer;
}
.selected-header {
  background-color: #d1d5db;
  color: #000;
  font-weight: bold;
}
.header-content {
  font-size: 12px;
  color: #666;
}
</style>
