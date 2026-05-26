<template>
  <div
    ref="atomRef"
    class="atom"
    :class="{ 'diff-cell-highlight': isDiffCell }"
    :data-row="Row"
    :data-col="Column"
    :style="{ width: `var(--col-width-${Column}, 73px)`, height: `var(--row-height-${Row}, 19px)` }"
    @mouseenter="onMouseEnter"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @dblclick="onDoubleClick"
  >
    <div v-if="!isEditing" class="content">
      {{ cellValue }}
    </div>
    <input
      v-else
      ref="inputRef"
      class="editor"
      v-model="inputValue"
      @blur="onBlur"
    />
  </div>
</template>
<script lang="ts">
/**
 * Atom 组件 - 单元格组件
 */
import { defineComponent, ref, computed, nextTick, watch } from 'vue';
import { useMaskStore } from '@/stores/MaskStore';
import { useDataStore } from '@/stores/DataStore';
import MaskPos from '@/utils/MaskPos';

export default defineComponent({
  name: 'Atom',
  // 接收自己是哪一行哪一列的单元格
  props: {
    Row: { type: Number, required: true },
    Column: { type: Number, required: true }
  },
  setup(props) {
  
    const atomRef = ref<HTMLElement | null>(null);
    const inputRef = ref<HTMLInputElement | null>(null);
    const maskStore = useMaskStore();
    const dataStore = useDataStore();
    const inputValue = ref('');

    const cellValue = computed(() => {
      // 检查是否是公式栏正在编辑的单元格
      if (maskStore.isFormulaEditing && 
          maskStore.formulaEditRow === props.Row && 
          maskStore.formulaEditCol === props.Column && 
          maskStore.initialInput !== null) {
        return maskStore.initialInput;
      }
      // 检查是否是单元格编辑模式
      if (maskStore.editRow === props.Row && 
          maskStore.editCol === props.Column && 
          maskStore.initialInput !== null) {
        return maskStore.initialInput;
      }
      return dataStore.getCellValue(props.Row, props.Column);
    });
    const isEditing = computed(() => maskStore.editRow === props.Row && maskStore.editCol === props.Column);

    watch(isEditing, (newVal, oldVal) => {
      if (newVal) {
        if (maskStore.initialInput !== null) {
          inputValue.value = maskStore.initialInput;
        } else {
          inputValue.value = cellValue.value;
        }
        nextTick(() => {
          if (inputRef.value) {
            inputRef.value.focus();
          }
        });
      } else if (oldVal) {
        maskStore.initialInput = null;
      }
    });

    watch(inputValue, (newVal) => {
      maskStore.initialInput = newVal;
    });

    // 快速编辑
    watch(() => maskStore.initialInput, (newVal) => {
      if (isEditing.value && newVal !== null) {
        inputValue.value = newVal;
      }
    });

    // 鼠标点击不放进入单元格时会调用，记入鼠标位置，来进行遮罩的绘制
    const onMouseEnter = () => {
      // atomRef.value 确保 DOM 元素存在，避免空指针错误
      if (atomRef.value && maskStore.isMouseDown) {
        // const el = atomRef.value;
        // maskStore.pos_x = el.offsetLeft;
        // maskStore.pos_y = el.offsetTop;
        // maskStore.pos_width = el.offsetWidth;
        // maskStore.pos_height = el.offsetHeight;
        maskStore.col = props.Column;
        maskStore.row = props.Row;
      }
    };

    const onMouseDown = (e: MouseEvent) => {
      if (maskStore.editRow !== -1 && (maskStore.editRow !== props.Row || maskStore.editCol !== props.Column)) {
        const prevRow = maskStore.editRow;
        const prevCol = maskStore.editCol;
        const prevValue = maskStore.initialInput ?? dataStore.getCellValue(prevRow, prevCol);
        dataStore.setCellValue(prevRow, prevCol, prevValue, false, true, true);
        maskStore.editRow = -1;
        maskStore.editCol = -1;
      }
      maskStore.copiedCopy = false;
      maskStore.isMouseDown = true;
      maskStore.selectedCols = new Set();
      maskStore.selectedRows = new Set();
      maskStore.copiedCols = false;
      maskStore.copiedRows = false;
      if (atomRef.value) {
        MaskPos(e, props.Row, props.Column);
      }
    };

    const onMouseUp = () => {
      maskStore.isMouseDown = false;
    };

    const onDoubleClick = () => {
      // 预览模式下禁止编辑
      if (maskStore.isPreviewMode) {
        return;
      }
      maskStore.editRow = props.Row;
      maskStore.editCol = props.Column;
      maskStore.copiedStartRow = -1;
      maskStore.copiedStartCol = -1;
      maskStore.copiedEndRow = -1;
      maskStore.copiedEndCol = -1;
      maskStore.copiedCols = false;
      maskStore.copiedRows = false;
      navigator.clipboard.writeText('');
    };

    const onBlur = () => {
    };

    const isDiffCell = computed(() => {
      return dataStore.highlightedDiffCells.includes(`${props.Row}-${props.Column}`);
    });

    return {
      atomRef,
      inputRef,
      onMouseEnter,
      onMouseDown,
      onDoubleClick,
      isEditing,
      inputValue,
      onBlur,
      onMouseUp,
      cellValue,
      isDiffCell,
    };
  }
});
</script>
<style scoped>
.atom {
  border-right: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  box-sizing: border-box;
  background-color: white;
  overflow: hidden;
}
.content {
  padding: 0 4px;
  width: 100%;
  height: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: inherit;
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #000;
  user-select: none;
}
.editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: 2px solid #10b981;
  padding: 0 4px;
  font-size: 13px;
  box-sizing: border-box;
  background-color: white;
  z-index: 20;
  position: relative;
  display: block;
}
.diff-cell-highlight {
  background-color: #93c5fd !important;
}
</style>
