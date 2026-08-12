<div align="center">

# 🌟 CosAI

### 智能电子表格 · AI 数据分析助手

[![Vue](https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-7.2-646cff?logo=vite)](https://vitejs.dev/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![pandasai](https://img.shields.io/badge/pandasai-AI%20Agent-blueviolet)](https://github.com/sinaptik-ai/pandas-ai)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一款集成 AI 大模型的高端电子表格 Web 应用，让数据处理与分析更智能。

[功能特性](#-功能特性) · [技术栈](#-技术栈) · [架构流程](#-架构流程) · [快速开始](#-快速开始) · [项目结构](#-项目结构) · [API 文档](#-api-文档)

</div>

---

## 📖 项目简介

CosAI 是一款面向数据分析场景的**智能电子表格 Web 应用**，在传统表格编辑能力之上，深度集成 AI 大模型，实现：

- 📊 **可视化表格编辑** —— 类 Excel 操作体验，支持单元格、行/列、选择、拖拽等完整编辑能力
- 🤖 **AI 数据分析助手** —— 自然语言对话即可完成数据修改、统计分析与图表生成
- 📁 **多格式数据导入导出** —— 支持 CSV 导入与图表渲染导出
- 🎨 **现代化 UI** —— 基于 TailwindCSS 4，界面美观、响应式适配

> **适合场景**：数据分析教学、个人/小团队数据处理、报表自动化、Python 数据科学辅助工具等。

---

## ✨ 功能特性

### 📝 电子表格编辑器

| 功能 | 描述 |
|------|------|
| 单元格编辑 | 支持双击/单击直接编辑单元格内容 |
| 行/列操作 | 动态插入、删除行/列 |
| 选择操作 | 多选、复制、粘贴、合并单元格 |
| 拖拽调整 | 拖拽调整行高与列宽 |
| 图表渲染 | 内置 ECharts 等图表组件，支持动态扩展 |
| 撤销/重做 | 完整的操作历史栈，支持任意回退 |

### 🤖 AI 数据分析助手（pandasai 驱动）

> **核心说明**：本模块所有数据处理与分析任务均通过 **pandasai** 实现，包括自然语言对话、自动代码生成、预处理工具链、描述性统计与图表生成——一个引擎搞定所有分析动作。

| 功能 | 描述 |
|------|------|
| 智能对话 | 通过自然语言与 AI 助手对话，**pandasai 自动转换为 Pandas 代码**执行 |
| 意图识别 | 自动判断用户意图（修改数据 / 生成报告 / 提问），路由到不同处理链路 |
| 数据预处理工具 | 内置多种预处理能力：<br>• 数据标准化（Standard Scaling）<br>• 归一化（MinMax Scaling）<br>• 异常值处理<br>• 缺失值填充<br>• 线性回归拟合 |
| 描述性统计 | pandasai 调用 Pandas 自动生成描述性统计报告 |
| 图表自动生成 | pandasai 调用 matplotlib 生成可视化图表并返回前端展示 |

### 📁 数据导入导出

- ✅ **CSV 导入**：支持导入标准 CSV 数据文件
- ✅ **图表导出**：支持将分析结果导出为图表

---

## 🛠️ 技术栈

### 前端
| 技术 | 用途 |
|------|------|
| **Vue 3** | 主框架（Composition API） |
| **TypeScript** | 类型系统 |
| **Pinia** | 状态管理（含持久化插件 pinia-plugin-persistedstate） |
| **Vue Router** | 路由管理 |
| **TailwindCSS 4** | 原子化样式 |
| **Vite 7** | 构建工具 |
| **Monaco Editor** | 代码编辑器 |
| **Element Plus Icons** | 图标库 |
| **clsx / tailwind-merge** | className 合并工具 |

### 后端
| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架，提供 RESTful API |
| **pandasai** | AI 数据分析核心引擎（自然语言 → 代码 → 执行） |
| **pandasai_litellm** | pandasai 的 LLM 适配层，统一多模型接入 |
| **langchain_core + langchain_litellm** | 意图识别链路（modify / report / question） |
| **大语言模型（LLM）** | 底层大模型，通过 LiteLLM 统一接入（支持多家主流厂商） |
| **Pandas + NumPy** | 数据处理（pandasai 调用） |
| **matplotlib** | 图表生成（pandasai 调用） |
| **Pydantic** | 数据校验 |
| **SQLite** | 对话历史持久化 |

---

## 🏗️ 架构流程

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  前端 (Vue 3)│         │  后端 (FastAPI)  │         │   大模型 (LLM)  │
│             │         │                  │         │                 │
│  表格编辑   │ ──────▶ │  api.py          │ ──────▶ │  大语言模型     │
│  Monaco代码 │   CSV   │   ├─ 意图识别     │   HTTP  │  (LLM)         │
│  ECharts    │ ◀────── │   ├─ pandasai    │ ◀────── │  (via LiteLLM)  │
│             │  Chart  │   ├─ matplotlib  │   Resp  │                 │
└─────────────┘         └──────────────────┘         └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  exports/    │
                       │  ├─ charts/  │  ← 生成的图表
                       │  ├─ data/    │  ← 导出数据
                       │  └─ logs/    │  ← pandasai 日志
                       └──────────────┘
```

**数据流向**：

1. 用户在前端表格编辑数据 → POST `/api/post-data` → 后端转为 Pandas DataFrame
2. 用户用自然语言提问 → POST `/process` → 意图识别路由 → 调用 **pandasai** 分析
3. pandasai 自动生成代码并执行（数据清洗、统计、可视化）
4. 结果返回前端：数据回填表格 + 图表 URL 展示

---

## 🛡️ 技术选型说明

> **📌 关于 AI 数据分析能力的实现方式**
>
> 本项目的**核心数据分析能力**（数据修改、报告生成）均基于开源框架 **[pandasai](https://github.com/sinaptik-ai/pandas-ai)** 实现，而非从零自研 AI 算法。
>
> pandasai 面向数据分析场景，将自然语言转换为 Python + Pandas 代码执行，能完成完整的数据分析任务：

### 🔍 pandasai 在 CosAI 中的实际应用

| 业务场景 | 用户自然语言示例 | 实现方式 |
|---------|----------------|---------|
| **数据修改（modify）** | "请帮我删除列中的重复值和缺失值并填充" | ✅ pandasai（生成去重 + 填充代码） |
| **数据转换** | "按销量降序排列，保存到 milk.csv" | ✅ pandasai（生成 sort + to_csv 代码） |
| **数据预处理** | "对销售额做标准化处理" | ✅ pandasai（生成 StandardScaler 代码） |
| **报告生成（report）** | "统计各城市销售总额，生成柱状图" | ✅ pandasai（生成聚合 + matplotlib 代码） |
| **异常值处理** | "检测并处理异常值" | ✅ pandasai |
| **回归分析** | "做线性回归拟合" | ✅ pandasai（生成 sklearn 代码） |
| **业务问答（question）** | "哪款奶茶销量最高？" | ⚙️ 直接调 LLM（不走 pandasai） |

### 🔧 在此基础上，本人完成的工程化工作

| 工作内容 | 说明 |
|---------|------|
| 🔧 **AI 引擎集成** | 通过 `pandasai_litellm` + LiteLLM 统一接入大语言模型（支持多家厂商） |
| 🧭 **意图识别路由** | 基于 `langchain_core` + Pydantic 实现 modify / report / question 三分类 |
| 🔌 **前后端打通** | FastAPI + Vue 联动，实现表格 ↔ DataFrame ↔ CSV 双向流转 |
| 📊 **可视化闭环** | pandasai 生成的 matplotlib 图表自动暴露为静态资源，前端 ECharts 渲染 |
| 💾 **历史持久化** | 基于 SQLite 存储多轮对话上下文（pandasai history_dir） |
| 📝 **可审计的代码** | 每次 AI 操作都返回 `last_code_executed`，方便问题追溯 |

### 💡 架构亮点

```
用户输入自然语言
       ↓
  [意图识别]  →  modify / report / question
       ↓              ↓                ↓
  pandasai 引擎    pandasai 引擎     直接调 LLM
  (数据修改)      (统计+可视化)      (业务问答)
       ↓              ↓                ↓
  返回修改结果    返回图表 URL        返回文本回答
```

> 这是一种 **"站在巨人肩膀上"** 的工程实践：把成熟的 AI Agent 框架（pandasai）与 Web 全栈技术结合，让 AI 真正落地到具体业务场景中。

---

## 🚀 快速开始

### 环境要求

- **Node.js** >= 18
- **Python** >= 3.9
- 大模型 API Key（支持任意主流厂商，前往对应平台申请即可）

### 1. 克隆仓库

```bash
git clone https://github.com/Clannadgh/cosai.git
cd cosai
```

### 2. 前端启动

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行于：**http://localhost:5173**

### 3. 后端启动

```bash
# 进入后端目录
cd cosai

# 安装 Python 依赖
pip install -r requirements.txt

# 启动 FastAPI 服务
python api.py
```

后端运行于：**http://localhost:8001**

### 4. 配置 API Key

当前版本 API Key 硬编码于 `cosai/api.py` 中。生产环境建议改为环境变量读取：

```env
# 在项目根目录创建 .env 文件
DASHSCOPE_API_KEY=your_api_key_here
```

---

## 📁 项目结构

```
cosai/
├── src/                        # 前端源码
│   ├── components/             # Vue 公共组件
│   │   └── Table/              # 表格核心组件（Cell, ColumnHeader, RowHeader 等）
│   ├── views/                  # 页面视图
│   ├── stores/                 # Pinia 状态管理
│   ├── router/                 # 路由配置
│   ├── utils/                  # 工具函数
│   ├── App.vue                 # 根组件
│   ├── main.ts                 # 入口文件
│   └── index.css               # 全局样式
│
├── cosai/                      # 后端源码
│   ├── api.py                  # FastAPI 主服务（核心入口）
│   ├── 1.py / 2.py             # 实验性脚本（意图识别 + pandasai 测试）
│   ├── import_data_to_db.py    # 数据导入工具
│   ├── 奶茶店每日订单.csv      # 测试数据
│   ├── milk.csv / baogao.csv   # 数据样本
│   ├── exports/                # 导出目录
│   │   ├── charts/             # AI 生成的图表
│   │   ├── data/               # 导出数据
│   │   └── logs/               # 运行日志
│   ├── pandasai_history/       # pandasai 对话历史
│   └── *.db                    # SQLite 数据库
│
├── public/                     # 前端静态资源
├── index.html                  # HTML 入口
├── package.json                # 前端依赖配置
├── vite.config.js              # Vite 构建配置
├── tsconfig.json               # TS 配置
└── README.md                   # 项目说明（本文件）
```

---

## 📡 API 文档

后端服务运行后，可访问 **http://localhost:8001/docs** 查看完整的 Swagger API 文档。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径，返回欢迎信息 |
| `/api/post-data` | POST | 接收前端表格数据 |
| `/api/get-data` | GET | 获取当前数据 |
| `/process` | POST | AI 数据分析处理（核心接口） |
| `/charts/*` | GET | 静态访问生成的图表 |

---

## 🧠 为什么选择 pandasai？

### 📌 什么是 pandasai？

[pandasai](https://github.com/sinaptik-ai/pandas-ai) 是面向数据分析场景的 **AI Agent 库**，将自然语言转换为 Python + Pandas 代码执行，让数据分析和处理变得像"说话"一样自然。

```python
# 传统方式：写代码
df.groupby('城市')['销售额'].sum().sort_values(ascending=False).head(5)

# pandasai 方式：说人话
df.chat("哪个城市的销售额最高？前五名")
```

### 🎯 pandasai 核心优势

| 优势 | 说明 |
|------|------|
| **🔄 一站式分析引擎** | 数据清洗、统计、回归、可视化，一个库全包 |
| **📝 自然语言交互** | 用户无需写代码，用中文即可完成数据分析 |
| **🔍 可审计的代码生成** | 每次 AI 操作都返回 `last_code_executed`，方便问题追溯 |
| **📊 自动可视化** | 原生支持 matplotlib，自动保存图表 |
| **🔌 多模型适配** | 通过 LiteLLM 无缝接入多种大模型 |
| **💾 上下文持久化** | 内置历史记录支持（SQLite 存储） |

### 🌟 为什么不直接调 LLM API？

| 方案 | 劣势 |
|------|------|
| 直接调 LLM API | 缺少代码执行环境，无法处理真实数据 |
| LangChain Agent 自接 | 配置复杂，需自己拼接 DataFrame 工具链 |
| 自研 AI + Pandas | 开发周期长，难以保证代码执行稳定性 |
| **pandasai** ✅ | **封装完整 + 自动代码生成 + 可审计 + 多模型适配** |

---

## 🎯 项目亮点

- ✅ **真实落地** —— AI 助手可基于自然语言完成完整的数据预处理与可视化
- ✅ **前沿技术** —— 使用 pandasai AI Agent 框架 + 最新 Vue 3 + TypeScript 全栈
- ✅ **工程化规范** —— ESLint、Vite 7 单文件打包、Pinia 持久化、类型安全
- ✅ **可视化能力** —— 前端 Monaco Editor + 表格内嵌 ECharts 图表
- ✅ **意图路由** —— langchain + pandasai 分层架构，不同意图走不同处理链路

---

## 🛣️ Roadmap

- [ ] 接入更多大模型（GPT-4 / Claude / DeepSeek）
- [ ] 支持更多文件格式（Excel / JSON / Parquet）
- [ ] 多人协作编辑（WebSocket 实时同步）
- [ ] AI 工具自定义配置（可视化工具编排）
- [ ] 用户系统与历史对话云端持久化
- [ ] 将硬编码 API Key 改造为环境变量配置

---

## 🤝 贡献

欢迎提交 Issue 与 PR！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

---

## 📄 开源协议

本项目基于 [MIT](LICENSE) 协议开源。

---

## 👤 作者

**Clannadgh** — [GitHub](https://github.com/Clannadgh)

> 如果这个项目对你有帮助，欢迎 ⭐ Star 支持一下！
