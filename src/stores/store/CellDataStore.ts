import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useCounterStore } from './GridStore';
export const useDataCellStore = defineStore('dataCell', () => {
  const cells = ref<Record<string, string>>({});
  const cellStyles = ref<Record<string, string>>({});
  const isColumn = ref<number[]>([]);
  const store = useCounterStore();

  // History stacks
  const history = ref<Record<string, string>[]>([]);
  const future = ref<Record<string, string>[]>([]);
  const styleHistory = ref<Record<string, string>[]>([]);
  const styleFuture = ref<Record<string, string>[]>([]);

  const canUndo = computed(() => history.value.length > 0);
  const canRedo = computed(() => future.value.length > 0);

  const getCellValue = (row: number, col: number): string => {
    return cells.value[`${row}-${col}`] || '';
  };

  const getCellStyle = (row: number, col: number): string => {
    return cellStyles.value[`${row}-${col}`] || '';
  };

  const setCellStyle = (row: number, col: number, style: string, saveHistory: boolean = true) => {
    if (saveHistory) {
      saveState();
    }
    if (!style) {
      delete cellStyles.value[`${row}-${col}`];
    } else {
      cellStyles.value[`${row}-${col}`] = style;
    }
  };

  const setRangeBackgroundColor = (minRow: number, maxRow: number, minCol: number, maxCol: number, color: string, saveHistory: boolean = true) => {
    if (saveHistory) {
      saveState();
    }
    for (let row = minRow; row <= maxRow; row++) {
      for (let col = minCol; col <= maxCol; col++) {
        cellStyles.value[`${row}-${col}`] = `background-color: ${color};`;
      }
    }
  };

  const setRangeBorder = (minRow: number, maxRow: number, minCol: number, maxCol: number, borderStyle: string = '1px solid blue', saveHistory: boolean = true) => {
    if (saveHistory) {
      saveState();
    }
    for (let row = minRow; row <= maxRow; row++) {
      for (let col = minCol; col <= maxCol; col++) {
        let border = '';
        if (row === minRow) border += `border-top: ${borderStyle};`;
        if (row === maxRow) border += `border-bottom: ${borderStyle};`;
        if (col === minCol) border += `border-left: ${borderStyle};`;
        if (col === maxCol) border += `border-right: ${borderStyle};`;
        if (border) {
          cellStyles.value[`${row}-${col}`] = border;
        }
      }
    }
  };

  const saveState = () => {
    history.value.push(JSON.parse(JSON.stringify(cells.value)));
    styleHistory.value.push(JSON.parse(JSON.stringify(cellStyles.value)));
    future.value = []; // Clear redo stack on new change
    styleFuture.value = [];
  };

  const undo = () => {
    if (history.value.length === 0) return;
    future.value.push(JSON.parse(JSON.stringify(cells.value)));
    styleFuture.value.push(JSON.parse(JSON.stringify(cellStyles.value)));
    const previousState = history.value.pop();
    const previousStyleState = styleHistory.value.pop();
    if (previousState) {
      cells.value = previousState;
    }
    if (previousStyleState) {
      cellStyles.value = previousStyleState;
    }
  };

  const redo = () => {
    if (future.value.length === 0) return;
    history.value.push(JSON.parse(JSON.stringify(cells.value)));
    styleHistory.value.push(JSON.parse(JSON.stringify(cellStyles.value)));
    const nextState = future.value.pop();
    const nextStyleState = styleFuture.value.pop();
    if (nextState) {
      cells.value = nextState;
    }
    if (nextStyleState) {
      cellStyles.value = nextStyleState;
    }
  };

  const setCellValue = (row: number, col: number, value: string, isDelete: boolean = false, isCopy: boolean = true, saveHistory: boolean = true) => {
    if (saveHistory) {
      saveState(); // Save state before modification
    }

    if (isCopy && row === store.MAX_ROWS) {
      store.MAX_ROWS += 50;
    };
    if (isCopy && col === store.MAX_COLS) {
      store.MAX_COLS += 5;
    };
    if (!isDelete) {
      if (!value) {
        delete cells.value[`${row}-${col}`];
      } else {
        cells.value[`${row}-${col}`] = value;
      }
    } else {
      if (row === 0) {
        for (const key in cells.value) {
          const parts = key.split('-');
          const r = parseInt(parts[0], 10);
          const c = parseInt(parts[1], 10);
          if (c === col) {
            delete cells.value[`${r}-${c}`];
          }
        }
      }
    }
  };

  const sortRowsByColumn = (col: number, ascending: boolean) => {
    saveState();

    const rows: Record<number, Record<number, string>> = {};
    let maxRow = 0;

    for (const key in cells.value) {
      const parts = key.split('-');
      const r = parseInt(parts[0], 10);
      const c = parseInt(parts[1], 10);
      if (r > maxRow) maxRow = r;

      if (!rows[r]) rows[r] = {};
      rows[r][c] = cells.value[key];
    }

    const rowIndices = [];
    for (let i = 1; i <= maxRow; i++) {
      rowIndices.push(i);
    }

    rowIndices.sort((a, b) => {
      const valA = rows[a]?.[col] || '';
      const valB = rows[b]?.[col] || '';

      if (valA === valB) return 0;

      const numA = parseFloat(valA);
      const numB = parseFloat(valB);
      const isNumA = !isNaN(numA);
      const isNumB = !isNaN(numB);

      if (isNumA && isNumB) {
        return ascending ? numA - numB : numB - numA;
      }

      return ascending ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    const newCells: Record<string, string> = {};
    rowIndices.forEach((oldRowIndex, newIndex0) => {
      const newRowIndex = newIndex0 + 1;
      const rowData = rows[oldRowIndex];
      if (rowData) {
        for (const cStr in rowData) {
          const c = parseInt(cStr, 10);
          newCells[`${newRowIndex}-${c}`] = rowData[c];
        }
      }
    });

    cells.value = newCells;
  };

  const deleteRow = (targetRow: number) => {
    saveState();

    // Shift rows up: 
    // Rows > targetRow move to row - 1
    // TargetRow data is overwritten or removed

    // 1. Collect all keys
    const allKeys = Object.keys(cells.value);

    // 2. Build new cells object
    const newCells: Record<string, string> = {};

    for (const key of allKeys) {
      const parts = key.split('-');
      const r = parseInt(parts[0], 10);
      const c = parseInt(parts[1], 10);

      if (r === targetRow) {
        // Skip (delete)
        continue;
      } else if (r > targetRow) {
        // Shift Up
        newCells[`${r - 1}-${c}`] = cells.value[key];
      } else {
        // Keep as is
        newCells[key] = cells.value[key];
      }
    }
    cells.value = newCells;
  };

  const deleteColumn = (targetCol: number) => {
    saveState();

    // Shift columns left:
    // Cols > targetCol move to col - 1

    const allKeys = Object.keys(cells.value);
    const newCells: Record<string, string> = {};

    for (const key of allKeys) {
      const parts = key.split('-');
      const r = parseInt(parts[0], 10);
      const c = parseInt(parts[1], 10);

      if (c === targetCol) {
        // Skip
        continue;
      } else if (c > targetCol) {
        // Shift Left
        newCells[`${r}-${c - 1}`] = cells.value[key];
      } else {
        // Keep
        newCells[key] = cells.value[key];
      }
    }
    cells.value = newCells;
  };

  return { cells, cellStyles, isColumn, getCellValue, getCellStyle, setCellValue, setCellStyle, setRangeBackgroundColor, setRangeBorder, saveState, sortRowsByColumn, deleteRow, deleteColumn, undo, redo, canUndo, canRedo };
}, {
  persist: {
    key: 'dataCell',
    paths: ['cells']
  }
});
