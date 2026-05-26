<template>
  <div
    class="column"
    :style="{ width: `var(--col-width-${index}, 73px)` }"
    @contextmenu.prevent="onContextMenu"
    @mousedown="onSelectCol"
    :class="{ 'selected-header': isSelected }"
  >
    <div class="header-content">
      {{ header_logo }}
    </div>
    <div class="tug-container">
      <Tug @mousedown="onResizeStart" />
    </div>
  </div>
</template>
<script lang="ts">
import { defineComponent, computed } from 'vue';
import Tug from './Tug.vue';
import { useCounterStore } from '@/stores/RowColumn';
import { useMaskStore } from '@/stores/MaskStore';
import { startColumnResize } from '@/utils/resizeTool';

export default defineComponent({
  name: 'Column',
  components: { Tug },
  props: {
    header_logo: { type: String, required: true },
    index: { type: Number, required: true }
  },
  emits: ['header-contextmenu'],
  setup(props, { emit }) {
    const store = useCounterStore();
    const maskStore = useMaskStore();


    // 列宽拖动更新宽度
    const onResizeStart = (e: MouseEvent) => {
      e.stopPropagation();
      // 先获取当前列的宽度
      const currentWidth = store.getColWidth(props.index);
      // 开始拖动更新宽度
      // 当用户松开鼠标时，会调用 stopResize 函数，取消当前的动画帧
      startColumnResize(e, currentWidth, (newWidth) => {
        store.setColWidth(props.index, newWidth, false);
      });
    };

    // 右键菜单
    const onContextMenu = (e: MouseEvent) => {
      emit('header-contextmenu', { index: props.index, x: e.clientX, y: e.clientY, nativeEvent: e });
    };

    // ctrl 是多选
    // shift 是范围选
    const onSelectCol = (e: MouseEvent) => {
     
      
      if (e.shiftKey) e.preventDefault(); 
      // 检查是否按下了 Ctrl 或 Meta 键（Mac）
      const isCtrl = e.ctrlKey || e.metaKey;
      // 检查是否按下了 Shift 键
      const isShift = e.shiftKey;

      // copiedCols 和 copiedRows 整行和整列的复制操作
      maskStore.copiedCols = false;
      maskStore.copiedRows = false;
      // 标记是否处于"剪切/粘贴"模式
      maskStore.copiedX = false;
      // 标记是否处于"复制"模式
      maskStore.copiedCopy = false;
      // 清空选中的行，解决互斥问题
      maskStore.selectedRows = new Set();
      maskStore.selStartRow = -1;
      maskStore.selEndRow = -1;
      maskStore.selStartCol = -1;
      maskStore.selEndCol = -1;

      if (isShift) {
        // 锚点
        const anchor = maskStore.selStartCol > 0 ? maskStore.selStartCol : props.index;
        const start = Math.min(anchor, props.index);
        const end = Math.max(anchor, props.index);

        const newSet = new Set<number>();
        for (let i = start; i <= end; i++) {
          newSet.add(i);
        }
        maskStore.selectedCols = newSet;
        maskStore.isShow = true;
      } else if (isCtrl) {
        // 先获取当前选中的列索引
        const newSet = new Set(maskStore.selectedCols);
        // 当你点击的时候有当前列就删除，没有就添加
        if (newSet.has(props.index)) {
          newSet.delete(props.index);
        } else {
          newSet.add(props.index);
        }
        maskStore.selectedCols = newSet;
        maskStore.isShow = true; 
        
      } else {
        
        const newSet = new Set<number>();
        newSet.add(props.index);
        maskStore.selectedCols = newSet;
        
        // 这几行是给复制截切准备的
        maskStore.selStartRow = 1;
        maskStore.selEndRow = store.MAX_ROWS;
        maskStore.selStartCol = props.index;
        maskStore.selEndCol = props.index;

        maskStore.isShow = true;
      }
    };

    const isSelected = computed(() => {
      // 如果遮罩不显示，直接返回 false
      if (!maskStore.isShow) return false;
      
      // 检查多列选择模式
      if (maskStore.selectedCols.size > 0) {
        return maskStore.selectedCols.has(props.index);
      }

      // 单范围选择模式
      const c1 = Math.min(maskStore.selStartCol, maskStore.selEndCol);
      const c2 = Math.max(maskStore.selStartCol, maskStore.selEndCol);
      const isWholeHeight = (maskStore.selStartRow === 1 && maskStore.selEndRow === store.MAX_ROWS);

      return props.index >= c1 && props.index <= c2 && isWholeHeight;
    });

    return { onResizeStart, onContextMenu, onSelectCol, isSelected };
  }
});
</script>
<style scoped>
.column {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 19px;
  border-right: 1px solid #ccc;
  border-bottom: 1px solid #ccc;
  background-color: #f3f4f6;
  position: relative;
  box-sizing: border-box;
  user-select: none;
}
.column:hover {
  background-color: #e5e7eb;
  cursor: pointer;
}
.selected-header {
  background-color: #d1d5db;
  color: #000;
  font-weight: bold;
}
.header-content {
  flex-grow: 1;
  text-align: center;
  font-size: 12px;
  color: #666;
}
.tug-container {
  width: 5px;
  height: 100%;
  cursor: col-resize;
  position: absolute;
  right: 0;
  top: 0;
  z-index: 10;
}
</style>