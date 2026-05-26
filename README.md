# CosAI - 在线电子表格 + AI 数据分析助手

一个功能强大的在线电子表格应用，集成 AI 智能数据分析能力。

## 功能特性

### 电子表格编辑器
- **单元格编辑** - 支持双击/输入直接编辑单元格内容
- **行列操作** - 动态插入、删除行/列
- **选中操作** - 多选区复制、粘贴、剪切
- **表格调整** - 拖拽调整行高和列宽
- **虚拟滚动** - 大表格高效渲染，支持动态扩展
- **撤销/重做** - 支持操作历史回退

### AI 数据分析助手
- **智能对话** - 通过侧边栏与 AI 助手对话
- **意图识别** - 自动分类用户意图（数据问答、特定分析工具请求、寒暄等）
- **数据分析工具** - 支持多种数据分析预处理工具：
  - 标准化 (Standard Scaling)
  - 归一化 (MinMax Scaling)
  - 异常值处理
  - 缺失值填充
  - 线性回归分析
- **描述性统计** - 自动生成数据统计报告

### 数据导入导出
- **CSV 导入** - 支持导入 CSV 数据文件
- **图表导出** - 支持将分析结果图表导出

## 技术栈

### 前端
- Vue 3 + Composition API
- TypeScript
- Pinia (状态管理)
- Vue Router
- TailwindCSS 4
- Vite

### 后端
- FastAPI
- LangChain
- ChatTongyi (通义千问)
- Pandas + scikit-learn
- SQLite (聊天记录存储)

## 环境要求

- **Node.js** >= 18
- **Python** >= 3.9
- **DASHSCOPE_API_KEY** - 通义千问 API 密钥

## 本地开发

### 1. 克隆仓库
```bash
git clone https://github.com/Clannadgh/cosai.git
cd cosai
```

### 2. 前端 setup
```bash
npm install
npm run dev
```
前端服务启动于 http://localhost:5173

### 3. 后端 setup
```bash
cd cosai
pip install -r requirements.txt
python main.py
```
后端服务启动于 http://localhost:8001

### 4. 配置环境变量
在项目根目录创建 `.env` 文件：
```
DASHSCOPE_API_KEY=你的通义千问API密钥
```

## 项目结构

```
├── src/                    # 前端源码
│   ├── components/         # Vue 组件
│   │   └── Table/         # 表格相关组件
│   ├── views/             # 页面视图
│   ├── stores/            # Pinia 状态管理
│   └── utils/             # 工具函数
├── cosai/                  # 后端源码
│   ├── tools/             # AI 分析工具
│   ├── tongyi_chat.py     # 通义千问集成
│   └── main.py            # FastAPI 主入口
└── public/                # 静态资源
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/post-data` | POST | 接收前端表格数据 |
| `/api/chat` | POST | 主对话入口 |
| `/api/select` | POST | 获取工具参数建议 |
| `/api/confirm-scenario` | POST | 确认分析场景 |
| `/api/run-description` | POST | 运行描述性统计 |

## 许可证

MIT