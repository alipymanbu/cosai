<template>
  <div ref="maskRef" v-if="isShow && !hasMultiSelection" class="mask" :style="maskStyle"></div>
  
  <template v-if="isShow && hasMultiColSelection">
    <div
      v-for="col in sortedSelectedCols" 
      :key="col" dsa
      :class="{'mask':true, 'multi-mask' : true, 'multi-mask-copy': copiedCols}" 
      :style="getColStyle(col)"
    ></div>
    
  </template>

  <template v-if="isShow && hasMultiRowSelection">
    <div
      v-for="row in sortedSelectedRows" 
      :key="row" 
      :class="{'mask':true, 'multi-mask' : true, 'multi-mask-copy': copiedRows}" 
      :style="getRowStyle(row)"
    ></div>
  </template>
</template>

<script lang="ts">
import { defineComponent, computed, ref, watch, nextTick } from 'vue';
import { useMaskStore } from '@/stores/MaskStore';
import { useCounterStore } from '@/stores/RowColumn';
import { storeToRefs } from 'pinia';

export default defineComponent({
  name: 'Mask',
  setup() {
    const maskRef = ref<HTMLDivElement>();
    const maskStore = useMaskStore();
    const rowColumnStore = useCounterStore();
    const { isShow, selStartRow, selStartCol, selEndRow, selEndCol, selectedCols, copiedCols, selectedRows, copiedRows } = storeToRefs(maskStore);
    
    // 监听影响遮罩位置的坐标变化

    watch([() => maskStore.moveAtom], async() => {
 
      
      if (maskRef.value) {
        await nextTick();
        const rect = maskRef.value.getBoundingClientRect();
        maskStore.absPos_x = rect.x;
        maskStore.absPos_y = rect.y; 
        maskStore.scrollMoveAtom = maskStore.scrollMoveAtom + 1;
        
      }
    });
    const hasMultiColSelection = computed(() => {
      return selectedCols.value.size > 0 && !maskStore.copiedCopy;
    });

    const hasMultiRowSelection = computed(() => {
      return selectedRows.value.size > 0 && !maskStore.copiedCopy;
    });

    const hasMultiSelection = computed(() => {
      return hasMultiColSelection.value || hasMultiRowSelection.value;
    });

    const sortedSelectedCols = computed(() => {
      return Array.from(selectedCols.value).sort((a, b) => a - b);
    });

    const sortedSelectedRows = computed(() => {
      return Array.from(selectedRows.value).sort((a, b) => a - b);
    });

    const maskStyle = computed(() => {
      if (selStartRow.value < 0 || selStartCol.value < 0) {
        return { display: 'none' };
      }
      const rect = rowColumnStore.getRect(
        selStartRow.value,
        selStartCol.value,
        selEndRow.value,
        selEndCol.value
      );

      return {
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`
      };
    });

    const getColStyle = (colIndex: number) => {
      if(maskStore.selectedCols.size > 0 && maskStore.copiedX) {
        const rect = rowColumnStore.getRect(
          1,
          colIndex,
          1,
          colIndex
        );
        return {
          left: `${rect.left}px`,
          top: `${rect.top}px`,
          width: `${rect.width}px`,
          height: `${rect.height}px`,
          border: 'none',
          boxSizing: 'border-box',
          zIndex: 5
         };
      }
      const rect = rowColumnStore.getRect(
        1,
        colIndex,
        rowColumnStore.MAX_ROWS,
        colIndex
      );

      return {
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        border: 'none',
        boxSizing: 'border-box',
        zIndex: 5
      };
    };

    const getRowStyle = (rowIndex: number) => {
      if(maskStore.selectedRows.size > 0 && maskStore.copiedX){
        const rect = rowColumnStore.getRect(
          rowIndex,
          1,
          rowIndex,
          1
        );
        return {
          left: `${rect.left}px`,
          top: `${rect.top}px`,
          width: `${rect.width}px`,
          height: `${rect.height}px`,
          border: 'none',
          boxSizing: 'border-box',
          zIndex: 5
        };
      }
      const rect = rowColumnStore.getRect(
        rowIndex,
        1,
        rowIndex,
        rowColumnStore.MAX_COLS
      );

      return {
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        border: 'none',
        boxSizing: 'border-box',
        zIndex: 5
      };
    };

    return { 
      isShow, maskStyle, 
      hasMultiSelection, hasMultiColSelection, hasMultiRowSelection,
      sortedSelectedCols, sortedSelectedRows,
      getColStyle, getRowStyle,
      copiedCols, copiedRows,
      maskRef
    };
  }
});
</script>

<style scoped>
.mask {
  position: absolute;
  background-color: rgba(14, 165, 233, 0.2);
  border: 2px solid rgb(14, 165, 233);
  pointer-events: none;
  z-index: 5;
  box-sizing: border-box;
}
.multi-mask {
  background-color: rgba(14, 165, 233, 0.2);
  border: none;
  pointer-events: none;
  z-index: 5;
  box-sizing: border-box;
}
.multi-mask-copy {
  background-color: #10b9813f
}
</style>
