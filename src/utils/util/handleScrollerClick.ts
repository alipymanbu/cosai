import { useMaskStore } from '@/stores/store/SelectionStore';

const onScrollerMouseDown = (e: MouseEvent) => {
  const maskStore = useMaskStore();

  // 检查当前焦点是否在 formula-bar 上
  const activeEl = document.activeElement;
  const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');

  if (isFormulaBarFocused) {
    // 让 formula-bar 失去焦点
    (activeEl as HTMLElement)?.blur();
  }

  if (e.target === e.currentTarget) {
    if (maskStore.editRow !== -1) {
      maskStore.editRow = -1;
      maskStore.editCol = -1;
    }
  }
};

export default onScrollerMouseDown;
