<template>
  <div class="file-menu-container" ref="containerRef">
    <!-- 下拉菜单 -->
    <div class="file-dropdown" v-if="isOpen" @click.stop>
      <div class="menu-item" @click="handleOpen">
        <span class="menu-label">📂 打开...</span>
        <span class="shortcut">Ctrl+O</span>
      </div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="hasData && handleSave()" :class="{ disabled: !hasData }">
        <span class="menu-label">💾 保存</span>
        <span class="shortcut">Ctrl+S</span>
      </div>
      <div class="menu-item" @click="hasData && handleSaveAs()" :class="{ disabled: !hasData }">
        <span class="menu-label">📥 另存为...</span>
        <span class="shortcut">Ctrl+Shift+S</span>
      </div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="hasData && handleClear()" :class="{ disabled: !hasData }">
        <span class="menu-label">🗑️ 清空数据</span>
      </div>
    </div>
    
    <!-- 隐藏的文件输入框 -->
    <input 
      ref="fileInputRef"
      type="file" 
      accept=".xlsx,.xls,.csv,.tsv,.txt"
      style="display: none"
      @change="onFileSelected"
    />
    
    <!-- 导入设置对话框 -->
    <div class="modal-overlay" v-if="showImportDialog" @click="showImportDialog = false">
      <div class="import-dialog" @click.stop>
        <h3>📥 导入文件</h3>
        
        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ selectedFile?.name }}</span>
          <span class="file-size">{{ formatFileSize(selectedFile?.size || 0) }}</span>
        </div>
        
        <!-- ===== 通用设置 ===== -->
        <div class="settings-section">
          <div class="section-title">📌 基本设置</div>
          
          <div class="form-group checkbox">
            <label class="checkbox-label">
              <input type="checkbox" v-model="importSettings.hasHeader" @change="loadPreview" />
              <span>第一行为标题行</span>
            </label>
            <span class="help-text">开启后第一行将作为列名使用</span>
          </div>
        </div>
        
        <!-- ===== CSV/文本文件设置 ===== -->
        <div class="settings-section" v-if="isTextFile">
          <div class="section-title">📝 文本文件设置</div>
          
          <div class="form-group">
            <label>编码格式：</label>
            <select v-model="importSettings.encoding" @change="loadPreview">
              <option value="utf-8">UTF-8（推荐，国际通用）</option>
              <option value="utf-8-sig">UTF-8 with BOM（部分 Excel 需要）</option>
              <option value="gbk">GBK（中文 Windows 默认）</option>
              <option value="gb2312">GB2312（老中文系统）</option>
              <option value="latin1">Latin-1（西欧语言）</option>
            </select>
            <span class="help-text">选择与文件实际编码匹配的格式</span>
          </div>
          
          <div class="form-group">
            <label>分隔符：</label>
            <select v-model="importSettings.delimiter" @change="loadPreview">
              <option value=",">逗号 ,（标准 CSV）</option>
              <option value=";">分号 ;（欧洲格式）</option>
              <option value="\t">制表符 Tab（TSV 文件）</option>
              <option value="|">竖线 |</option>
              <option value=" ">空格</option>
            </select>
            <span class="help-text">分隔各列的字符</span>
          </div>
          
          <div class="form-group">
            <label>文本限定符：</label>
            <select v-model="importSettings.quotechar" @change="loadPreview">
              <option value='"'>双引号 "（标准）</option>
              <option value="'">单引号 '</option>
              <option value="">无</option>
            </select>
            <span class="help-text">包围含分隔符的文本</span>
          </div>
        </div>
        
        <!-- ===== Excel 文件设置 ===== -->
        <div class="settings-section" v-if="isExcelFile">
          <div class="section-title">📊 Excel 设置</div>
          
          <div class="form-group">
            <label>工作表：</label>
            <select v-model="importSettings.sheetIndex" @change="loadPreview">
              <option v-for="(sheet, idx) in availableSheets" :key="idx" :value="idx">
                {{ sheet }}
              </option>
            </select>
            <span class="help-text">选择要导入的工作表</span>
          </div>
        </div>
        
        <!-- 数据预览 -->
        <div class="preview-section">
          <div class="preview-header">
            <label>👁️ 数据预览</label>
            <span class="preview-info" v-if="previewTotalRows > 0">
              共 {{ previewTotalRows }} 行 × {{ previewColCount }} 列
              <span v-if="isPreviewTruncated">（显示前 {{ previewRowCount }} 行）</span>
            </span>
          </div>
          
          <!-- 编码降级警告 -->
          <div class="encoding-warning" v-if="encodingFallback">
            ⚠️ 编码不匹配：使用 {{ selectedEncoding }} 编码读取失败，已自动切换为 {{ actualEncoding }}。可能存在乱码，请尝试选择其他编码格式。
          </div>
          
          <div class="preview-table" v-if="previewData.headers.length > 0">
            <div class="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th class="row-num">#</th>
                    <th v-for="(col, idx) in previewData.headers" :key="idx">
                      {{ col }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rIdx) in previewData.rows" :key="rIdx">
                    <td class="row-num">{{ rIdx + 1 + (importSettings.hasHeader ? 1 : 0) }}</td>
                    <td v-for="(cell, cIdx) in row" :key="cIdx" :title="cell">
                      {{ truncateCell(cell) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div v-else-if="isLoading" class="preview-loading">
            加载预览中...
          </div>
          
          <div v-else class="preview-empty">
            暂无预览数据
          </div>
        </div>
        
        <div class="dialog-buttons">
          <button @click="cancelImport">取消</button>
          <button class="primary" @click="confirmImport" :disabled="isLoading">
            {{ isLoading ? '导入中...' : '确认导入' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 另存为对话框 -->
    <div class="modal-overlay" v-if="showSaveDialog" @click="showSaveDialog = false">
      <div class="save-dialog" @click.stop>
        <h3>📥 另存为</h3>
        
        <div class="form-group">
          <label>文件名：</label>
          <input 
            ref="saveFileNameInputRef"
            v-model="saveFileName" 
            type="text" 
            placeholder="请输入文件名"
            @keyup.enter="confirmSave"
            @keydown.stop
            @input.stop
          />
        </div>
        
        <div class="form-group">
          <label>保存格式：</label>
          <select v-model="saveFormat" @change="onSaveFormatChange">
            <option value="xlsx">Excel 工作簿 (.xlsx)</option>
            <option value="csv">CSV 文件 (.csv)</option>
          </select>
        </div>
        
        <!-- CSV 导出设置 -->
        <div class="settings-section" v-if="saveFormat === 'csv'">
          <div class="section-title">📝 CSV 设置</div>
          
          <div class="form-group">
            <label>分隔符：</label>
            <select v-model="exportSettings.delimiter">
              <option value=",">逗号 ,（标准 CSV）</option>
              <option value=";">分号 ;</option>
              <option value="\t">制表符 Tab</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>编码：</label>
            <select v-model="exportSettings.encoding">
              <option value="utf-8-sig">UTF-8 with BOM（Excel 推荐）</option>
              <option value="utf-8">UTF-8（无 BOM）</option>
              <option value="gbk">GBK（中文 Windows）</option>
            </select>
          </div>
          
          <div class="form-group checkbox">
            <label class="checkbox-label">
              <input type="checkbox" v-model="exportSettings.includeHeader" />
              <span>包含标题行</span>
            </label>
          </div>
        </div>
        
        <div class="dialog-buttons">
          <button @click="showSaveDialog = false">取消</button>
          <button class="primary" @click="confirmSave" :disabled="isLoading">
            {{ isLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div class="loading-toast" v-if="isLoading && !showImportDialog">
      <span class="spinner"></span>
      <span>处理中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useDataStore } from '@/stores/DataStore';
import { useColumnTypeStore } from '@/stores/ColumnTypeStore';
import { useCounterStore } from '@/stores/RowColumn';

const emit = defineEmits(['dialogStateChange']);

const dataStore = useDataStore();
const columnTypeStore = useColumnTypeStore();
const counterStore = useCounterStore();

// 状态
const isOpen = ref(false);
const isLoading = ref(false);
const showSaveDialog = ref(false);
const showImportDialog = ref(false);
const saveFileName = ref('');
const saveFormat = ref('xlsx');
const fileInputRef = ref<HTMLInputElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);
const saveFileNameInputRef = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const currentFilePath = ref<string>('');  // 当前打开的文件路径

// 预览数据
const previewData = ref({
  headers: [] as string[],
  rows: [] as string[][]
});
const previewTotalRows = ref(0);
const previewRowCount = ref(0);
const previewColCount = ref(0);
const isPreviewTruncated = ref(false);
const encodingFallback = ref(false);  // 是否发生了编码降级
const selectedEncoding = ref('');  // 用户选择的编码
const actualEncoding = ref('');  // 实际使用的编码

// 可用的工作表（Excel）
const availableSheets = ref<string[]>(['Sheet1']);

// 监听 store 中的文件菜单状态
watch(() => dataStore.isFileMenuOpen, (newVal, oldVal) => {
  console.log('👁️ [FileMenu] watch 触发 - 旧值:', oldVal, '新值:', newVal);
  if (newVal && !oldVal) {
    // 从 false → true，打开菜单
    console.log('✅ [FileMenu] 打开菜单');
    isOpen.value = true;
  } else if (!newVal && oldVal) {
    // 从 true → false，关闭菜单
    console.log('❌ [FileMenu] 关闭菜单');
    isOpen.value = false;
  }
});

// 导入设置
const importSettings = ref({
  hasHeader: true,
  encoding: 'utf-8',
  delimiter: ',',
  quotechar: '"',
  sheetIndex: 0
});

// 导出设置
const exportSettings = ref({
  delimiter: ',',
  encoding: 'utf-8-sig',
  includeHeader: true
});

// 计算属性
const hasData = computed(() => {
  return Object.keys(dataStore.cells).length > 0;
});

const isTextFile = computed(() => {
  const name = selectedFile.value?.name.toLowerCase() ?? '';
  return name.endsWith('.csv') || name.endsWith('.tsv') || name.endsWith('.txt');
});

const isExcelFile = computed(() => {
  const name = selectedFile.value?.name.toLowerCase() ?? '';
  return name.endsWith('.xlsx') || name.endsWith('.xls');
});

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// 截断单元格显示
const truncateCell = (cell: string): string => {
  if (!cell) return '';
  return cell.length > 30 ? cell.substring(0, 30) + '...' : cell;
};

// 切换菜单
const toggleMenu = () => {
  isOpen.value = !isOpen.value;
};

// 打开菜单
const openMenu = () => {
  isOpen.value = true;
};

// 关闭菜单
const closeMenu = () => {
  isOpen.value = false;
};

defineExpose({
  openMenu,
  closeMenu
});

const handleClickOutside = (e: MouseEvent) => {
  // 菜单没打开 → 直接跳过
  if (!isOpen.value) return;

  const target = e.target as HTMLElement;
  
  // 点击的是 Logo → 不关闭
  if (target.closest('.logo')) {
    return;
  }

  // 点击的不是菜单内部 → 关闭
  if (containerRef.value && !containerRef.value.contains(target)) {
    isOpen.value = false;
    dataStore.closeFileMenu();
  }
};

const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    if (e.shiftKey) {
      handleSaveAs();
    } else {
      handleSave();
    }
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  document.addEventListener('keydown', handleGlobalKeyDown);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('keydown', handleGlobalKeyDown);
});

// 打开文件（选择器）
const handleOpen = async () => {
  isOpen.value = false;
  fileInputRef.value?.click();
};

// 清空数据
const handleClear = () => {
  if (!hasData.value) {
    return;
  }
  if (confirm('确定要清空所有数据吗？')) {
    dataStore.clearAll();
    currentFilePath.value = '';
  }
  isOpen.value = false;
};

// 文件选择后
const onFileSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  
  if (!file) return;
  
  console.log('文件已选择:', file.name);
  
  // 保存选中的文件
  selectedFile.value = file;
  
  // 如果是 CSV/TSV/TXT 文件，显示选项对话框；Excel 也显示对话框
  if (file.name.endsWith('.csv') || file.name.endsWith('.tsv') || file.name.endsWith('.txt')) {
    // 重置设置
    resetImportSettings();
    // 加载预览
    await loadPreview();
    // 显示导入对话框
    showImportDialog.value = true;
  } else {
    // Excel 文件也显示对话框
    isLoading.value = true;
    try {
      // 准备设置
      const requestBody = {
        preview: true,  // 先预览
        settings: {
          hasHeader: true,
          encoding: 'utf-8',
          delimiter: ',',
          quotechar: '"',
          sheetIndex: 0
        }
      };
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('data', JSON.stringify(requestBody));
      
      console.log('📤 上传 Excel 文件预览:', file.name);
      
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      console.log('📥 后端返回:', result);
      
      if (result.success) {
        console.log('✅ Excel 预览加载成功，行数:', result.rows?.length);
        // 加载预览数据
        previewData.value.headers = result.columns || [];
        previewData.value.rows = result.rows || [];
        previewTotalRows.value = result.totalRows || result.rows?.length || 0;
        previewRowCount.value = result.rows?.length || 0;
        previewColCount.value = result.columns?.length || 0;
        isPreviewTruncated.value = result.isPreview === true;
        availableSheets.value = result.sheets || ['Sheet1'];
        
        // 显示导入对话框
        showImportDialog.value = true;
      } else {
        alert('预览失败：' + result.error);
      }
    } catch (error) {
      console.error('❌ Excel 预览失败:', error);
      alert('预览失败，请检查后端服务是否运行');
    } finally {
      isLoading.value = false;
    }
  }
};

// 重置导入设置
const resetImportSettings = () => {
  if (isExcelFile.value) {
    importSettings.value = {
      hasHeader: true,
      encoding: 'utf-8',
      delimiter: ',',
      quotechar: '"',
      sheetIndex: 0
    };
  } else {
    importSettings.value = {
      hasHeader: true,
      encoding: 'utf-8',
      delimiter: ',',
      quotechar: '"',
      sheetIndex: 0
    };
  }
  availableSheets.value = ['Sheet1'];
};

// 加载预览
const loadPreview = async () => {
  if (!selectedFile.value) return;
  
  isLoading.value = true;
  previewData.value = { headers: [], rows: [] };
  previewTotalRows.value = 0;
  previewRowCount.value = 0;
  previewColCount.value = 0;
  encodingFallback.value = false;
  selectedEncoding.value = '';
  actualEncoding.value = '';
  
  try {
    const requestBody = {
      preview: true,
      settings: importSettings.value
    };
    
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('data', JSON.stringify(requestBody));
    
    const response = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: formData,
    });
    
    const result = await response.json();
    
    if (result.success) {
      previewData.value.headers = result.columns || [];
      
      // 如果勾选了"第一行为标题行"，预览数据跳过第一行
      const startIndex = importSettings.value.hasHeader ? 1 : 0;
      previewData.value.rows = result.rows?.slice(startIndex) || [];
      
      previewTotalRows.value = (result.totalRows || result.rows?.length || 0) - startIndex;
      previewRowCount.value = result.rows?.length ? result.rows.length - startIndex : 0;
      previewColCount.value = result.columns?.length || 0;
      isPreviewTruncated.value = result.isPreview === true;
      availableSheets.value = result.sheets || ['Sheet1'];
      
      // 如果编码降级，提示用户
      if (result.encodingFallback) {
        encodingFallback.value = true;
        selectedEncoding.value = importSettings.value.encoding;
        actualEncoding.value = result.encodingUsed || 'latin1';
      }
    } else {
      console.error('预览加载失败:', result.error);
      alert('预览失败：' + result.error + '\n\n请尝试：\n1. 选择正确的分隔符\n2. 尝试其他编码格式\n3. 检查文件是否损坏');
    }
  } catch (error) {
    console.error('预览加载失败:', error);
    const errorMsg = error instanceof Error ? error.message : String(error);
    alert('预览失败：' + errorMsg + '\n\n请确保：\n1. 后端服务已启动（python server.py）\n2. 网络连接正常');
  } finally {
    isLoading.value = false;
  }
};

// 确认导入
const confirmImport = async () => {
  if (!selectedFile.value) return;
  
  isLoading.value = true;
  
  try {
    // 准备请求体
    const requestBody = {
      preview: false,  // 正式导入
      settings: importSettings.value
    };
    
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('data', JSON.stringify(requestBody));
    
    console.log('📤 确认导入，设置:', importSettings.value);
    
    const response = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: formData,
    });
    
    const result = await response.json();
    console.log('📥 导入结果:', result);
    
    if (result.success) {
      console.log('✅ 导入成功，行数:', result.rows?.length);
      // 保存列类型信息
      if (result.columnsWithType) {
        columnTypeStore.setColumnsWithType(result.columnsWithType);
        console.log('📊 列类型信息已保存:', result.columnsWithType);
      }
      // 直接导入到当前页面
      await loadDataToStore(result.rows, result.columns, importSettings.value.hasHeader);
      currentFilePath.value = `uploads/${result.fileName}`;
      showImportDialog.value = false;
      isLoading.value = false;
    } else {
      console.error('❌ 导入失败:', result.error);
      isLoading.value = false;
      alert('导入失败：' + result.error);
    }
  } catch (error) {
    console.error('❌ 导入失败:', error);
    alert('导入失败，请检查后端服务是否运行');
    isLoading.value = false;
  } finally {
    // 确保 loading 被关闭
    if (isLoading.value) {
      isLoading.value = false;
    }
    // 清空文件输入
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
    selectedFile.value = null;
  }
};

// 取消导入
const cancelImport = () => {
  showImportDialog.value = false;
  selectedFile.value = null;
  // 清空文件输入框，确保可以重新选择同一个文件
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

// 保存（覆盖原文件）
const handleSave = async () => {
  if (!hasData.value) {
    return;
  }
  
  // 如果没有打开过文件，提示使用另存为
  if (!currentFilePath.value) {
    handleSaveAs();
    return;
  }
  
  isOpen.value = false;
  
  // 从路径中提取文件名和格式
  const pathParts = currentFilePath.value.split('/');
  const fileNameWithExt = pathParts[pathParts.length - 1];
  const fileName = fileNameWithExt.substring(0, fileNameWithExt.lastIndexOf('.'));
  const format = fileNameWithExt.split('.').pop() || 'xlsx';
  
  // 使用 performSave 函数，overwrite=false 表示保存模式
  await performSave(fileName, format, {}, false);
};

// 另存为
const handleSaveAs = () => {
  if (!hasData.value) {
    return;
  }
  isOpen.value = false;
  saveFileName.value = '';
  saveFormat.value = 'xlsx';
  exportSettings.value = {
    delimiter: ',',
    encoding: 'utf-8-sig',
    includeHeader: true
  };
  showSaveDialog.value = true;
  nextTick(() => {
    saveFileNameInputRef.value?.focus();
  });
};

// 监听对话框显示，自动聚焦
watch(showSaveDialog, (newVal, oldVal) => {
  // 只有状态真正变化时才 emit
  if (oldVal !== undefined && newVal !== oldVal) {
    emit('dialogStateChange', newVal);
  }
  if (newVal) {
    nextTick(() => {
      saveFileNameInputRef.value?.focus();
    });
  }
});

watch(showImportDialog, (newVal, oldVal) => {
  // 只有状态真正变化时才 emit
  if (oldVal !== undefined && newVal !== oldVal) {
    emit('dialogStateChange', newVal);
  }
});

// 格式改变时
const onSaveFormatChange = () => {
  if (saveFormat.value === 'csv') {
    exportSettings.value.encoding = 'utf-8-sig'; // Excel兼容
  }
};

// 确认另存为
const confirmSave = async () => {
  if (!saveFileName.value.trim()) {
    alert('请输入文件名');
    return;
  }
  
  showSaveDialog.value = false;
  await performSave(saveFileName.value.trim(), saveFormat.value, exportSettings.value, true); // true=另存为
};

// 执行保存
const performSave = async (fileName: string, format: string, settings: any, isSaveAs: boolean = false) => {
  isLoading.value = true;
  
  try {
    const { columns, rows } = prepareExportData();
    
    const payload: any = {
      fileName,
      format,
      columns,
      rows,
      overwrite: !isSaveAs, // true=保存（只存后端），false=另存为（下载）
    };
    
    // 如果是 CSV，添加导出设置
    if (format === 'csv') {
      payload.exportSettings = {
        encoding: settings.encoding || 'utf-8-sig',
        delimiter: settings.delimiter || ',',
        includeHeader: settings.includeHeader !== false
      };
    }
    
    console.log('保存请求:', payload);
    
    const response = await fetch('http://localhost:8000/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const error = await response.json();
      alert('❌ 保存失败：' + error.error);
      return;
    }
    
    if (isSaveAs) {
      // 另存为模式：浏览器下载
      const blob = await response.blob();
      const ext = format.startsWith('.') ? format : `.${format}`;
      const fullFileName = fileName.endsWith(ext) ? fileName : `${fileName}${ext}`;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fullFileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      console.log('✅ 另存为完成，文件已下载:', fullFileName);
    } else {
      // 保存模式：只显示成功提示
      const result = await response.json();
      alert(`✅ 保存成功！\n文件名：${result.fileName}\n保存位置：${result.savePath}`);
      console.log('✅ 保存完成，文件已保存到后端:', result.savePath);
    }
  } catch (error) {
    console.error('保存失败:', error);
    alert('❌ 保存失败，请检查后端服务是否运行');
  } finally {
    isLoading.value = false;
  }
};

// 准备导出数据
const prepareExportData = () => {
  const rowsMap = new Map<number, Map<number, string>>();
  let maxRow = 0;
  let maxCol = 0;
  
  // 从 store 中读取所有单元格
  Object.entries(dataStore.cells).forEach(([key, value]) => {
    if (!value) return;
    const [r, c] = key.split('-').map(Number);
    if (!rowsMap.has(r)) rowsMap.set(r, new Map());
    rowsMap.get(r)!.set(c, value);
    maxRow = Math.max(maxRow, r);
    maxCol = Math.max(maxCol, c);
  });
  
  // 生成列名
  const getColLabel = (index: number): string => {
    let label = '';
    while (index >= 0) {
      label = String.fromCharCode(65 + (index % 26)) + label;
      index = Math.floor(index / 26) - 1;
    }
    return label;
  };
  
  const columns = Array.from({ length: maxCol }, (_, i) => getColLabel(i));
  
  // 排序行索引
  const sortedRows = Array.from(rowsMap.keys()).sort((a, b) => a - b);
  
  // 生成数据行
  const dataRows = sortedRows.map(row => {
    const rowData = rowsMap.get(row)!;
    return Array.from({ length: maxCol }, (_, i) => rowData.get(i + 1) || '');
  });
  
  return { columns, rows: dataRows };
};

// 加载数据到 store
const loadDataToStore = async (rows: string[][], columns?: string[], hasHeader?: boolean) => {
  console.log('开始导入数据，总行数:', rows.length);
  
  // 清空现有数据
  dataStore.clearAll();
  
  // 不设置自定义列标题，保持 Column 组件中的列标题
  // counterStore.clearColHeaders();
  
  // 如果有自定义列标题，保存到 store（但不覆盖 Column 组件的列标题）
  // if (columns && columns.length > 0 && hasHeader) {
  //   console.log('设置自定义列标题:', columns);
  //   for (let c = 0; c < columns.length; c++) {
  //     counterStore.setColHeader(c + 1, columns[c]);
  //   }
  // }
  
  // 计算实际的行列数
  // 如果勾选了"第一行为标题行"，跳过第一行数据
  const startIndex = hasHeader ? 1 : 0;
  const dataRowCount = rows.length - startIndex;
  const dataColCount = rows.length > 0 ? Math.max(...rows.map(r => r.length)) : 0;
  
  console.log('数据规模:', dataRowCount, '行 ×', dataColCount, '列');
  
  // 设置初始行数：数据行数 + 50 行空白
  const extraRows = 50; // 额外空白行数
  counterStore.MAX_ROWS = dataRowCount + extraRows;
  counterStore.MAX_COLS = Math.max(26, dataColCount);
  
  console.log('设置表格大小:', counterStore.MAX_ROWS, '行 ×', counterStore.MAX_COLS, '列（含空白行）');
  
  // 等待 Vue 更新行列数
  await nextTick();
  
  // 批量构建 cells 对象（性能最优）
  const newCells: Record<string, string> = {};
  
  rows.forEach((row, rowIndex) => {
    // 如果勾选了"第一行为标题行"，第一行数据会放到表格的第一行（r=1）
    // 不再跳过第一行
    const r = rowIndex + 1;
    row.forEach((cell, colIndex) => {
      const c = colIndex + 1;
      if (cell !== undefined && cell !== null && cell !== '') {
        newCells[`${r}-${c}`] = String(cell);
      }
    });
  });
  
  // 一次性赋值（不会触发多次渲染）
  dataStore.cells = newCells;
  
  console.log('导入完成！单元格数量:', Object.keys(newCells).length);
  
  // 等待 Vue 完成 DOM 渲染
  await nextTick();
};
</script>

<style scoped>
.file-menu-container {
  position: relative;
  display: inline-block;
}

.file-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.15s;
  font-family: inherit;
}

.file-btn:hover,
.file-btn.active {
  background: rgba(0, 0, 0, 0.08);
}

.file-dropdown {
  position: absolute;
  top: -30px;
  left: -20px;
  margin-top: 4px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  min-width: 200px;
  z-index: 1000;
  padding: 8px 0;
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.1s;
}

.menu-item:hover:not(.disabled) {
  background: #f5f5f5;
}

.menu-item.disabled {
  color: #999;
  background: #f8f8f8;
  cursor: not-allowed;
  opacity: 0.6;
}

.menu-item.disabled .menu-label,
.menu-item.disabled .shortcut {
  color: #999;
}

.menu-label {
  font-size: 14px;
  color: #333;
}

.shortcut {
  font-size: 12px;
  color: #999;
}

.menu-divider {
  height: 1px;
  background: #eee;
  margin: 8px 0;
}

/* 对话框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.save-dialog,
.import-dialog {
  background: white;
  border-radius: 12px;
  padding: 24px;
  min-width: 500px;
  max-width: 700px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.import-dialog h3,
.save-dialog h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

/* 文件信息 */
.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.file-icon {
  font-size: 24px;
}

.file-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  word-break: break-all;
  flex: 1;
}

.file-size {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* 设置区域 */
.settings-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.settings-section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
  font-weight: 500;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  background: white;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.help-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}

.form-group.checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  cursor: pointer;
}

/* 预览 */
.preview-section {
  margin-top: 20px;
  margin-bottom: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-header label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.preview-info {
  font-size: 12px;
  color: #666;
}

/* 编码降级警告 */
.encoding-warning {
  padding: 12px 16px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 13px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.preview-table {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  max-height: 250px;
}

.table-scroll {
  overflow: auto;
  max-height: 250px;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  min-width: 100%;
}

.preview-table th,
.preview-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-table th {
  background: #f5f5f5;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}

.row-num {
  width: 40px;
  color: #999;
  text-align: center !important;
  background: #fafafa !important;
  font-size: 11px;
}

.preview-table tbody tr:hover {
  background: #f8f9fa;
}

.preview-loading,
.preview-empty {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

/* 按钮 */
.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.dialog-buttons button {
  padding: 10px 24px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
}

.dialog-buttons button:hover:not(:disabled) {
  background: #f5f5f5;
}

.dialog-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dialog-buttons button.primary {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.dialog-buttons button.primary:hover:not(:disabled) {
  background: #2563eb;
}

/* 加载提示 */
.loading-toast {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 16px 32px;
  border-radius: 8px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
