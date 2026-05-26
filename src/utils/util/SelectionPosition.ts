import { useMaskStore } from '@/stores/store/SelectionStore';
import { useCounterStore } from '@/stores/store/GridStore';
import { storeToRefs } from 'pinia';

function MaskPos(e: MouseEvent, startRow: number, startCol: number) {
  e.preventDefault();
  const maskStore = useMaskStore();
  const rowColumnStore = useCounterStore();
  const {
    isShow,
    selStartRow,
    selStartCol,
    selEndRow,
    selEndCol
  } = storeToRefs(maskStore);

  selStartRow.value = startRow;
  selStartCol.value = startCol;
  selEndRow.value = startRow;
  selEndCol.value = startCol;

  isShow.value = true;

  let currentX = e.clientX;
  let currentY = e.clientY;

  const scroller = document.querySelector('.scroller') as HTMLElement;
  let animationFrameId: number | null = null;

  const updateSelectionFromPoint = (x: number, y: number) => {
    const el = document.elementFromPoint(x, y);
    const atom = el?.closest('.atom') as HTMLElement;

    if (atom && atom.dataset.row && atom.dataset.col) {
      const r = parseInt(atom.dataset.row, 10);
      const c = parseInt(atom.dataset.col, 10);
      if (!isNaN(r) && !isNaN(c)) {
        selEndRow.value = r;
        selEndCol.value = c;
        maskStore.col = c;
        maskStore.row = r;
        return;
      }
    }

    if (scroller) {
      const rect = scroller.getBoundingClientRect();
      const scrollTop = scroller.scrollTop;
      const scrollLeft = scroller.scrollLeft;

      const gridX = (x - rect.left) + scrollLeft;
      const gridY = (y - rect.top) + scrollTop;

      const r = rowColumnStore.getRowIndexAt(gridY);
      const c = rowColumnStore.getColIndexAt(gridX);

      selEndRow.value = r;
      selEndCol.value = c;

      maskStore.col = c;
      maskStore.row = r;
    }
  };

  const autoScroll = () => {
    if (!scroller) return;

    const rect = scroller.getBoundingClientRect();
    const edgeSize = 50;
    const maxSpeed = 5;

    let vx = 0;
    let vy = 0;

    if (currentY < rect.top + edgeSize) {
      const intensity = (rect.top + edgeSize - currentY) / edgeSize;
      vy = -maxSpeed * intensity;
    } else if (currentY > rect.bottom - edgeSize) {
      const intensity = (currentY - (rect.bottom - edgeSize)) / edgeSize;
      vy = maxSpeed * intensity;
    }

    if (currentX < rect.left + edgeSize) {
      const intensity = (rect.left + edgeSize - currentX) / edgeSize;
      vx = -maxSpeed * intensity;
    } else if (currentX > rect.right - edgeSize) {
      const intensity = (currentX - (rect.right - edgeSize)) / edgeSize;
      vx = maxSpeed * intensity;
    }

    if (vx !== 0 || vy !== 0) {
      scroller.scrollLeft += vx;
      scroller.scrollTop += vy;
      updateSelectionFromPoint(currentX, currentY);
    }

    animationFrameId = requestAnimationFrame(autoScroll);
  };

  const doRec = (ev: MouseEvent) => {
    if (ev.buttons === 0) {
      stopRec();
      return;
    }
    currentX = ev.clientX;
    currentY = ev.clientY;
    updateSelectionFromPoint(currentX, currentY);
  };

  const stopRec = () => {
    window.removeEventListener('mousemove', doRec);
    window.removeEventListener('mouseup', stopRec);
    window.removeEventListener('mouseenter', checkButtons);
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
    }
  };

  const checkButtons = (ev: MouseEvent) => {
    if (ev.buttons === 0) {
      stopRec();
    }
  };

  window.addEventListener('mousemove', doRec);
  window.addEventListener('mouseup', stopRec);
  window.addEventListener('mouseenter', checkButtons);

  autoScroll();
}

export default MaskPos;
