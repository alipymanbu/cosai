# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

一个**在线电子表格 + AI 数据分析助手**应用。前端 Vue 3 表格编辑器，后端 FastAPI + LangChain 对接通义千问模型实现智能数据分析。

## 环境配置

每次执行命令前先切换 UTF-8 编码：
```powershell
powershell -Command "chcp 65001"
```

## 常用命令

**前端**
```powershell
npm run dev    # 启动开发服务器 (Vite, port 5173)
npm run build  # 构建生产版本
```

**后端**
```powershell
python cosai/main.py  # 启动 FastAPI (port 8001, reload=True)
```

## 技术栈

- **前端**: Vue 3 + TypeScript + Pinia + TailwindCSS 4 + Vite + Vue Router
- **后端**: FastAPI + LangChain + ChatTongyi (通义千问)
- **数据库**: SQLite (`cosai/chat_history.db`)
- **AI 工具**: scikit-learn 数据预处理、线性回归

## 架构

### 前端 (src/)

| 路径 | 职责 |
|------|------|
| `views/Spreadsheet.vue` | 表格主页，工具栏 + 单元格渲染 + AI 侧边栏 |
| `components/Table/tabl/` | 核心表格组件 (Cell, ColumnHeader, RowHeader, SelectionOverlay 等) |
| `stores/DataStore.ts` | 单元格数据 + undo/redo 历史记录 |
| `stores/RowColumn.ts` | 行列数量、宽高管理 |
| `stores/store/SelectionStore.ts` | 选区状态管理 |

表格采用虚拟滚动，行/列动态扩展。单元格 key 格式为 `{row}-{col}`。

### 后端 (cosai/)

| 路径 | 职责 |
|------|------|
| `main.py` | FastAPI 主入口，4 个核心端点：`/api/chat`、`/api/select`、`/api/confirm-scenario`、`/api/run-description` |
| `llm_chat.py` | 创建 ChatTongyi 模型实例 |
| `tongyi_chat.py` | 意图分类 (`classify_user_intent`) 和工具匹配 (`process_specific_analysis_request`) |
| `tools/main.py` | 动态加载 `cosai/tools/` 下所有 .py 文件中的函数作为白名单工具 |
| `tools/data_preprocessing_tools.py` | 6 个数据预处理工具 (standard_scaling, minmax_scaling, handle_outliers 等) |
| `data_descriptive.py` | 描述性统计分析 |
| `Ai_advice.py` | 生成参数建议 |

### 意图分类 (intent_type)

| 值 | 含义 |
|---|------|
| 1 | 需要特定分析工具 |
| 2/3 | 数据分析问答 |
| 4 | 寒暄 |

### API 设计

- `POST /api/post-data` — 接收前端表格数据
- `POST /api/chat` — 主对话入口，意图分类后路由
- `POST /api/select` — 获取工具参数建议
- `POST /api/confirm-scenario` — 确认分析场景，AI 判断是否需要预处理
- `POST /api/run-description` — 运行描述性统计

## 数据库

`chat_history.db` (SQLite) 存储聊天记录，表结构：
```sql
CREATE TABLE chat_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,       -- 'user' 或 'assistant'
  content TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 注意事项

- `cosai/llm_chat.py` 中硬编码了 DASHSCOPE_API_KEY，需保持有效
- 后端全局变量 `df` 在多个端点间共享状态
- `cosai/tools/` 下工具通过动态 import 加载，无需手动注册
