<template>
  <div
    ref="atomRef"
    class="atom"
    :data-row="Row"
    :data-col="Column"
    :style="[{
      width: `var(--col-width-${Column}, 73px)`, 
      height: `var(--row-height-${Row}, 19px)` 
    }, cellStyle]"
    @mouseenter="onMouseEnter"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
  >
    <div class="content">
      {{ cellValue }}
    </div>
  </div>
</template>
<script lang="ts">
/**
 * Cell 组件 - 单元格组件
 */
import { defineComponent, ref, computed, nextTick, watch } from 'vue';
import { useMaskStore } from '@/stores/store/SelectionStore';
import { useDataCellStore } from '@/stores/store/CellDataStore';
import MaskPos from '@/utils/util/SelectionPosition';

export default defineComponent({
  name: 'Cell',
  // 接收自己是哪一行哪一列的单元格
  props: {
    Row: { type: Number, required: true },
    Column: { type: Number, required: true }
  },
  setup(props) {
  
    const atomRef = ref<HTMLElement | null>(null);
    const maskStore = useMaskStore();
    const dataStore = useDataCellStore();

    const cellValue = computed(() => dataStore.getCellValue(props.Row, props.Column));
    const cellStyle = computed(() => {
      const styleStr = dataStore.getCellStyle(props.Row, props.Column);
      if (!styleStr) return {};
      const styleObj: Record<string, string> = {};
      styleStr.split(';').forEach(style => {
        const parts = style.split(':');
        if (parts.length === 2) {
          styleObj[parts[0].trim()] = parts[1].trim();
        }
      });
      return styleObj;
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
      // maskStore.copiedX = false;
      maskStore.copiedCopy = false;
      maskStore.isMouseDown = true;
      // 这个是取消选中状态，避免重复选中。当用户不点击编辑单元格时，才会取消选中
      // 为什么不选择!isEditing.value呢？是因为这样每个不编辑的单元格都要重新赋值，导致性能问题
      if (maskStore.editRow !== -1) {
        maskStore.editRow = -1;
        maskStore.editCol = -1;
      }
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

    return {
      atomRef,
      onMouseEnter,
      onMouseDown,
      onMouseUp,
      cellValue,
      cellStyle
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
  user-select: text;
}

</style>
