import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMaskStore = defineStore('mask', () => {
  const x = ref(0); 
  const y = ref(0); 
  const width = ref(0); 
  const height = ref(0); 

  const pos_x = ref(0); 
  const pos_y = ref(0); 
  const pos_width = ref(0); 
  const pos_height = ref(0); 

  const isShow = ref(false); 

  const lastHeight = ref(0); 
  const lastWidth = ref(0); 

  const col = ref(0); 
  const row = ref(0); 

  const selStartRow = ref(-1); 
  const selStartCol = ref(-1); 
  const selEndRow = ref(-1); 
  const selEndCol = ref(-1); 

  const editRow = ref(-1); 
  const editCol = ref(-1); 

  const copiedStartRow = ref(-1); 
  const copiedStartCol = ref(-1); 
  const copiedEndRow = ref(-1); 
  const copiedEndCol = ref(-1); 

  const isCtrlKeyDown = ref(false);
  
  // Multi-column selection support
  const selectedCols = ref<Set<number>>(new Set());
  // Multi-column copy support
  const copiedCols = ref(false);

  // Multi-row selection support (Added)
  const selectedRows = ref<Set<number>>(new Set());
  // Multi-row copy support (Added)
  const copiedRows = ref(false);
  const copiedX = ref(false);
  const copiedCopy = ref(false);
  const error = ref(false);
  const absPos_x = ref(0);
  const absPos_y = ref(0);
  const moveAtom = ref(0);
  const scrollMoveAtom = ref(0);
  const isMouseDown = ref(false);
  const initialInput = ref<string | null>(null);
  const enterPressedOnce = ref(false);
  const isFormulaEditing = ref(false);
  const formulaEditRow = ref(-1);
  const formulaEditCol = ref(-1);

  // ai输入框的宽度
  const aiInput = ref<number>(0);
  // 预览模式状态
  const isPreviewMode = ref(false);

  return {
    x, y, width, height, isShow,
    pos_x, pos_y, pos_width, pos_height,
    lastHeight, lastWidth,
    col, row,
    selStartRow, selStartCol, selEndRow, selEndCol,
    editRow, editCol,
    copiedStartRow, copiedStartCol, copiedEndRow, copiedEndCol,
    isCtrlKeyDown,
    selectedCols,
    copiedCols,
    selectedRows,
    copiedRows,
    copiedX,
    copiedCopy,
    error,
    absPos_x, absPos_y,
    moveAtom, scrollMoveAtom, isMouseDown,
    initialInput,
    enterPressedOnce,
    isFormulaEditing,
    formulaEditRow,
    formulaEditCol,
    aiInput,
    isPreviewMode
  }
})
