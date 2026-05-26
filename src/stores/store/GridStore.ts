import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useCounterStore = defineStore('rowColumn', () => {
  const colWidths = ref<Record<number, number>>({});
  const rowHeights = ref<Record<number, number>>({});

  const DEFAULT_WIDTH = 73;
  const DEFAULT_HEIGHT = 19;
  const MAX_ROWS = ref(100);
  const MAX_COLS = ref(26);

  const getColWidth = (i: number) => colWidths.value[i] ?? DEFAULT_WIDTH;
  const getRowHeight = (i: number) => rowHeights.value[i] ?? DEFAULT_HEIGHT;

  const setColWidth = (i: number, w: number, isShow: boolean) => {
    colWidths.value[i] = isShow ? 0 : Math.max(w, 20); 
  };

  const setRowHeight = (i: number, h: number) => {
    rowHeights.value[i] = Math.max(h, 5);
  };

  const getRect = (startRow: number, startCol: number, endRow: number, endCol: number) => {
    const r1 = Math.min(startRow, endRow);
    const c1 = Math.min(startCol, endCol);
    const r2 = Math.max(startRow, endRow);
    const c2 = Math.max(startCol, endCol);

    let left = 44; 
    let top = 24;  
    let width = 0;
    let height = 0;

    for (let c = 1; c < c1; c++) {
      left += colWidths.value[c] ?? DEFAULT_WIDTH;
    }

    for (let r = 1; r < r1; r++) {
      top += rowHeights.value[r] ?? DEFAULT_HEIGHT;
    }

    for (let c = c1; c <= c2; c++) {
      width += colWidths.value[c] ?? DEFAULT_WIDTH;
    }

    for (let r = r1; r <= r2; r++) {
      height += rowHeights.value[r] ?? DEFAULT_HEIGHT;
    }

    return { left, top, width, height };
  };

  const getRowIndexAt = (y: number): number => {
    if (y <= 24) return 1;
    let currentY = 24;
    let row = 1;

    while (row < MAX_ROWS.value) {
      const h = rowHeights.value[row] ?? DEFAULT_HEIGHT;
      if (y < currentY + h) return row;
      currentY += h;
      row++;
    }
    return MAX_ROWS.value;
  };

  const getColIndexAt = (x: number): number => {
    if (x <= 44) return 1;
    let currentX = 44;
    let col = 1;

    while (col < MAX_COLS.value) {
      const w = colWidths.value[col] ?? DEFAULT_WIDTH;
      if (x < currentX + w) return col;
      currentX += w;
      col++;
    }
    return MAX_COLS.value;
  };

  return {
    colWidths,
    rowHeights,
    getColWidth,
    getRowHeight,
    setColWidth,
    setRowHeight,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    MAX_ROWS,
    MAX_COLS,
    getRect,
    getRowIndexAt,
    getColIndexAt
  };
});
