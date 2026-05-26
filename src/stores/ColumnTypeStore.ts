import { defineStore } from 'pinia';

export const useColumnTypeStore = defineStore('columnType', {
  persist: {
    key: 'column-type-store',
    storage: localStorage,
  },
  state: () => ({
    columnsWithType: [] as { name: string; type: string }[] // 列类型信息
  }),
  actions: {
    setColumnsWithType(columns: { name: string; type: string }[]) {
      this.columnsWithType = columns;
    },
    clearColumnsWithType() {
      this.columnsWithType = [];
    }
  }
});
