import { defineStore } from 'pinia';
import { useCounterStore } from './RowColumn';

export const useDataStore = defineStore('data', {
  persist: {
    key: 'data-store',
    storage: localStorage,
    serializer: {
      serialize: (state) => {
        return JSON.stringify({ cells: state.cells });
      },
      deserialize: (value) => {
        const parsed = JSON.parse(value);
        return { ...parsed, history: [], future: [], isFileMenuOpen: false, dataChanged: 0, _batch: undefined };
      }
    }
  },
  state: () => ({
    cells: {} as Record<string, string>,
    history: [] as { batch: { key: string; value: string | undefined }[] }[],
    future: [] as { batch: { key: string; value: string | undefined }[] }[],
    isFileMenuOpen: false,
    dataChanged: 0, // 1表示数据已更改，0表示未更改
    highlightedNewRows: [] as number[], // 新出现的行索引（标绿）
    highlightedDiffCells: [] as string[], // 不一样的单元格坐标（标蓝）
    highlightedDeletedRows: [] as number[], // 删除的行索引（标红）
    addedDeletedRows: [] as number[], // 因missing_ids添加的行索引（确定时需删除）
    oldCellsBackup: {} as Record<string, string>, // 旧数据备份（用于取消恢复）
    _batch: undefined as { key: string; value: string | undefined }[] | undefined
  }),
  getters: {
    canUndo: (state) => state.history.length > 0,
    canRedo: (state) => state.future.length > 0
  },
  actions: {
    getCellValue(row: number, col: number): string {
      return this.cells[`${row}-${col}`] || '';
    },
    async syncToBackend() {
      if (this.dataChanged === 1) {
        try {
          const response = await fetch('http://localhost:8001/api/post-data', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(this.cells),
          });
          console.log('数据已同步到后端');
          this.dataChanged = 0;
        } catch (error) {
          console.error('同步数据到后端失败:', error);
        }
      } else {
        console.log('数据未更改，跳过同步');
      }
    },
    // 开始批量操作
    startBatch() {
      this._batch = [];
    },
    // 结束批量操作并保存历史
    endBatch() {
      if (this._batch && this._batch.length > 0) {
        this.history.push({ batch: this._batch });
        if (this.history.length > 50) {
          this.history.shift();
        }
        this.future = [];
        this._batch = undefined;
      }
    },
    setCellValue(row: number, col: number, value: string, isDelete: boolean = false, isCopy: boolean = true, saveHistory: boolean = true) {
      const store = useCounterStore();
      const key = `${row}-${col}`;

      if (saveHistory) {
        if (this._batch) {
          // 如果在批量操作中，添加到当前批次
          this._batch.push({ key, value: this.cells[key] });
        } else {
          // 否则单独保存历史
          this.history.push({ batch: [{ key, value: this.cells[key] }] });
          if (this.history.length > 50) {
            this.history.shift();
          }
          this.future = [];
        }
      }

      if (isCopy && row === store.MAX_ROWS) {
        store.MAX_ROWS += 50;
      };
      if (isCopy && col === store.MAX_COLS) {
        store.MAX_COLS += 5;
      };
      if (!isDelete) {
        if (!value) {
          delete this.cells[`${row}-${col}`];
        } else {
          this.cells[`${row}-${col}`] = value;
        }
      } else {
        if (row === 0) {
          for (const key in this.cells) {
            const parts = key.split('-');
            const r = parseInt(parts[0], 10);
            const c = parseInt(parts[1], 10);
            if (c === col) {
              delete this.cells[`${r}-${c}`];
            }
          }
        }
      }
      this.dataChanged = 1;
    },
    clearAll() {
      this.cells = {};
      this.history = [];
      this.future = [];
      this.highlightedNewRows = [];
      this.highlightedDiffCells = [];
      this.highlightedDeletedRows = [];
      this.addedDeletedRows = [];
      this.oldCellsBackup = {};
      this.dataChanged = 1;
    },

    setHighlightedNewRows(rows: number[]) {
      this.highlightedNewRows = rows;
    },

    clearHighlightedNewRows() {
      this.highlightedNewRows = [];
    },

    setHighlightedDiffCells(cells: string[]) {
      this.highlightedDiffCells = cells;
    },

    clearHighlightedDiffCells() {
      this.highlightedDiffCells = [];
    },

    setHighlightedDeletedRows(rows: number[]) {
      this.highlightedDeletedRows = rows;
    },

    clearHighlightedDeletedRows() {
      this.highlightedDeletedRows = [];
    },

    setAddedDeletedRows(rows: number[]) {
      this.addedDeletedRows = rows;
    },

    clearAddedDeletedRows() {
      this.addedDeletedRows = [];
    },

    backupOldCells() {
      this.oldCellsBackup = { ...this.cells };
    },

    restoreOldCells() {
      this.cells = { ...this.oldCellsBackup };
      this.oldCellsBackup = {};
      this.dataChanged = 1;
    },

    deleteAddedDeletedRows() {
      // 删除因missing_ids添加的行
      this.addedDeletedRows.forEach(row => {
        for (const key in this.cells) {
          if (key.startsWith(`${row}-`)) {
            delete this.cells[key];
          }
        }
      });
      this.addedDeletedRows = [];
    },

    deleteLastColumn() {
      // 找到最大的列号
      let maxCol = 0;
      for (const key in this.cells) {
        const parts = key.split('-');
        const col = parseInt(parts[1], 10);
        if (col > maxCol) {
          maxCol = col;
        }
      }

      // 删除最后一列的所有单元格
      for (const key in this.cells) {
        const parts = key.split('-');
        const col = parseInt(parts[1], 10);
        if (col === maxCol) {
          delete this.cells[key];
        }
      }
    },

    removeEmptyCells() {
      // 删除所有空格单元格
      for (const key in this.cells) {
        if (this.cells[key] === ' ') {
          delete this.cells[key];
        }
      }
    },

    sortRowsByColumn(col: number, ascending: boolean) {
      // 批量操作不保存历史记录

      const rows: Record<number, Record<number, string>> = {};
      let maxRow = 0;

      for (const key in this.cells) {
        const parts = key.split('-');
        const r = parseInt(parts[0], 10);
        const c = parseInt(parts[1], 10);
        if (r > maxRow) maxRow = r;

        if (!rows[r]) rows[r] = {};
        rows[r][c] = this.cells[key];
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

      this.cells = newCells;
      this.dataChanged = 1;
    },
    deleteRow(targetRow: number) {
      // 批量操作不保存历史记录

      const allKeys = Object.keys(this.cells);

      const newCells: Record<string, string> = {};

      for (const key of allKeys) {
        const parts = key.split('-');
        const r = parseInt(parts[0], 10);
        const c = parseInt(parts[1], 10);

        if (r === targetRow) {
          continue;
        } else if (r > targetRow) {
          newCells[`${r - 1}-${c}`] = this.cells[key];
        } else {
          newCells[key] = this.cells[key];
        }
      }
      this.cells = newCells;
      this.dataChanged = 1;
    },
    deleteColumn(targetCol: number) {
      // 批量操作不保存历史记录

      const allKeys = Object.keys(this.cells);
      const newCells: Record<string, string> = {};

      for (const key of allKeys) {
        const parts = key.split('-');
        const r = parseInt(parts[0], 10);
        const c = parseInt(parts[1], 10);

        if (c === targetCol) {
          continue;
        } else if (c > targetCol) {
          newCells[`${r}-${c - 1}`] = this.cells[key];
        } else {
          newCells[key] = this.cells[key];
        }
      }
      this.cells = newCells;
      this.dataChanged = 1;
    },
    undo() {
      if (this.history.length === 0) return;
      const lastChange = this.history.pop();
      if (lastChange) {
        // 保存当前值到 future
        const currentBatch: { key: string; value: string | undefined }[] = [];
        for (const item of lastChange.batch) {
          currentBatch.push({ key: item.key, value: this.cells[item.key] });
        }
        this.future.push({ batch: currentBatch });
        // 恢复旧值
        for (const item of lastChange.batch) {
          if (item.value !== undefined && item.value !== '') {
            this.cells[item.key] = item.value;
          } else {
            delete this.cells[item.key];
          }
        }
        this.dataChanged = 1;
      }
    },
    redo() {
      if (this.future.length === 0) return;
      const nextChange = this.future.pop();
      if (nextChange) {
        // 保存当前值到 history
        const currentBatch: { key: string; value: string | undefined }[] = [];
        for (const item of nextChange.batch) {
          currentBatch.push({ key: item.key, value: this.cells[item.key] });
        }
        this.history.push({ batch: currentBatch });
        // 恢复新值
        for (const item of nextChange.batch) {
          if (item.value !== undefined && item.value !== '') {
            this.cells[item.key] = item.value;
          } else {
            delete this.cells[item.key];
          }
        }
        this.dataChanged = 1;
      }
    },
    openFileMenu() {
      console.log('📂 [DataStore] openFileMenu 被调用');
      this.isFileMenuOpen = true;
      console.log('📂 [DataStore] isFileMenuOpen 设置为:', this.isFileMenuOpen);
    },
    closeFileMenu() {
      console.log('❌ [DataStore] closeFileMenu 被调用');
      this.isFileMenuOpen = false;
      console.log('❌ [DataStore] isFileMenuOpen 设置为:', this.isFileMenuOpen);
    }
  }
});
