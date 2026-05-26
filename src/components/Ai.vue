<template>
  <div class="builder-container" ref="containerRef">
    <button v-if="messages.length > 0" class="clear-history-btn" @click="clearHistory" title="删除历史记录">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3,6 5,6 21,6"></polyline>
        <path d="M19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1 2-2h4a2,2 0 0,1 2,2v2"></path>
        <line x1="10" y1="11" x2="10" y2="17"></line>
        <line x1="14" y1="11" x2="14" y2="17"></line>
      </svg>
      <span>清空</span>
    </button>
    <!-- 关闭按钮 -->
    <button class="close-btn" @click="hide" title="关闭">
      <span class="close-icon">×</span>
    </button>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="messages-container">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="builder-logo">
            <div class="logo-icon">
              <div class="logo-square">
                <div class="logo-dots">
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
            </div>
            <h1 class="builder-title">AI 助手</h1>
            <p class="builder-subtitle">定制化 AI 助手，为用户提供智能助手。</p>
            
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div v-else class="messages-list">
          <div 
            v-for="msg in messages" 
            :key="msg.id" 
            :class="['message-item', msg.sender === 'user' ? 'user-message' : 'ai-message']"
          >
            <div class="message-content">
                <div class="text-with-code-hint">
                  <span class="message-text" v-html="parseMarkdown(msg.content)" @click="handleMessageClick(msg)"></span>
                  <span v-if="msg.code" class="code-hint" @click="toggleCodePopup($event, msg.code, msg.id)">?</span>
                </div>
                <div v-if="msg.chartUrl" class="chart-container">
                  <img :src="msg.chartUrl" alt="图表" class="chart-image" />
                </div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
          </div>
          
          <!-- 加载动画 -->
          <div v-if="isLoading" class="message-item ai-message loading-message">
            <div class="message-content">
              <div class="loading-spinner"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 聊天输入区域 -->
    <div class="chat-input-area">
      <!-- 预览模式：显示确定和取消按钮 -->
      <div v-if="isPreviewMode" class="preview-actions">
        <button class="preview-btn cancel-btn" @click="cancelPreview">取消</button>
        <button class="preview-btn confirm-btn" @click="confirmPreview">确定</button>
      </div>
      <!-- 正常模式：发送消息 -->
      <div v-else class="chat-input-container">
        <div class="chat-input-wrapper">
          <input
            ref="chatInputRef"
            type="text"
            class="chat-input"
            placeholder="开始聊天吧"
            v-model="message"
            @keydown.enter="sendMessage"
          />
          <div class="input-actions">

            <button class="action-icon attachment-btn" @click="shade">
              <img src="../../public/dividers.png" alt="选择" />
            </button>
            <div class="divider"></div>

            <button class="send-btn" @click="sendMessage">
              <span class="send-icon">↑</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Code 弹出框 -->
    <div 
      v-if="codePopup.show" 
      class="code-popup" 
      :style="{ left: codePopup.x + 'px', top: codePopup.y + 'px' }"
      @click.stop
    >
      <pre>{{ codePopup.code }}</pre>
    </div>
    
    <!-- 调整宽度的拖拽手柄 -->
    <div class="resize-handle" @mousedown="startResize"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useAiStore } from '@/stores/AiStore';
import { marked } from 'marked';
import { useDataStore } from '@/stores/DataStore';
import { useColumnTypeStore } from '@/stores/ColumnTypeStore';
import { useMaskStore } from '@/stores/MaskStore';
import { useDataCellStore } from '@/stores/store/CellDataStore';

let maxRow = 0;
// 保存每个 explanation 对应的行列范围信息
const explanationRanges = ref<Record<string, { minRow: number; maxRow: number; minCol: number; maxCol: number }>>({});
const aiStore = useAiStore();
const dataStore = useDataStore();
const columnTypeStore = useColumnTypeStore();
const maskStore = useMaskStore();
const cellsStore = useDataCellStore(); 
const message = ref('');
const chatInputRef = ref<HTMLInputElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);
const isResizing = ref(false);
const minWidth = 300;
const apiIntent = ref('');
const apiMessage = ref('');
const apiExplanation = ref('');
const isLoading = ref(false);
const isPreviewMode = ref(false);
const previewResult = ref<{
  new_ids: number[],
  different_cells: string[],
  missing_ids: string[][]
} | null>(null);
const codePopup = ref<{ show: boolean; code: string; x: number; y: number; messageId?: number }>({
  show: false,
  code: '',
  x: 0,
  y: 0
});

let initialWidth = 0;
let initialX = 0;

// 消息类型定义
interface Message {
  id: number;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  code?: string;
  explanation?: string;
  chartUrl?: string;
}

// 消息列表
const messages = ref<Message[]>([]);
let messageId = 0;

// 从 localStorage 加载历史记录
const loadMessages = () => {
  try {
    const saved = localStorage.getItem('ai-chat-messages');
    if (saved) {
      const parsed = JSON.parse(saved);
      messages.value = (parsed.messages || []).map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
      messageId = parsed.nextId || 0;
    }
  } catch (error) {
    console.error('加载历史记录失败:', error);
  }
};

// 保存历史记录到 localStorage
const saveMessages = () => {
  try {
    const data = {
      messages: messages.value,
      nextId: messageId
    };
    localStorage.setItem('ai-chat-messages', JSON.stringify(data));
  } catch (error) {
    console.error('保存历史记录失败:', error);
  }
};

// 清除历史记录
const clearHistory = () => {
  try {
    localStorage.removeItem('ai-chat-messages');
    messages.value = [];
    messageId = 0;
  } catch (error) {
    console.error('清除历史记录失败:', error);
  }
};



// 解析 dataframe 数据为 cells 格式
const parseDataFrame = (data: string): Record<string, string> => {
  const cells: Record<string, string> = {};
  
  // 简单的解析逻辑，根据实际返回格式调整
  // 假设返回的是类似表格的文本格式
  const lines = data.split('\n');
  
  let headerColumns = 0; // 表头列数
  let dataRowStart = 0; // 数据行开始索引
  
  // 先处理表头，获取列数
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) {
      continue;
    }
    
    if (line.includes('---')) {
      // 找到表头分隔线，上一行是表头
      if (i > 0) {
        const headerLine = lines[i - 1];
        headerColumns = headerLine.split('chen').length;
      }
      dataRowStart = i + 1;
      break;
    }
  }
  
  // 处理数据行
  for (let rowIndex = dataRowStart; rowIndex < lines.length; rowIndex++) {
    const line = lines[rowIndex];
    if (!line.trim()) {
      continue;
    }
    
    // 分割单元格（按chen分割）
    const cellsInLine = line.split('chen');
    
    // 如果有表头，使用表头的列数作为最大列数
    const maxColumns = headerColumns > 0 ? headerColumns : cellsInLine.length;
    
    for (let colIndex = 0; colIndex < maxColumns; colIndex++) {
      // 转换为 1-based 索引
      const row = rowIndex - dataRowStart + 1;
      const col = colIndex + 1;
      // 只保存实际存在的值，不填充空格
      const cellValue = cellsInLine[colIndex];
      if (cellValue) {
        cells[`${row}-${col}`] = cellValue;
      }
    }
  }
  
  return cells;
};

// 对比 parsedCells 与原有的数据，找出差异
const compareDataWithOriginal = (parsedCells: Record<string, string>) => {
  // 结果字典
  const result = {
    different_cells: [] as string[],  // 不一样的单元格坐标
    missing_ids: [] as string[][],    // 原先行有的id但后面没有的行（嵌套数组）
    new_ids: [] as number[]           // 新出现的行
  };
  
  // 获取原有的所有行号
  const originalRows = new Set<number>();
  for (const key in dataStore.cells) {
    const parts = key.split('-');
    const row = parseInt(parts[0], 10);
    originalRows.add(row);
  }
  
  // 处理新数据：从最后一列获取行号，并建立行号到行索引的映射
  const newRowMap = new Map<number, number>(); // 行号 -> 行索引
  
  // 计算整个新数据的最大列数（从表头或数据行）
  let maxColumns = 0;
  for (const key in parsedCells) {
    const parts = key.split('-');
    const col = parseInt(parts[1], 10);
    if (col > maxColumns) {
      maxColumns = col;
    }
  }
  maxColumns = maxColumns;
  // 从每行的最后一列（统一的最大列数）获取行号
  const rows = new Set<number>();
  for (const key in parsedCells) {
    const parts = key.split('-');
    const rowIndex = parseInt(parts[0], 10);
    rows.add(rowIndex);
  }
  
  rows.forEach(rowIndex => {
    const lastCellKey = `${rowIndex}-${maxColumns}`;
    console.log(lastCellKey);
    
    const rowIdStr = parsedCells[lastCellKey] || '';
    const rowId = parseInt(rowIdStr, 10);
    
    if (!isNaN(rowId)) {
      newRowMap.set(rowId, rowIndex);
    } else {
      // 如果最后一列不是数字，回退到使用行索引
      newRowMap.set(rowIndex, rowIndex);
    }
  });
  
  // 获取新数据的所有行号
  const newRows = new Set<number>(newRowMap.keys());
  
  // 检查原有的id但后面没有的行
  originalRows.forEach(row => {
    // 跳过第一行（表头）
    if (row === 1) return;

    // 检查该行是否在新数据中存在
    if (!newRows.has(row)) {
      // 把该行的所有单元格数据封装成嵌套数组
      const rowData: string[] = [];
      for (const key in dataStore.cells) {
        
        
        const parts = key.split('-');
        const r = parseInt(parts[0], 10);
        const c = parseInt(parts[1], 10);
        if (r === row) {
          // 确保数组有足够的元素
          while (rowData.length < c) {
            rowData.push('');
          }
          rowData[c - 1] = dataStore.cells[key];
   
          
        }
      }
      
      
      result.missing_ids.push(rowData);
    }
  });
  console.log(originalRows);
  
  console.log(newRows);
  
  // 检查新出现的行
  newRows.forEach(rowId => {
    // 跳过第一行（表头）
    if (rowId === 1) return;
  
    
    // 检查该行是否在原有数据中存在
    if (!originalRows.has(rowId)) {
      // 获取新数据的行索引
      const newRowIndex = newRowMap.get(rowId);
      
      if (newRowIndex !== undefined) {
        result.new_ids.push(newRowIndex);
      }
    }
  });
  
  // 对比同行数据，找出不一样的单元格
  newRows.forEach(row => {
    // 跳过第一行（表头）
    if (row === 1) return;
    
    // 检查该行是否在原有数据中存在
    if (originalRows.has(row)) {
      // 获取新数据中该行的行索引
      const newRowIndex = newRowMap.get(row);
      if (newRowIndex !== undefined) {
        // 找出该行的所有列
        const cols = new Set<number>();
        
        // 收集原有数据的列
        for (const key in dataStore.cells) {
          const parts = key.split('-');
          const r = parseInt(parts[0], 10);
          const c = parseInt(parts[1], 10);
          if (r === row) {
            cols.add(c);
          }
        }
        
        // 收集新数据的列
        for (const key in parsedCells) {
          const parts = key.split('-');
          const r = parseInt(parts[0], 10);
          const c = parseInt(parts[1], 10);
          if (r === newRowIndex) {
            cols.add(c);
          }
        }
        
        // 对比每一列（跳过最后一列，即存储行号的列）
        cols.forEach(col => {
          // 跳过最后一列
          if (col === maxColumns) return;
          
          const originalKey = `${row}-${col}`;
          const newKey = `${newRowIndex}-${col}`;
          
          const originalValue = dataStore.cells[originalKey] || '';
          const newValue = parsedCells[newKey] || '';
          
          // 空格也视为空数据
          const isOriginalEmpty = originalValue.trim() === '';
          const isNewEmpty = newValue.trim() === '' || newValue === ' ';
          
          // 原数据为空，新数据是空格，认为无差异
          if (isOriginalEmpty && isNewEmpty) {
            return;
          }
          
          if (originalValue !== newValue) {
            result.different_cells.push(`${newRowIndex}-${col}`);
          }
        });
      }
    }
  });
  
  console.log('数据对比结果:', result);
  return result;
};

const sendMessage = async () => {
  dataStore.removeEmptyCells();
  console.log("列类型信息:", columnTypeStore.columnsWithType);
  if (message.value.trim()) {

    const userMessage: Message = {
      id: messageId++,
      content: message.value.trim(),
      sender: 'user',
      timestamp: new Date()
    };
    messages.value.push(userMessage);
    saveMessages();
    
    message.value = '';
    dataStore.dataChanged = 1;
    // 同步数据到后端
    await dataStore.syncToBackend();
    
    // 请求后端 /process 接口
    try {
      isLoading.value = true;
      const response = await fetch('http://localhost:8001/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userMessage.content }),
      });
      
      if (response.ok) {
          const result = await response.json();
          apiIntent.value = result.intent || '';
          apiMessage.value = result.message || '';
          apiExplanation.value = result.explanation || '';
          
          // 检查返回的 explanation 是否包含 dataframe 数据
          // 如果是，替换现有的 cells 数据
          if (result.explanation && typeof result.explanation === 'string') {
            console.log(result.intent);
            
            try {
              if (result.intent === 'modify'){
                // 备份旧数据（用于取消时恢复）
                dataStore.backupOldCells();
                console.log(dataStore.cells);
                
                // 解析 dataframe 数据
                const parsedCells = parseDataFrame(result.explanation);
                
                console.log('解析后的 cells:', parsedCells);
                console.log('原有的 cells:', dataStore.cells);
                
                // 对比数据差异
                const comparisonResult = compareDataWithOriginal(parsedCells);
                console.log('对比结果:', comparisonResult);
                
                // 删除 parsedCells 的最后一列
                let maxColumns = 0;
                for (const key in parsedCells) {
                  const parts = key.split('-');
                  const col = parseInt(parts[1], 10);
                  if (col > maxColumns) {
                    maxColumns = col;
                  }
                }
                console.log(maxColumns);
                
                for (const key in parsedCells) {
                  const parts = key.split('-');
                  const col = parseInt(parts[1], 10);
                  if (col === maxColumns) {
                    delete parsedCells[key];
                  }
                }
                delete parsedCells[`1-${maxColumns}`];
                
                // 清空旧数据
                dataStore.cells = {};
                // 把新数据放入 cells
                Object.keys(parsedCells).forEach(key => {
                  dataStore.cells[key] = parsedCells[key];
                });
                // 删除所有空格单元格
              

                // 设置新出现的行为高亮（绿色）
                dataStore.setHighlightedNewRows(comparisonResult.new_ids);

                // 设置不一样的单元格高亮（蓝色）
                dataStore.setHighlightedDiffCells(comparisonResult.different_cells);

                // 把丢失的行数据添加到表格最后，并标记为红色
                if (comparisonResult.missing_ids.length > 0) {
                  // 获取当前最大行号
                  let maxRow = 0;
                  for (const key in dataStore.cells) {
                    const parts = key.split('-');
                    const row = parseInt(parts[0], 10);
                    if (row > maxRow) maxRow = row;
                  }

                  // 记录添加的行的索引（用于标红）
                  const addedRowIndices: number[] = [];

                  // 添加丢失的行数据
                  comparisonResult.missing_ids.forEach((rowData, index) => {
                    const newRowIndex = maxRow + index + 1;
                    addedRowIndices.push(newRowIndex);
                    rowData.forEach((value, colIndex) => {
                      if (value) {
                        dataStore.setCellValue(newRowIndex, colIndex + 1, value, false, false, false);
                      }
                    });
                  });

                  // 设置删除的行高亮（红色）
                  dataStore.setHighlightedDeletedRows(addedRowIndices);
                  // 保存添加的行索引（确定时需删除）
                  dataStore.setAddedDeletedRows(addedRowIndices);
                  // 标记数据已更改
                  dataStore.dataChanged = 1;

                  // 进入预览模式，显示确定和取消按钮
                  isPreviewMode.value = true;
                  maskStore.isPreviewMode = true;
                }
              } else if (result.intent === 'report') {
                console.log('进入 report 分支');
                
                
                console.log('explanation:', result.explanation);
                const parsedCells = parseDataFrame(result.explanation);
                console.log('parsedCells:', parsedCells);
                // 计算当前 cellsStore 中的最大行号
                if (result.explanation !== '') {
                  for (const key in cellsStore.cells) {
                    const parts = key.split('-');
                    const row = parseInt(parts[0], 10);
                    if (row > maxRow) maxRow = row;
                  }
                }

                // 计算本次数据的行列范围
                let minRow = Infinity, maxRowLocal = 0, minCol = Infinity, maxCol = 0;
                Object.keys(parsedCells).forEach(key => {
                  const parts = key.split('-');
                  const row = parseInt(parts[0], 10);
                  const col = parseInt(parts[1], 10);
                  if (row < minRow) minRow = row;
                  if (row > maxRowLocal) maxRowLocal = row;
                  if (col < minCol) minCol = col;
                  if (col > maxCol) maxCol = col;
                });

                // 保存到字典中，以 explanation 为 key
                const range = {
                  minRow: minRow + maxRow + 2,
                  maxRow: maxRowLocal + maxRow + 2,
                  minCol: minCol + 1,
                  maxCol: maxCol + 1
                };
                explanationRanges.value[result.explanation] = range;
                console.log('保存的行列范围:', range);
                
                // 为范围添加边框
                cellsStore.saveState();
                const borderColor = 'rgb(14, 165, 233)';
                for (let row = range.minRow; row <= range.maxRow; row++) {
                  for (let col = range.minCol; col <= range.maxCol; col++) {
                    let border = '';
                    if (row === range.minRow) border += `border-top: 1px solid ${borderColor};`;
                    if (row === range.maxRow) border += `border-bottom: 1px solid ${borderColor};`;
                    if (col === range.minCol) border += `border-left: 1px solid ${borderColor};`;
                    if (col === range.maxCol) border += `border-right: 1px solid ${borderColor};`;
                    if (border) {
                      cellsStore.setCellStyle(row, col, border, false);
                    }
                  }
                }

                console.log('当前最大行号:', maxRow);
                cellsStore.$patch((state) => {
                  // 清空旧数据
                  Object.keys(parsedCells).forEach(key => {
                    const parts = key.split('-');
                    const row = parseInt(parts[0], 10);
                    const col = parseInt(parts[1], 10);
                    console.log(parsedCells[key]);
                    
                    console.log(row, col);
                    const newKey = `${row + maxRow + 2}-${col + 1}`;
                    state.cells[newKey] = parsedCells[key];
                  });
                });
                console.log('cellsStore.cells:', cellsStore.cells);
                console.log('CellDataStore.getCellValue(1,1):', cellsStore.getCellValue(1, 1));
                dataStore.dataChanged = 1;
              }
            } catch (error) {
              console.error('解析返回数据失败:', error);
            }
          }
          
          // 使用 message 创建 AI 消息
          const aiMessage: Message = {
            id: messageId++,
            content: result.message || '无回复',
            sender: 'ai',
            timestamp: new Date(),
            code: result.code || undefined,
            explanation: result.explanation || undefined,
            chartUrl: result.chart_url || undefined
          };
          messages.value.push(aiMessage);
          saveMessages();
        } else {
        throw new Error('请求失败');
      }
    } catch (error) {
      console.error('请求后端服务失败:', error);
      // 模拟 AI 回复（仅界面展示）
      const aiMessage: Message = {
        id: messageId++,
        content: '这是一个静态界面演示，未连接后端服务。',
        sender: 'ai',
        timestamp: new Date()
      };
      messages.value.push(aiMessage);
      saveMessages();
    } finally {
      isLoading.value = false;
    }
  }
};

const hide = () => {
  aiStore.hide();
};

const handleClickOutside = (e: MouseEvent) => {
  if (containerRef.value && chatInputRef.value && !containerRef.value.contains(e.target as Node)) {
    chatInputRef.value.blur();
  }
};

// 格式化时间
const formatTime = (date: Date) => {
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
};

// 预览模式：显示新数据
const showPreview = () => {
  isPreviewMode.value = true;
};

// 取消预览，恢复旧数据
const cancelPreview = () => {
  isPreviewMode.value = false;
  maskStore.isPreviewMode = false;
  dataStore.restoreOldCells();
  dataStore.clearHighlightedNewRows();
  dataStore.clearHighlightedDiffCells();
  dataStore.clearHighlightedDeletedRows();
  dataStore.clearAddedDeletedRows();
  previewResult.value = null;
};

// 确定替换，用新数据覆盖旧数据
const confirmPreview = () => {
  // 删除因missing_ids添加的行
  dataStore.deleteAddedDeletedRows();
  // 清除备份
  dataStore.oldCellsBackup = {};
  // 清除所有高亮状态
  dataStore.clearHighlightedNewRows();
  dataStore.clearHighlightedDiffCells();
  dataStore.clearHighlightedDeletedRows();
  isPreviewMode.value = false;
  maskStore.isPreviewMode = false;
  previewResult.value = null;
};

const handleMessageClick = (message: Message) => {
  // 查找该消息对应的行列范围
  if (message.explanation) {
    const range = explanationRanges.value[message.explanation];
    if (range) {
      // 设置该范围内的单元格背景为蓝色
      cellsStore.setRangeBackgroundColor(
        range.minRow,
        range.maxRow,
        range.minCol,
        range.maxCol,
        '#E6F7FF'
      );
    }
  }
};

const shade = () => {
};

const toggleCodePopup = (e: MouseEvent, code: string, messageId: number) => {
  // 阻止事件冒泡，避免触发其他点击事件
  e.stopPropagation();
  
  // 如果点击的是同一个消息，切换显示状态
  if (codePopup.value.messageId === messageId) {
    codePopup.value.show = !codePopup.value.show;
  } else {
    // 如果点击的是不同消息，显示新的弹出框
    codePopup.value.show = true;
  }
  
  if (codePopup.value.show) {
    codePopup.value.code = code;
    codePopup.value.messageId = messageId;
    codePopup.value.x = (e.target as HTMLElement).getBoundingClientRect().right + 10;
    codePopup.value.y = (e.target as HTMLElement).getBoundingClientRect().top;
  }
};

const hideCodePopup = () => {
  codePopup.value.show = false;
};

const startResize = (e: MouseEvent) => {
  e.preventDefault();
  const container = containerRef.value;
  if (container) {
    initialWidth = container.offsetWidth;
    initialX = e.clientX;
  }
  isResizing.value = true;
  document.body.style.cursor = 'ew-resize';
};

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return;
  
  const container = containerRef.value;
  if (!container) return;
  
  const deltaX = initialX - e.clientX;
  const newWidth = initialWidth + deltaX;
  
  if (newWidth >= minWidth) {
    container.style.width = `${newWidth}px`;
  }
};

const stopResize = () => {
  isResizing.value = false;
  document.body.style.cursor = 'default';
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  // 点击页面其他地方关闭code弹出框
  document.addEventListener('click', () => {
    codePopup.value.show = false;
  });
  // 加载历史记录
  loadMessages();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  // 移除全局点击事件监听器
  document.removeEventListener('click', () => {
    codePopup.value.show = false;
  });
});

const parseMarkdown = (text: string) => {
  if (!text) return '';
  // text = String(text);
  // console.log('Markdown文本:', text);
  
  const html = marked.parse(text);
  // console.log('解析后的HTML:', html);
  return html;
};
</script>

<style scoped>
.builder-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 350px;
  background: #ffffff;
  color: #333333;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  border: 1px solid #e0e0e0;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: transparent;
  border: none;
  color: #6b7280;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.close-icon {
  font-size: 18px;
  font-weight: bold;
  line-height: 1;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e0e0e0;
  overflow-y: auto;
}

.messages-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  margin: 0;
}

.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.builder-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-square {
  width: 60px;
  height: 60px;
  background: #ffffff;
  border: 2px solid #3b82f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo-dots {
  display: flex;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  background: #3b82f6;
  border-radius: 50%;
}

.builder-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #333333;
}

.builder-subtitle {
  font-size: 12px;
  color: #6b7280;
  max-width: 300px;
  margin: 0;
  line-height: 1.5;
}

.clear-history-btn {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #9ca3af;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
}

.clear-history-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.5);
  color: #ef4444;
}

.clear-history-btn svg {
  flex-shrink: 0;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.message-item {
  display: flex;
  margin: 0;
  width: auto;
  max-width: 100%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 13px;
  line-height: 1.4;
  /* display: inline-flex; */
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 100%;
}

.user-message .message-content {
  background: #3b82f6;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.ai-message .message-content {
  background: #ffffff;
  color: #333333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

/* 加载动画 */
.loading-message .message-content {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 20px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.text-with-code-hint {
  display: flex;
  align-items: center;
  flex: 0 1 auto;
  min-width: 0;
}

.message-text {
  user-select: text;
  flex: 0 1 auto;
  min-width: 0;
  word-wrap: break-word;
}

.message-time {
  font-size: 10px;
  opacity: 0.7;
  margin-top: 4px;
  text-align: right;
  width: 100%;
}

/* 图表容器 */
.chart-container {
  margin-top: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 图表图片 */
.chart-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

/* 聊天输入区域 */
.chat-input-area {
  background: #ffffff;
  padding: 12px;
}

.chat-input-container {
  background: #ffffff;
  border-radius: 6px;
  padding: 8px;
  border: 1px solid #d1d5db;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.chat-label {
  font-size: 11px;
  font-weight: 500;
  color: #333333;
}

.chat-status {
  font-size: 11px;
  color: #10b981;
}

.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-input {
  flex: 1;
  background: #ffffff;

  padding: 6px 10px;
  color: #333333;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
}

.chat-input:focus {
  border-color: #d1d5db;
  box-shadow: none;
}

.chat-input::placeholder {
  color: #9ca3af;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.divider {
  width: 1px;
  height: 18px;
  background: #d1d5db;
  margin: 0 2px;
}

.action-icon {
  background: transparent;
  border: none;
  color: #6b7280;
  padding: 3px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.action-icon:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.attachment-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-btn img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.send-btn {
  background: #3b82f6;
  border: none;
  color: #ffffff;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.send-btn:hover {
  background: #2563eb;
}

.send-icon {
  font-size: 12px;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {

  
  .builder-title {
    font-size: 16px;
  }
  
  .builder-subtitle {
    font-size: 11px;

  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
  }
  
  .logo-square {
    width: 45px;
    height: 45px;
  }
  
  .chat-input-area {
    padding: 10px;
  }
  
  .chat-input-container {
    padding: 6px;
  }
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: ew-resize;
  z-index: 20;
  background: transparent;
  transition: background 0.2s ease;
}

.resize-handle:hover {
  background: rgba(59, 130, 246, 0.2);
}

.resize-handle:active {
  background: rgba(59, 130, 246, 0.4);
}

/* Code 弹出框 */
.code-hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: #e5e7eb;
  color: #6b7280;
  border-radius: 50%;
  font-size: 11px;
  font-weight: bold;
  cursor: pointer;
  margin-left: 4px;
  vertical-align: middle;
  user-select: none;
  position: relative;
  top: -1px;
}

.code-hint:hover {
  background: #3b82f6;
  color: #ffffff;
}

.code-popup {
  position: fixed;
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-width: 400px;
  max-height: 300px;
  overflow: auto;
}

.code-popup pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Markdown 内容样式 - 使用 :deep() 穿透 scoped */
:deep(.message-text) h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 12px 0;
  color: #333333;
}

:deep(.message-text) h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 14px 0 10px 0;
  color: #333333;
}

:deep(.message-text) h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  color: #333333;
}
/* :deep(.message-text) p {
  margin: 8px 0;
  line-height: 1.6;
} */

:deep(.message-text) ul,
:deep(.message-text) ol {
  margin: 8px 0;
  padding-left: 20px;
}

:deep(.message-text) li {
  margin: 4px 0;
}

:deep(.message-text) code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

:deep(.message-text) pre {
  background: #f3f4f6;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

:deep(.message-text) pre code {
  background: transparent;
  padding: 0;
}

:deep(.message-text) strong {
  font-weight: 600;
  color: #1f2937;
}

:deep(.message-text) blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 12px;
  margin: 12px 0;
  color: #6b7280;
}

:deep(.message-text) table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

:deep(.message-text) th,
:deep(.message-text) td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

:deep(.message-text) th {
  background: #f9fafb;
  font-weight: 600;
}

/* 预览模式按钮 */
.preview-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 8px;
  background: #f9fafb;
  border-top: 1px solid #e0e0e0;
}

.preview-btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
}

.cancel-btn:hover {
  background: #f3f4f6;
}

.confirm-btn {
  background: #3b82f6;
  border: 1px solid #3b82f6;
  color: #ffffff;
}

.confirm-btn:hover {
  background: #2563eb;
}
</style>