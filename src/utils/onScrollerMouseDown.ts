import { useMaskStore } from '@/stores/MaskStore';

const onScrollerMouseDown = (e: MouseEvent) => {
  const maskStore = useMaskStore();

  const activeEl = document.activeElement;
  const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');

  if (isFormulaBarFocused) {
    (activeEl as HTMLElement)?.blur();
  }

  if (e.target === e.currentTarget) {
    if (maskStore.editRow !== -1) {
      setTimeout(() => {
        maskStore.editRow = -1;
        maskStore.editCol = -1;
      }, 0);
    }
  }
};

export default onScrollerMouseDown;
