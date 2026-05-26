// ts的类型别名定义，用于定义更新回调函数的参数类型和返回值类型
type UpdateCallback = (newValue: number) => void;

export function startColumnResize(e: MouseEvent, startWidth: number, onUpdate: UpdateCallback) {
  // 阻止默认事件，防止浏览器滚动
  e.preventDefault();

  const startX = e.clientX;
  let animationFrameId: number | null = null;

  const doResize = (ev: MouseEvent) => {
    const currentX = ev.clientX;
    

    if (animationFrameId !== null) {
        return; 
    }
    // requestAnimationFrame 节流，避免频繁调用 onUpdate 函数
    animationFrameId = requestAnimationFrame(() => {
        const diff = currentX - startX;
        onUpdate(startWidth + diff);
        animationFrameId = null;
    });
  };

  const stopResize = () => {
    if (animationFrameId !== null) {
      // 取消当前的动画帧，避免重复调用 onUpdate 函数
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    window.removeEventListener('mousemove', doResize);
    window.removeEventListener('mouseup', stopResize);
  };

  window.addEventListener('mousemove', doResize);
  window.addEventListener('mouseup', stopResize);
}

