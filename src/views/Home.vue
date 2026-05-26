<template>
  <div class="app-wrapper">
    <div class="top-nav" ref="topnav">
      <Logo />
    </div>
    <div v-if="currentNavComponent" class="nav-component-container">
      <component :is="currentNavComponent" />
    </div>
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
          <div class="tool-divider"></div>
          <div class="fx-bar">
             <div class="address-box">{{ currentAddress }}</div>
             <div class="fx-icon"><router-link to="/setting"><img src="/earth.png" alt=""></router-link></div>
             <input 
                class="formula-bar" 
                :value="formulaVal" 
                @input="onFormulaInput" 
                @focus="onFormulaFocus" 
                @blur="onFormulaBlur"
                @compositionend="onCompositionEnd"
             />
          </div>
        </div>

        <div class="scroller" @scroll="onScroll" @mousedown="onScrollerMouseDown" tabindex="0" style="overflow-y: auto;">
          <!-- Header Row -->
          <div class="header-row" style="position: sticky; top: 0; z-index: 10; background: white;">
            <!-- Top Left Corner (Fixed) -->
            <div class="corner" @click="onSelectAll"></div>

            <!-- Column Headers -->
            <Column v-for="i in colCount" :key="i" :index="i" :header_logo="getColLabel(i - 1)"
              @header-contextmenu="onHeaderContextMenu" />
          </div>

          <!-- 占位元素，保持滚动高度 -->
          <div :style="{ height: totalHeight + 'px', width: '1px' }"></div>

          <!-- Data Rows (只渲染可见区域) -->
          <div :style="{ position: 'absolute', top: offsetTop + 'px', width: '100%' }">
            <div v-for="r in visibleRows" :key="r" class="data-row">
              <!-- Row Header -->
              <Row :index="r" class="sticky-left" @row-contextmenu="onRowContextMenu" />

              <!-- Atoms -->
              <Atom v-for="c in colCount" :key="c" :Row="r" :Column="c" />
            </div>
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
import Column from '@/components/Table/Column.vue';
import Row from '@/components/Table/Row.vue';
import Atom from '@/components/Table/Atom.vue';
import Error from '@/components/Table/error.vue';
import Ai from '@/components/Ai.vue';
import Mask from '@/components/Table/Mask.vue';
import CopyMask from '@/components/CopyMask.vue';
import ContextMenu from '@/components/Table/ContextMenu.vue';
import { useCounterStore } from '@/stores/RowColumn';
import Logo from '@/components/Logo.vue';
import { useMaskStore } from '@/stores/MaskStore';
import { useDataStore } from '@/stores/DataStore';
import { useAiStore } from '@/stores/AiStore';
import { useCapsuleStore } from '@/stores/CapsuleStore';
import onScrollerMouseDown from '@/utils/onScrollerMouseDown';


const capsuleStore = useCapsuleStore();

// 动态组件映射（缓存已加载的组件）
const navComponentsCache: Record<string, () => Promise<any>> = {};

// 获取组件导入函数
const getComponentImporter = (componentName: string): (() => Promise<any>) => {
  // 如果缓存中有，直接返回
  if (navComponentsCache[componentName]) {
    return navComponentsCache[componentName];
  }
  
  // 动态创建导入函数
  const importer = () => import(`@/components/ToolsNavs/${componentName}/index.vue`);
  
  // 缓存起来
  navComponentsCache[componentName] = importer;
  return importer;
};

// 加载 Capsule 项
const loadCapsuleItems = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/components');
    if (response.ok) {
      const result = await response.json();
      console.log('📋 后端返回的组件列表:', result.components);
      
      // 过滤掉空字符串和无效名称
      const validComponents = (result.components || [])
        .filter((name: string) => name && name.trim() !== '')
        .map((name: string) => name.trim());
      
      console.log('✅ 过滤后的有效组件:', validComponents);
      
      
      // 将组件列表转换为标准格式
      return validComponents.map((componentName: string, index: number) => ({
        id: index + 1,
        componentName,
        name: componentName
      }));
    }
  } catch (error) {
    console.error('加载 Capsule 项失败:', error);
  }
  return [];
};

export default defineComponent({
  name: 'Home',
  components: { Column, Row, Atom, Ai, Mask, CopyMask, ContextMenu, Error, Logo },
  setup() {
    const store = useCounterStore();
    const maskStore = useMaskStore();
    const dataStore = useDataStore();
    const aiStore = useAiStore();

    const colCount = computed(() => store.MAX_COLS);
    const rowCount = computed(() => store.MAX_ROWS);
    
    const visibleRows = computed(() => store.visibleRows);
    const totalHeight = computed(() => store.totalHeight);
    const offsetTop = computed(() => store.offsetTop);

    const maincontent = ref(null);
    const topnav = ref(null);
    
    const domMaskWidth = computed(() => (document.documentElement.clientWidth - maskStore.aiInput) + 'px');
    const domMaskTop = computed(() => ((topnav.value as HTMLElement | null)?.clientHeight ?? 0) + 9 + 'px');
    const domMaskHeight = computed(() => (document.documentElement.clientHeight - ((topnav.value as HTMLElement | null)?.clientHeight ?? 0)) + 'px');
    // 初始化 AI 面板宽度
    if (maskStore.aiInput === 0) {
      maskStore.aiInput = 350;
    }

    // 当前选中的导航类型
    const currentNavType = ref<string>('');
    // 动态加载的导航组件
    const TopNav = shallowRef<any>(null);
    // 当前显示的导航组件
    const currentNavComponent = shallowRef<any>(null);
    // 对话框是否打开
    const isDialogOpen = ref(false);

    // 加载导航组件
    const loadNavComponent = async (navType: string) => {
      const importer = getComponentImporter(navType);
      if (importer) {
        try {
          TopNav.value = (await importer()).default;
          currentNavComponent.value = TopNav.value;
          currentNavType.value = navType;
          console.log('✅ 已加载组件:', navType);
        } catch (error) {
          console.error(`❌ 加载 ${navType} 失败:`, error);
        }
      } else {
        console.warn(`⚠️ 未找到组件：${navType}`);
      }
    };

    // 切换导航类型
    const switchNavType = (navType: string) => {
      if (currentNavType.value !== navType) {
        currentNavType.value = navType;
        loadNavComponent(navType);
      }
    };

    // 初始加载
    loadNavComponent(currentNavType.value);

    // 处理主标签切换
    const handleTabChange = (tab: string) => {
      console.log('切换到主标签:', tab);
      currentNavComponent.value = null;
    };

    // 处理对话框状态变化
    const handleDialogStateChange = (isOpen: boolean) => {
      isDialogOpen.value = isOpen;
    };

    // 处理子标签切换
    const handleSubTabChange = (payload: { tab: string; subTab: string }) => {
      console.log('切换到子标签:', payload);
      
      if (payload.tab === 'analysis' && payload.subTab === 'ml') {
        loadSpecificNavComponent('TopNav0');
      } else if (payload.tab === 'analysis' && payload.subTab === 'stats') {
        loadSpecificNavComponent('TopNav1');
      } else {
        currentNavComponent.value = null;
      }
    };

    // 加载指定的导航组件
    const loadSpecificNavComponent = async (componentName: string) => {
      try {
        const module = await import(`@/components/ToolsNavs/${componentName}/index.vue`);
        currentNavComponent.value = module.default;
        console.log('✅ 已加载组件:', componentName);
      } catch (error) {
        console.error(`❌ 加载 ${componentName} 失败:`, error);
      }
    };
    
    // 加载数据到 store
    const loadDataToStore = async (rows: string[][], columns?: string[], hasHeader?: boolean) => {
      console.log('开始导入数据，总行数:', rows.length);
      
      const dataStore = useDataStore();
      // 清空现有数据
      dataStore.clearAll();
      
      // 清空列标题
      store.clearColHeaders();
      
      // 如果有自定义列标题，保存到 store
      if (columns && columns.length > 0 && hasHeader) {
        console.log('设置自定义列标题:', columns);
        for (let c = 0; c < columns.length; c++) {
          store.setColHeader(c + 1, columns[c]);
        }
      }
      
      // 批量导入数据
      // 如果勾选了"第一行为标题行"，跳过第一行数据（因为它已经作为列标题）
      const startIndex = hasHeader ? 1 : 0;
      const actualRows = rows.length - startIndex;
      
      for (let r = startIndex; r < rows.length; r++) {
        for (let c = 0; c < rows[r].length; c++) {
          const value = rows[r][c];
          if (value) {
            dataStore.setCellValue(r - startIndex + 1, c + 1, value, false, false, true);
          }
        }
      }
      
      // 设置最大行数为实际行数 + 50
      store.MAX_ROWS = actualRows + 50;
      console.log(`📈 导入后行数调整: ${actualRows} + 50 = ${store.MAX_ROWS}`);
      
      console.log('✅ 数据导入完成，总单元格数:', Object.keys(dataStore.cells).length);
    };
    
    // 监听 Capsule 组件的选择变化
    onMounted(async () => {
      console.log('🏠 Home.vue 已挂载');
      
      // 从 store 恢复选中的 ID
      capsuleStore.restoreFromStorage();
      
      // 监听 store 中 selectedId 的变化
      watch(() => capsuleStore.selectedId, async (newId, oldId) => {
        if (newId !== oldId) {
          console.log('📦 检测到选中 ID 变化:', newId);
          const items = await loadCapsuleItems();
          const selectedItem = items.find(item => item.id.toString() === newId);
          if (selectedItem && selectedItem.componentName) {
            console.log('🚀 切换组件:', selectedItem.componentName);
            loadNavComponent(selectedItem.componentName);
          }
        }
      }, { immediate: false });
      
      // 初始加载：根据选中的 ID 加载组件
    const items = await loadCapsuleItems();
    console.log('📋 加载到的 Capsule 项:', items);
    
    // 确保有有效的组件可以加载
    if (items.length > 0) {
      // 如果当前选中的 ID 没有对应的组件，使用第一个
      const selectedItem = items.find(item => item.id.toString() === capsuleStore.selectedId);
      if (selectedItem && selectedItem.componentName) {
        console.log('🚀 初始加载组件:', selectedItem.componentName);
        loadNavComponent(selectedItem.componentName);
      } else {
        // 使用第一个组件
        console.log('⚠️ 未找到选中的组件，使用第一个组件:', items[0].componentName);
        loadNavComponent(items[0].componentName);
      }
    } else {
      console.warn('⚠️ 没有可用的导航组件');
    }
  });

    const menuVisible = ref(false);
    const menuX = ref(0);
    const menuY = ref(0);
    const menuTargetCol = ref(-1);
    const menuTargetRow = ref(-1);

    const maskRef = ref(null);

    const isFormulaFocus = ref(false);
    const hasSavedForFormula = ref(false);
    const formulaVal = ref('');
    const formulaCellRow = ref(-1);
    const formulaCellCol = ref(-1);

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
      // 预览模式下禁止编辑
      if (maskStore.isPreviewMode) {
        return;
      }
      formulaVal.value = currentVal.value;
      isFormulaFocus.value = true;
      hasSavedForFormula.value = false;
      formulaCellRow.value = maskStore.selStartRow;
      formulaCellCol.value = maskStore.selStartCol;
      maskStore.isFormulaEditing = true;
      maskStore.formulaEditRow = maskStore.selStartRow;
      maskStore.formulaEditCol = maskStore.selStartCol;
    };

    const onFormulaBlur = () => {
      isFormulaFocus.value = false;
      hasSavedForFormula.value = false;
      
      // 预览模式下禁止编辑
      if (!maskStore.isPreviewMode && formulaCellRow.value > 0 && formulaCellCol.value > 0) {
        dataStore.setCellValue(formulaCellRow.value, formulaCellCol.value, formulaVal.value, false, false, true);
      }
      
      // 重置公式栏编辑状态
      maskStore.isFormulaEditing = false;
      maskStore.formulaEditRow = -1;
      maskStore.formulaEditCol = -1;
      maskStore.initialInput = null;
      formulaCellRow.value = -1;
      formulaCellCol.value = -1;
    };

    const onCompositionEnd = (e: Event) => {
      const val = (e.target as HTMLInputElement).value;
      formulaVal.value = val;
      
      if (formulaCellRow.value > 0 && formulaCellCol.value > 0) {
        maskStore.initialInput = val;
      }
    };

    const onFormulaInput = (e: Event) => {
      const val = (e.target as HTMLInputElement).value;
      formulaVal.value = val;
      
      if (formulaCellRow.value > 0 && formulaCellCol.value > 0) {
        maskStore.initialInput = val;
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
      // 优先使用自定义列标题
      const customHeader = store.getColHeader(index + 1);
      if (customHeader) {
        return customHeader;
      }
      
      // 默认使用 ABCD...
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

      // 如果对话框打开，阻止键盘事件传递到表格
      if (isDialogOpen.value) {
        return;
      }

      // 阻止 Ctrl+S 和 Ctrl+Shift+S 的默认浏览器保存行为
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        return;
      }

      if (e.key === 'Tab') {
        e.preventDefault();

        // If currently editing, finish editing first (triggers save in Atom watcher)
        if (maskStore.editRow !== -1) {
           dataStore.setCellValue(maskStore.editRow, maskStore.editCol, maskStore.initialInput ?? dataStore.getCellValue(maskStore.editRow, maskStore.editCol), false, true, true);
           maskStore.editRow = -1;
           maskStore.editCol = -1;
        }

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
      
      if (maskStore.editRow !== -1) {
        const activeEl = document.activeElement;
        const isInputFocused = activeEl?.tagName === 'INPUT' || activeEl?.tagName === 'TEXTAREA';

        if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          dataStore.setCellValue(maskStore.editRow, maskStore.editCol, maskStore.initialInput ?? dataStore.getCellValue(maskStore.editRow, maskStore.editCol), false, true, true);
          maskStore.editRow = -1;
          maskStore.editCol = -1;
          return;
        }

        if (!isInputFocused && !e.ctrlKey && !e.metaKey && e.key.length === 1) {
          e.preventDefault();
          const currentVal = maskStore.initialInput ?? dataStore.getCellValue(maskStore.editRow, maskStore.editCol);
          maskStore.initialInput = currentVal + e.key;
        }
        return;
      }

      // Delete / Backspace to clear selection
      if (e.key === 'Delete' || e.key === 'Backspace') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        
        // 开始批量操作
        dataStore.startBatch();
        
        // Multi-Column
        if (maskStore.selectedCols.size > 0) {
           const sortedCols = Array.from(maskStore.selectedCols);
           for (let r = 1; r <= store.MAX_ROWS; r++) {
             for (const c of sortedCols) {
               if (dataStore.getCellValue(r, c) !== '') {
                  dataStore.setCellValue(r, c, '', false, false, true);
               }
             }
           }
        } 
        // Multi-Row
        else if (maskStore.selectedRows.size > 0) {
           const sortedRows = Array.from(maskStore.selectedRows);
           for (const r of sortedRows) {
             for (let c = 1; c <= store.MAX_COLS; c++) {
               if (dataStore.getCellValue(r, c) !== '') {
                  dataStore.setCellValue(r, c, '', false, false, true);
               }
             }
           }
        }
        // Range / Single
        else {
           const { selStartRow, selStartCol, selEndRow, selEndCol } = maskStore;
           if (selStartRow >= 0 && selStartCol >= 0) {
              const r1 = Math.min(selStartRow, selEndRow);
              const c1 = Math.min(selStartCol, selEndCol);
              const r2 = Math.max(selStartRow, selEndRow);
              const c2 = Math.max(selStartCol, selEndCol);
              
              for (let r = r1; r <= r2; r++) {
                for (let c = c1; c <= c2; c++) {
                   if (dataStore.getCellValue(r, c) !== '') {
                      dataStore.setCellValue(r, c, '', false, false, true);
                   }
                }
              }
           }
        }
        
        // 结束批量操作并保存历史
        dataStore.endBatch();
        
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

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        dataStore.undo();
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        dataStore.redo();
        return;
      }

      if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'x')) {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        const isCut = e.key === 'x';
        isX = e.key === 'x';
        maskStore.copiedX = isX;
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
            console.log(isCut ? 'Cut multi-col to clipboard' : 'Copied multi-col to clipboard');
          } catch (err) {
            console.error('Failed to copy/cut multi: ', err);
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
            console.log(isCut ? 'Cut multi-row to clipboard' : 'Copied multi-row to clipboard');
          } catch (err) {
            console.error('Failed to copy/cut multi-row: ', err);
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
            console.log(isCut ? 'Cut to clipboard' : 'Copied to clipboard');
          } catch (err) {
            console.error('Failed to copy/cut: ', err);
          }
        }
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') {
        // 检查当前焦点是否在 formula-bar 或 Ai 组件的输入框上
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');
        
        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }
        
        e.preventDefault();
        try {
          const clipboardData = await navigator.clipboard.readText();
          const rows = clipboardData.split('\n');
          const r1 = maskStore.selStartRow;
          const c1 = maskStore.selStartCol;
          const r2 = r1 + rows.length - 1;
          const c2 = c1 + (rows[0]?.split('\t')?.length || 1) - 1;
          if (clipboardData === '') {
            return;
          }
          if (r2 > store.MAX_ROWS || c2 > store.MAX_COLS) {
            maskStore.error = true;
            return;
          }

          // 开始批量操作
          dataStore.startBatch();

          for (let i = 0; i < rows.length; i++) {
            const cols = rows[i].split('\t');
            for (let j = 0; j < cols.length; j++) {
              const r = r1 + i;
              const c = c1 + j;
              dataStore.setCellValue(r, c, cols[j], false, false, true);
            }
          }
          
          if (maskStore.copiedX) {
            // 清空原剪切区域
            if (maskStore.copiedCols) {
              // 清空整列
              const sortedCols = Array.from(maskStore.selectedCols).sort((a, b) => a - b);
              for (let r = 1; r <= store.MAX_ROWS; r++) {
                for (const c of sortedCols) {
                  dataStore.setCellValue(r, c, '', false, false, true);
                }
              }
            } else if (maskStore.copiedRows) {
              // 清空整行
              const sortedRows = Array.from(maskStore.selectedRows).sort((a, b) => a - b);
              for (const r of sortedRows) {
                for (let c = 1; c <= store.MAX_COLS; c++) {
                  dataStore.setCellValue(r, c, '', false, false, true);
                }
              }
            } else if (maskStore.copiedStartRow !== -1 && maskStore.copiedStartCol !== -1) {
              // 清空选定区域
              for (let r = maskStore.copiedStartRow; r <= maskStore.copiedEndRow; r++) {
                for (let c = maskStore.copiedStartCol; c <= maskStore.copiedEndCol; c++) {
                  dataStore.setCellValue(r, c, '', false, false, true);
                }
              }
            }
            maskStore.copiedStartRow = -1;
            maskStore.copiedStartCol = -1;
            maskStore.copiedEndRow = -1;
            maskStore.copiedEndCol = -1;
            maskStore.copiedX = false;
            maskStore.copiedCols = false;
            maskStore.copiedRows = false;
            navigator.clipboard.writeText('');
          }

          // 结束批量操作并保存历史
          dataStore.endBatch();
          
          maskStore.selStartRow = r1;
          maskStore.selStartCol = c1;
          maskStore.selEndRow = r1 + rows.length - 1;
          maskStore.selEndCol = c1 + (rows[0]?.split('\t')?.length || 1) - 1;

          console.log('Pasted from clipboard');
        } catch (err) {
          console.error('Failed to paste: ', err);
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

      // Enter to edit / confirm / exit
      if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
        const activeEl = document.activeElement;
        const isFormulaBarFocused = activeEl?.classList.contains('formula-bar');
        const isAiInputFocused = activeEl?.classList.contains('chat-input');

        if (isFormulaBarFocused || isAiInputFocused) {
          return;
        }

        if (maskStore.editRow === -1) {
          e.preventDefault();
          maskStore.editRow = maskStore.selStartRow;
          maskStore.editCol = maskStore.selStartCol;
          maskStore.initialInput = null;
        }
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
        !maskStore.isPreviewMode &&
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

    return {
      colCount,
      rowCount,
      visibleRows,
      totalHeight,
      offsetTop,
      getColLabel,
      gridStyles,
      onScroll: (e: Event) => {
        const target = e.target as HTMLElement;
        store.scrollTop = target.scrollTop;
        store.containerHeight = target.clientHeight;
      },
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
      TopNav,
      currentNavType,
      switchNavType,
      domMaskWidth,
      maincontent,
      domMaskHeight,
      topnav,
      domMaskTop,
      currentNavComponent,
      handleTabChange,
      handleSubTabChange,
      handleDialogStateChange
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

.nav-component-container {
  background: linear-gradient(180deg, #fafafa 0%, #f0f0f0 100%);
  border-bottom: 1px solid #d0d0d0;
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
  height: 19px;
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
  height: 19px;
  display: flex;
  min-width: fit-content;
  background: white;
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
