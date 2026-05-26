<template>
  <div class="app-wrapper">
    <div class="main-content" ref="maincontent">
      <div class="app-container" :style="gridStyles">

        <!-- Toolbar -->
        <div class="toolbar">
          <div class="tool-group">
            <button class="tool-btn" @click="handleUndo" title="撤销 (Ctrl+Z)" :disabled="!canUndo">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/></svg>
            </button>
            <button class="tool-btn" @click="handleRedo" title="重做 (Ctrl+Y)" :disabled="!canRedo">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.4 10.6C16.55 9 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.95 0 3.73.72 5.12 1.88L13 16h9V7l-3.6 3.6z"/></svg>
            </button>
          </div>
          <div class="tool-group">
            <button class="tool-btn" @click="showAI" title="显示 AI 助手" v-if="!aiStore.isVisible">
              <img src="/ai.png" alt="AI 助手" width="16" height="16" />
            </button>
          </div>
          <div class="tool-divider"></div>
          <div class="fx-bar">
             <div class="address-box">{{ currentAddress }}</div>
             <input 
                class="formula-bar" 
                v-model="formulaVal" 
                @input="onFormulaInput"
                @focus="onFormulaFocus" 
                @blur="onFormulaBlur"
                @compositionend="onCompositionEnd"
                readonly
             />
          </div>
        </div>

        <!-- Notification Bar -->
        

        <div class="scroller" @mousedown="onScrollerMouseDown" tabindex="0">
          <!-- Header Row -->
          <div class="header-row">
            <!-- Top Left Corner (Fixed) -->
            <div class="corner" @click="onSelectAll"></div>

            <!-- Column Headers -->
            <Column v-for="i in colCount" :key="i" :index="i" :header_logo="getColLabel(i - 1)"
              @header-contextmenu="onHeaderContextMenu" />
          </div>

          <!-- Data Rows -->
          <div v-for="r in rowCount" :key="r" class="data-row">
            <!-- Row Header -->
            <Row :index="r" class="sticky-left" @row-contextmenu="onRowContextMenu" />

            <!-- Atoms -->
            <Atom v-for="c in colCount" :key="c" :Row="r" :Column="c" />
          </div>

          <Mask ref="maskRef" />
          <CopyMask />
          <Error />
        </div>

        <ContextMenu :visible="menuVisible" :x="menuX" :y="menuY" @close="closeMenu" @action="handleMenuAction" />
      </div>
      <div class="ai-container" v-if="aiStore.isVisible">
        <Ai />
      </div>
    </div>
  </div>
  <div class="domMask" :style="{ width: domMaskWidth, height: domMaskHeight, top: domMaskTop, display: 'none'}"></div>
</template>
<script lang="ts">
import { defineComponent, computed, ref, onMounted, onUnmounted, nextTick , watch, shallowRef} from 'vue';
import Column from '@/components/Table/tabl/ColumnHeader.vue';
import Row from '@/components/Table/tabl/RowHeader.vue';
import Atom from '@/components/Table/tabl/Cell.vue';
import Error from '@/components/Table/tabl/ErrorDialog.vue';
import Ai from '@/components/Table/tabl/Assistant.vue';
import Mask from '@/components/Table/tabl/SelectionOverlay.vue';
import CopyMask from '@/components/Table/tabl/CopyOverlay.vue';
import ContextMenu from '@/components/Table/tabl/TableContextMenu.vue';
import { useCounterStore } from '@/stores/store/GridStore';
import { useMaskStore } from '@/stores/store/SelectionStore';
import { useDataCellStore } from '@/stores/store/CellDataStore';
import { useAiStore } from '@/stores/store/AssistantStore'; 
import onScrollerMouseDown from '@/utils/util/handleScrollerClick';

export default defineComponent({
  name: 'Spreadsheet',
  components: { Column, Row, Atom, Ai, Mask, CopyMask, ContextMenu, Error },
  setup() {
    const store = useCounterStore();
    const maskStore = useMaskStore();
    const dataStore = useDataCellStore();
    const aiStore = useAiStore();

    const colCount = computed(() => store.MAX_COLS);;
    const rowCount = computed(() => store.MAX_ROWS);

    const maincontent = ref(null);
    
    const domMaskWidth = computed(() => (document.documentElement.clientWidth - maskStore.aiInput) + 'px');
    const domMaskTop = computed(() => 9 + 'px');
    const domMaskHeight = computed(() => (document.documentElement.clientHeight) + 'px');
    if (maskStore.aiInput === 0) {
      maskStore.aiInput = 350;
    }

  
    const menuVisible = ref(false);
    const menuX = ref(0);
    const menuY = ref(0);
    const menuTargetCol = ref(-1);
    const menuTargetRow = ref(-1);

    const maskRef = ref(null);

    const isFormulaFocus = ref(false);
    const hasSavedForFormula = ref(false);
    const formulaVal = ref('');

    const currentVal = computed(() => {
        if (maskStore.selStartRow <= 0 || maskStore.selStartCol <= 0) return '';
        return dataStore.getCellValue(maskStore.selStartRow, maskStore.selStartCol);
    });

    // 监听选择变化，确保 formula-bar 内容更新
    watch([() => maskStore.selStartRow, () => maskStore.selStartCol], () => {
      // 延迟一下，确保焦点状态已经更新
      setTimeout(() => {
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        
        if (!isFormulaBarFocused) {
          formulaVal.value = currentVal.value;
        }
      }, 0);
    });

    watch(currentVal, (newVal) => {
      if (!isFormulaFocus.value) {
        formulaVal.value = newVal;
      }
    }, { immediate: true });

    // Also watch selection to reset formula focus state if needed, though blur usually handles it.
    // If we change selection via keyboard while focused in formula bar? 
    // Usually focusing formula bar traps focus until Enter or Tab or Click away.
    // For now, let's keep it simple.

    const onFormulaFocus = () => {
      formulaVal.value = currentVal.value;
      isFormulaFocus.value = true;
      hasSavedForFormula.value = false;
    };

    const onFormulaBlur = () => {
      isFormulaFocus.value = false;
      hasSavedForFormula.value = false;
    };

    const onCompositionEnd = () => {
      if (maskStore.selStartRow > 0 && maskStore.selStartCol > 0) {
        if (!hasSavedForFormula.value) {
          dataStore.saveState();
          hasSavedForFormula.value = true;
        }
        dataStore.setCellValue(maskStore.selStartRow, maskStore.selStartCol, formulaVal.value, false, false, false);
      }
    };

    const onFormulaInput = () => {
      if (maskStore.selStartRow > 0 && maskStore.selStartCol > 0) {
        if (!hasSavedForFormula.value) {
          dataStore.saveState();
          hasSavedForFormula.value = true;
        }
        dataStore.setCellValue(maskStore.selStartRow, maskStore.selStartCol, formulaVal.value, false, false, false);
      }
    };

    watch([() => maskStore.scrollMoveAtom], async () => {

      
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const scroller = document.querySelector('.scroller') as HTMLElement;

     
      
      if((maskStore.absPos_x + store.getColWidth(maskStore.selStartCol) > Math.floor((viewportWidth - 44) / 73) * 73 + 44)) {
        scroller.scrollLeft = scroller.scrollLeft + store.getColWidth(maskStore.selStartCol);
      } 
      else if((maskStore.absPos_y + store.getRowHeight(maskStore.selStartRow) >= Math.floor((viewportHeight - 24) / 19) * 19 + 24)) {
        scroller.scrollTop = scroller.scrollTop + store.getRowHeight(maskStore.selStartRow);
      } else if((maskStore.absPos_x + store.getColWidth(maskStore.selStartCol) < 44 + store.getColWidth(maskStore.selStartCol))){
        scroller.scrollLeft = scroller.scrollLeft - store.getColWidth(maskStore.selStartCol);
      } else if((maskStore.absPos_y + store.getRowHeight(maskStore.selStartRow) < 24 + store.getRowHeight(maskStore.selStartRow))){
        scroller.scrollTop = scroller.scrollTop - store.getRowHeight(maskStore.selStartRow);
      }
      

    })

    const onHeaderContextMenu = async (payload: { index: number, x: number, y: number, nativeEvent: MouseEvent }) => {
      // Clear multi-selection for simplicity on right click (force single col selection)
      maskStore.selectedCols = new Set();
      maskStore.selectedRows = new Set();

      maskStore.selStartRow = 1;
      maskStore.selEndRow = store.MAX_ROWS;
      maskStore.selStartCol = payload.index;
      maskStore.selEndCol = payload.index;
      maskStore.isShow = true;

      menuX.value = payload.x;
      menuY.value = payload.y;
      menuTargetCol.value = payload.index;
      menuTargetRow.value = -1;
      menuVisible.value = true;
    };

    const onRowContextMenu = async (payload: { index: number, x: number, y: number, nativeEvent: MouseEvent }) => {
      maskStore.selectedCols = new Set();
      maskStore.selectedRows = new Set();

      maskStore.selStartRow = payload.index;
      maskStore.selEndRow = payload.index;
      maskStore.selStartCol = 1;
      maskStore.selEndCol = store.MAX_COLS;
      maskStore.isShow = true;
      
      menuX.value = payload.x;
      menuY.value = payload.y;
      menuTargetCol.value = -1;
      menuTargetRow.value = payload.index;
      menuVisible.value = true;
    };

    const closeMenu = () => {
      menuVisible.value = false;
    };

    const handleMenuAction = async (action: string) => {
      if (action === 'delete') {
        if (menuTargetCol.value !== -1) {
          // Delete Column (Shift Left)
          dataStore.deleteColumn(menuTargetCol.value);
          // Adjust selection (optional, but good UX)
          // maskStore.selStartCol = menuTargetCol.value;
          // maskStore.selEndCol = menuTargetCol.value;
          // console.log(menuTargetCol.value);
          
        } else if (menuTargetRow.value !== -1) {
          // Delete Row (Shift Up)
          dataStore.deleteRow(menuTargetRow.value);
          // Adjust selection
          // maskStore.selStartRow = menuTargetRow.value;
          // maskStore.selEndRow = menuTargetRow.value;
        }
      } else if (action === 'sort-asc') {
        if (menuTargetCol.value !== -1) {
          dataStore.sortRowsByColumn(menuTargetCol.value, true);
        }
      } else if (action === 'sort-desc') {
        if (menuTargetCol.value !== -1) {
          dataStore.sortRowsByColumn(menuTargetCol.value, false);
        }
      }
    };

    const getColLabel = (index: number) => {
      let label = '';
      let i = index;
      while (i >= 0) {
        label = String.fromCharCode(65 + (i % 26)) + label;
        i = Math.floor(i / 26) - 1;
      }
      return label;
    };

    const gridStyles = computed(() => {
      const styles: Record<string, string> = {};
      for (const [key, value] of Object.entries(store.colWidths)) {
        styles[`--col-width-${key}`] = `${value}px`;
      }
      for (const [key, value] of Object.entries(store.rowHeights)) {
        styles[`--row-height-${key}`] = `${value}px`;
      }
      return styles;
    });

    const onSelectAll = () => {
      maskStore.selectedCols = new Set();
      maskStore.selectedRows = new Set();
      maskStore.selStartRow = 1;
      maskStore.selStartCol = 1;
      maskStore.selEndRow = store.MAX_ROWS;
      maskStore.selEndCol = store.MAX_COLS;
      maskStore.isShow = true;
    };

    let isX = false;
    const handleKeyDown = async (e: KeyboardEvent) => {

      if (e.key === 'Tab') {
        e.preventDefault();

        const direction = e.shiftKey ? -1 : 1;
        let nextCol = maskStore.selStartCol + direction;

        if (nextCol < 1) nextCol = 1;
        if (nextCol > store.MAX_COLS) nextCol = store.MAX_COLS;

        maskStore.selStartCol = nextCol;
        maskStore.selEndCol = nextCol;
        // Ensure single cell selection on tab
        maskStore.selEndRow = maskStore.selStartRow;

        maskStore.moveAtom++;
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        onSelectAll();
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        // Handle Multi-Column Selection
        if (maskStore.selectedCols.size > 0) {
          e.preventDefault();

          maskStore.copiedCols = true;
          maskStore.copiedRows = false; // Reset row copy
          maskStore.copiedStartRow = -1;
          maskStore.copiedStartCol = -1;
          maskStore.copiedEndRow = -1;
          maskStore.copiedEndCol = -1;

          const sortedCols = Array.from(maskStore.selectedCols).sort((a, b) => a - b);
          const r1 = 1;
          const r2 = store.MAX_ROWS;

          const rowsData: string[] = [];
          for (let r = r1; r <= r2; r++) {
            const rowVals: string[] = [];
            for (const c of sortedCols) {
              rowVals.push(dataStore.getCellValue(r, c));
            }
            rowsData.push(rowVals.join('\t'));
          }
          const textData = rowsData.join('\n ');

          try {
            await navigator.clipboard.writeText(textData);
            console.log('Copied multi-col to clipboard');
          } catch (err) {
            console.error('Failed to copy multi: ', err);
          }
          return;
        }

        // Handle Multi-Row Selection
        if (maskStore.selectedRows.size > 0) {
          e.preventDefault();
          maskStore.copiedRows = true;
          maskStore.copiedCols = false; // Reset col copy
          
          maskStore.copiedStartRow = -1;
          maskStore.copiedStartCol = -1;
          maskStore.copiedEndRow = -1;
          maskStore.copiedEndCol = -1;

          const sortedRows = Array.from(maskStore.selectedRows).sort((a, b) => a - b);
          const c1 = 1;
          const c2 = store.MAX_COLS;

          const rowsData: string[] = [];
          for (const r of sortedRows) {
            const rowVals: string[] = [];
            for (let c = c1; c <= c2; c++) {
              rowVals.push(dataStore.getCellValue(r, c));
            }
            rowsData.push(rowVals.join('\t'));
          }
          const textData = rowsData.join('\n');
          try {
            await navigator.clipboard.writeText(textData);
            console.log('Copied multi-row to clipboard');
          } catch (err) {
            console.error('Failed to copy multi-row: ', err);
          }
          return;
        }

        // Handle Single Range Selection
        const { selStartRow, selStartCol, selEndRow, selEndCol } = maskStore;
        if (selStartRow >= 0 && selStartCol >= 0) {
          e.preventDefault();
          maskStore.copiedCols = false;
          maskStore.copiedRows = false;

          const r1 = Math.min(selStartRow, selEndRow);
          const c1 = Math.min(selStartCol, selEndCol);
          const r2 = Math.max(selStartRow, selEndRow);
          const c2 = Math.max(selStartCol, selEndCol);

          maskStore.copiedStartRow = r1;
          maskStore.copiedStartCol = c1;
          maskStore.copiedEndRow = r2;
          maskStore.copiedEndCol = c2;

          const rowsData: string[] = [];
          for (let r = r1; r <= r2; r++) {
            const rowVals: string[] = [];
            for (let c = c1; c <= c2; c++) {
              rowVals.push(dataStore.getCellValue(r, c));
            }
            rowsData.push(rowVals.join('\t'));
          }
          const textData = rowsData.join('\n ');

          try {
            await navigator.clipboard.writeText(textData);
            console.log('Copied to clipboard');
          } catch (err) {
            console.error('Failed to copy: ', err);
          }
        }
      }

      // Arrow keys navigation
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        const step = e.shiftKey ? 10 : 1;
        let { selStartRow, selStartCol, selEndRow, selEndCol } = maskStore;

        // If multi-selection, just move to edge
        const isMultiCol = maskStore.selectedCols.size > 0;
        const isMultiRow = maskStore.selectedRows.size > 0;
        const isRange = (selStartRow !== selEndRow) || (selStartCol !== selEndCol);

        if (isMultiCol || isMultiRow || isRange) {
          // For simplicity, move to top-left of selection
          selStartRow = Math.min(selStartRow, selEndRow);
          selStartCol = Math.min(selStartCol, selEndCol);
          selEndRow = selStartRow;
          selEndCol = selStartCol;
          maskStore.selectedCols = new Set();
          maskStore.selectedRows = new Set();
        }

        switch (e.key) {
          case 'ArrowUp':
            selStartRow = Math.max(1, selStartRow - step);
            break;
          case 'ArrowDown':
            selStartRow = Math.min(store.MAX_ROWS, selStartRow + step);
            break;
          case 'ArrowLeft':
            selStartCol = Math.max(1, selStartCol - step);
            break;
          case 'ArrowRight':
            selStartCol = Math.min(store.MAX_COLS, selStartCol + step);
            break;
        }

        maskStore.selStartRow = selStartRow;
        maskStore.selEndRow = selStartRow;
        maskStore.selStartCol = selStartCol;
        maskStore.selEndCol = selStartCol;
        maskStore.moveAtom++;
      }

      // Enter to edit
      if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        maskStore.editRow = maskStore.selStartRow;
        maskStore.editCol = maskStore.selStartCol;
        maskStore.initialInput = '';
      }

      // F2 to edit
      if (e.key === 'F2') {
        e.preventDefault();
        maskStore.editRow = maskStore.selStartRow;
        maskStore.editCol = maskStore.selStartCol;
        maskStore.initialInput = dataStore.getCellValue(maskStore.selStartRow, maskStore.selStartCol);
      }

      // Direct typing to edit
      if (
        maskStore.editRow === -1 &&
        maskStore.selStartRow > 0 &&
        maskStore.selStartCol > 0
      ) {
        const isSingleChar =
          e.key.length === 1 &&
          !e.ctrlKey &&
          !e.metaKey &&
          !e.altKey;

        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }

        if (isSingleChar) {
          e.preventDefault();
          maskStore.editRow = maskStore.selStartRow;
          maskStore.editCol = maskStore.selStartCol;
          maskStore.initialInput = e.key;
        }
      }
    };

    onMounted(() => {
      window.addEventListener('keydown', handleKeyDown);
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeyDown);
    });

    const showAI = () => {
      aiStore.show();
    };

    return {
      colCount,
      rowCount,
      getColLabel,
      gridStyles,
      onScrollerMouseDown,
      menuVisible,
      menuX,
      menuY,
      onHeaderContextMenu,
      onRowContextMenu,
      closeMenu,
      handleMenuAction,
      onSelectAll,
      maskRef,
      handleUndo: dataStore.undo,
      handleRedo: dataStore.redo,
      canUndo: computed(() => dataStore.canUndo),
      canRedo: computed(() => dataStore.canRedo),
      currentAddress: computed(() => {
        if (maskStore.selStartRow <= 0 || maskStore.selStartCol <= 0) return '';
        const colLabel = getColLabel(maskStore.selStartCol - 1);
        return `${colLabel}${maskStore.selStartRow}`;
      }),
      currentVal,
      formulaVal,
      onFormulaInput,
      onFormulaFocus,
      onFormulaBlur,
      onCompositionEnd,
      aiStore,
      domMaskWidth,
      maincontent,
      domMaskHeight,
      domMaskTop,
      showAI
    };
    
  }
});
</script>
<style scoped>
.domMask {
  background-color: #c32020 !important;
  z-index: 9999;

  position: fixed;

}
.app-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.top-nav {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: linear-gradient(180deg, #fafafa 0%, #f0f0f0 100%);
  border-bottom: 1px solid #d0d0d0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-container {
  flex: 1;
  overflow: hidden;
  background-color: #fff;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.notification-bar {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-bottom: 1px solid #bae6fd;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #0369a1;
  font-weight: 500;
}

.notification-icon {
  flex-shrink: 0;
  color: #0284c7;
}

.tool-group {
  display: flex;
  gap: 4px;
}

.tool-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  color: #555555;
  transition: all 0.2s;
}

.tool-btn:hover:not(:disabled) {
  background: #e8e8e8;
  border-color: #d0d0d0;
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tool-divider {
  width: 1px;
  height: 20px;
  background: #d0d0d0;
  margin: 0 4px;
}

.fx-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.address-box {
  min-width: 48px;
  height: 24px;
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #333333;
  font-weight: 500;
}

.fx-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}


.fx-icon a {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  text-decoration: none;
  color: inherit;
}

.fx-icon img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.formula-bar {
  flex: 1;
  height: 24px;
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  padding: 0 8px;
  font-size: 12px;
  outline: none;
}

.formula-bar:focus {
  border-color: #3b82f6;
}

.scroller {
  height: calc(100% - 48px);
  overflow: auto;
  position: relative;
  outline: none;
}

.header-row {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  min-width: fit-content;
}

.corner {
  position: sticky;
  left: 0;
  z-index: 10;
  width: 44px;
  height: 24px;
  background: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  cursor: pointer;
  flex-shrink: 0;
}

.corner:hover {
  background: #e8e8e8;
}

.data-row {
  
  display: flex;
  min-width: fit-content;
}

.sticky-left {
  position: sticky;
  left: 0;
  z-index: 50;
}

.ai-container {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}
</style>
