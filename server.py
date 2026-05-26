from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from typing import Dict, Optional


import pandas as pd
import os
import json
import csv
import numpy as np
from datetime import datetime
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()
app = FastAPI(
    title="FastAPI 服务器",
    version="1.0.0",
)

origins = [
    # 开发环境：允许前端本地调试的地址（根据自己的前端端口修改）
    "http://localhost:5173",  # Vue3 Vite 默认端口
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # 新增：前端应用端口
    "http://localhost:5175",  # 设置页面端口
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许跨域的源（前端地址）
    allow_credentials=True,  # 允许前端携带 Cookie/认证信息（关键！）
    allow_methods=["*"],     # 允许所有 HTTP 方法（GET/POST/PUT/DELETE 等）
    allow_headers=["*"],     # 允许所有请求头（如 Authorization、Content-Type 等）
    # 可选：暴露自定义响应头给前端（默认只暴露简单头，如 Content-Type）
    # expose_headers=["X-Custom-Header"],
)

# ============================================
# 数据表格相关接口
# ============================================

@app.post("/api/post-data")
async def post_data(data:Dict[str, str]):
    global df
    print("12")
    df = to_dataframe(data)



# 接口 1：返回简单 JSON（直接返回字典）
@app.get("/api/get-data")
async def get_data():
    if 'df' in globals():
        # 处理NaN值，转换为空格
        df_clean = df.replace({np.nan: ''})
        return df_clean.to_dict()
    else:
        return {}  # FastAPI 自动转为 JSON







# ============================================
# 从 Python 目录生成 Vue 组件
# ============================================

def scan_python_directory(base_dir: str) -> dict:
    """
    扫描 Python 目录结构，提取菜单配置
    """
    structure = {
        'componentName': os.path.basename(base_dir),
        'menus': []
    }
    
    # 遍历目录
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        
        # 跳过非目录和特殊文件
        if not os.path.isdir(item_path) or item.startswith('__'):
            continue
        
        # 检查是否有 .py 文件
        py_files = []
        for file in os.listdir(item_path):
            if file.endswith('.py') and file != '__init__.py':
                # 去掉 .py 后缀
                file_name = file[:-3]
                py_files.append(file_name)
        
        if py_files:
            menu = {
                'label': item,
                'items': []
            }
            
            # 检查是否有子目录
            sub_dirs = []
            for sub_item in os.listdir(item_path):
                sub_path = os.path.join(item_path, sub_item)
                if os.path.isdir(sub_path) and not sub_item.startswith('__'):
                    sub_dirs.append(sub_item)
            
            if sub_dirs:
                # 有子目录，按子目录分组
                menu['categories'] = []
                for sub_dir in sub_dirs:
                    sub_path = os.path.join(item_path, sub_dir)
                    sub_py_files = []
                    
                    for file in os.listdir(sub_path):
                        if file.endswith('.py') and file != '__init__.py':
                            file_name = file[:-3]
                            sub_py_files.append(file_name)
                    
                    if sub_py_files:
                        menu['categories'].append({
                            'title': sub_dir,
                            'items': [{'label': label} for label in sub_py_files]
                        })
            else:
                # 没有子目录，直接添加文件
                menu['items'] = [{'label': label} for label in py_files]
            
            structure['menus'].append(menu)
    
    return structure


def generate_menu_config_json(structure: dict) -> str:
    """
    生成 menu-config.json 内容
    """
    return json.dumps(structure, indent=2, ensure_ascii=False)


def generate_vue_component(structure: dict) -> str:
    """
    根据结构生成 Vue 组件
    """
    vue_template = '''<template>
  <div class="top-nav-content" ref="navRef">
    <div class="menu-bar">
      <div 
        v-for="(menu, menuIndex) in menus" 
        :key="menuIndex"
        class="menu-item"
      >
        <div 
          class="menu-label"
          :class="{ active: activeMenu === menu.label }"
          @click="toggleMenu(menu.label)"
        >
          <span>{{ menu.label }}</span>
          <span class="arrow" :class="{ down: activeMenu === menu.label }">▶</span>
        </div>
        
        <div 
          class="dropdown"
          v-show="activeMenu === menu.label"
          @wheel.stop="handleWheel"
        >
          <template v-if="menu.categories">
            <div 
              v-for="(category, catIndex) in menu.categories" 
              :key="catIndex"
              class="category"
            >
              <div class="category-title">{{ category.title }}</div>
              <div class="section-items">
                <div 
                  v-for="(item, itemIndex) in category.items" 
                  :key="itemIndex"
                  class="menu-option"
                  @click="callHandler(menu.label, item.label)"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>
          </template>
          
          <template v-else>
            <div class="section-items flat">
              <div 
                v-for="(item, itemIndex) in menu.items" 
                :key="itemIndex"
                class="menu-option"
                @click="callHandler(menu.label, item.label)"
              >
                {{ item.label }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue';
import { useAiStore } from '@/stores/AiStore';

const aiStore = useAiStore();
const activeMenu = ref<string | null>(null);
const navRef = ref<HTMLElement | null>(null);

const menus = '''
    
    # 添加 menus 数据
    menus_json = json.dumps(structure['menus'], ensure_ascii=False)
    
    vue_script = f'''{vue_template}{menus_json}

const toggleMenu = (menu: string) => {{
  activeMenu.value = activeMenu.value === menu ? null : menu
}}

const closeMenu = () => {{
  activeMenu.value = null
}}

const handleClickOutside = (e: MouseEvent) => {{
  if (navRef.value && !navRef.value.contains(e.target as Node)) {{
    closeMenu()
  }}
}}

const handleScroll = (e: Event) => {{
  const target = e.target as HTMLElement
  const dropdown = navRef.value?.querySelector('.dropdown')
  if (dropdown && (dropdown === target || dropdown.contains(target))) {{
    return
  }}
  closeMenu()
}}

const handleInput = () => {{
  closeMenu()
}}

const handleWheel = (e: WheelEvent) => {{
  const target = e.currentTarget as HTMLElement
  const isScrollingUp = e.deltaY < 0
  const isScrollingDown = e.deltaY > 0
  const isAtTop = target.scrollTop === 0
  const isAtBottom = target.scrollTop + target.clientHeight >= target.scrollHeight
  
  if ((isScrollingUp && isAtTop) || (isScrollingDown && isAtBottom)) {{
    e.preventDefault()
  }}
}}

const callHandler = async (menuLabel: string, itemLabel: string) => {{
  console.log(`调用：${{menuLabel}} - ${{itemLabel}}`)
  
  try {{
    const response = await fetch('http://localhost:8000/api/execute', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        module: menuLabel,
        function: itemLabel,
        data: aiStore.tableData
      }})
    }})
    
    const result = await response.json()
    console.log('执行结果:', result)
  }} catch (error) {{
    console.error('执行失败:', error)
  }}
}}

onBeforeUnmount(() => {{
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScroll, true)
  document.removeEventListener('input', handleInput, true)
}})
</script>

<style scoped lang="scss">
.top-nav-content {{
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  user-select: none;
}}

.menu-bar {{
  display: flex;
  align-items: center;
  gap: 16px;
}}

.menu-item {{
  position: relative;
  display: flex;
  align-items: center;
}}

.menu-label {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}}

.menu-label:hover,
.menu-label.active {{
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}}

.arrow {{
  font-size: 10px;
  transition: transform 0.2s ease;
}}

.arrow.down {{
  transform: rotate(90deg);
}}

.dropdown {{
  position: absolute;
  top: calc(100%);
  left: -8px;    
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  min-width: 320px;
  max-height: 500px;
  overflow-y: auto;
  z-index: 1000;
  padding: 16px;
  animation: fadeIn 0.15s ease;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(-4px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.category {{
  margin-bottom: 12px;
}}

.category:last-child {{
  margin-bottom: 0;
}}

.category-title {{
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding: 8px 0;
  border-bottom: 2px solid #3b82f6;
  margin-bottom: 12px;
}}

.category-content {{
  display: flex;
  flex-direction: column;
  gap: 12px;
}}

.section {{
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px 12px;
}}

.section-title {{
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}}

.section-items {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}

.section-items.flat {{
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px 12px;
}}

.menu-option {{
  padding: 6px 12px;
  font-size: 12px;
  color: #444;
  cursor: pointer;
  border-radius: 4px;
  background: #fff;
  border: 1px solid #e0e0e0;
  transition: all 0.15s ease;
  white-space: nowrap;
}}

.menu-option:hover {{
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}}

.divider {{
  height: 1px;
  background: #e0e0e0;
  margin: 16px 0;
}}
</style>
'''
    
    return vue_script


@app.post("/api/scan-and-generate")
async def scan_and_generate(request: Request):
    """
    扫描 Python 目录结构，自动生成 menu-config.json 和 index.vue
    """
    try:
        data = await request.json()
        component_name = data.get('componentName', '')
        
        if not component_name:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': '组件名不能为空'}
            )
        
        # 组件目录路径
        component_dir = os.path.join(TARGET_DIR, component_name)
        
        if not os.path.exists(component_dir):
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': f'组件 {component_name} 不存在'}
            )
        
        # 1. 扫描目录结构
        structure = scan_python_directory(component_dir)
        
        # 2. 生成 menu-config.json
        config_json = generate_menu_config_json(structure)
        config_path = os.path.join(component_dir, 'menu-config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_json)
        
        # 3. 生成 index.vue
        vue_content = generate_vue_component(structure)
        vue_path = os.path.join(component_dir, 'index.vue')
        with open(vue_path, 'w', encoding='utf-8') as f:
            f.write(vue_content)
        
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': '生成成功',
                'structure': structure,
                'configPath': config_path,
                'vuePath': vue_path
            }
        )
        
    except Exception as e:
        print(f"生成失败：{str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


@app.post("/api/execute")
async def execute_function(request: Request):
    """
    执行 Python 函数
    """
    try:
        data = await request.json()
        module_name = data.get('module', '')
        function_name = data.get('function', '')
        data_input = data.get('data', [])
        
        if not module_name or not function_name:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': '模块名和函数名不能为空'}
            )
        
        # 动态导入模块
        module_path = f"src.components.ToolsNavs.数据分析.{module_name}.{function_name}"
        module = importlib.import_module(module_path)
        
        # 获取函数
        func = getattr(module, function_name)
        
        # 转换数据为 DataFrame
        df = pd.DataFrame(data_input)
        
        # 执行函数
        result = func(df)
        
        # 处理NaN值，转换为空格
        if hasattr(result, 'to_dict'):
            result_clean = result.replace({np.nan: ''})
            result_data = result_clean.to_dict('records')
        else:
            result_data = result
        
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'data': result_data
            }
        )
        
    except Exception as e:
        print(f"执行失败：{str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


@app.get("/api/components")
async def get_components():
    """获取已创建的组件列表"""
    try:
        if not os.path.exists(TARGET_DIR):
            return JSONResponse(
                status_code=200,
                content={'components': []}
            )
        
        # 获取所有包含 index.vue 的文件夹
        components = []
        for item in os.listdir(TARGET_DIR):
            item_path = os.path.join(TARGET_DIR, item)
            if os.path.isdir(item_path):
                index_file = os.path.join(item_path, 'index.vue')
                if os.path.exists(index_file):
                    components.append(item)
        
        return JSONResponse(
            status_code=200,
            content={'components': components}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.post("/api/rename-component")
async def rename_component(request: Request):
    """重命名组件文件"""
    try:
        import shutil
        
        data = await request.json()
        old_component_name = data.get('oldComponentName', '')
        new_component_name = data.get('newComponentName', '')
        new_name = data.get('newName', '')
        
        print(f"重命名请求：{old_component_name} -> {new_component_name}, 新名称：{new_name}")
        
        if not old_component_name or not new_component_name:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': '组件名不能为空'}
            )
        
        # 生成文件夹路径（使用绝对路径）
        old_folder_path = os.path.abspath(os.path.join(TARGET_DIR, old_component_name))
        new_folder_path = os.path.abspath(os.path.join(TARGET_DIR, new_component_name))
        
        print(f"旧路径：{old_folder_path}")
        print(f"新路径：{new_folder_path}")
        
        # 检查旧文件夹是否存在
        if not os.path.exists(old_folder_path):
            return JSONResponse(
                status_code=400,
                content={
                    'success': False, 
                    'error': f'组件 {old_component_name} 不存在'
                }
            )
        
        # 检查新文件夹是否已存在
        if os.path.exists(new_folder_path) and old_folder_path != new_folder_path:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False, 
                    'error': f'组件 {new_component_name} 已存在'
                }
            )
        
        # 使用 shutil.move 代替 os.rename（更健壮，支持跨分区移动）
        shutil.move(old_folder_path, new_folder_path)
        
        print(f"重命名成功：{old_component_name}/ -> {new_component_name}/")
        
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': f'组件重命名成功',
                'newComponentName': new_component_name,
                'newName': new_name
            }
        )
        
    except Exception as e:
        print(f"重命名失败：{str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


# ============================================
# 文件导入 / 导出接口
# ============================================

import tempfile, shutil

@app.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """导入 Excel / CSV 文件，支持编码、分隔符、标题行选项
    
    支持两种请求格式：
    1. FormData 格式：file + data (JSON)
    2. JSON 格式：settings { hasHeader, encoding, delimiter, quotechar, sheetIndex }
    """
    try:
        # 尝试解析 JSON 设置
        settings = {}
        preview_mode = False
        
        # 先尝试从 FormData 解析
        try:
            form = await request.form()
            if 'data' in form:
                # 新的请求格式：data 字段包含 JSON
                data_field = form['data']
                if data_field:
                    json_data = json.loads(await data_field.read() if hasattr(data_field, 'read') else str(data_field))
                    settings = json_data.get('settings', {})
                    preview_mode = json_data.get('preview', False)
            elif 'settings' in form:
                # 旧的请求格式：settings 字段
                settings_field = form['settings']
                if settings_field:
                    settings_str = await settings_field.read() if hasattr(settings_field, 'read') else str(settings_field)
                    settings = json.loads(settings_str)
                preview_mode = form.get('preview', 'false').lower() == 'true'
        except Exception as e:
            print(f"   解析 FormData 失败：{e}")
            pass
        
        # 如果 FormData 没有，尝试从 body 解析 JSON
        if not settings:
            try:
                body = await request.body()
                if body:
                    try:
                        json_data = json.loads(body.decode('utf-8'))
                        settings = json_data.get('settings', {})
                        preview_mode = json_data.get('preview', False)
                    except:
                        pass
            except:
                pass
        
        # 从 settings 获取参数
        hasHeader_str = settings.get('hasHeader', 'true')
        hasHeader = hasHeader_str.lower() in ("true", "1", "yes") if isinstance(hasHeader_str, str) else bool(hasHeader_str)
        encoding = settings.get('encoding', 'utf-8')
        delimiter = settings.get('delimiter', ',')
        quotechar = settings.get('quotechar', '"')
        sheetIndex = settings.get('sheetIndex', 0)
        
        # 处理转义分隔符
        delim = delimiter.replace("\\t", "\t")
        
        print(f"📥 上传文件：{file.filename}")
        print(f"   预览模式：{preview_mode}")
        print(f"   标题行：{hasHeader}")
        print(f"   编码：{encoding}")
        print(f"   分隔符：{repr(delim)}")
        print(f"   文本限定符：{quotechar}")
        print(f"   Excel 工作表索引：{sheetIndex}")

        # 保存到临时文件
        suffix = os.path.splitext(file.filename or "data.csv")[1] or ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if suffix.lower() in (".xlsx", ".xls"):
                # Excel 文件
                print(f"   📊 处理 Excel 文件...")
                
                # Excel 文件不需要编码处理，直接设置默认值
                encoding_used = encoding
                encoding_fallback = False
                
                # 获取所有工作表名称（使用后立即关闭）
                excel_file = pd.ExcelFile(tmp_path)
                sheets = excel_file.sheet_names
                excel_file.close()  # 立即关闭文件
                
                # 确保 sheetIndex 有效
                if sheetIndex >= len(sheets):
                    sheetIndex = 0
                
                sheet_name = sheets[sheetIndex] if len(sheets) > 0 else 0
                print(f"   使用工作表：{sheet_name}")
                
                if preview_mode:
                    # 预览模式：只读取前 10 行
                    df = pd.read_excel(tmp_path, sheet_name=sheet_name, header=0 if hasHeader else None, nrows=10)
                else:
                    df = pd.read_excel(tmp_path, sheet_name=sheet_name, header=0 if hasHeader else None)
                
            else:
                # CSV / TSV / 其他文本分隔
                print(f"   📄 处理 CSV 文件...")
                
                # 直接使用用户选择的分隔符
                quotechar_val = quotechar if quotechar else None
                print(f"   使用分隔符：{repr(delim)}, 文本限定符：{quotechar_val}")
                
                # 如果 quotechar 为空，需要设置 quoting=csv.QUOTE_NONE
                quoting_val = csv.QUOTE_NONE if not quotechar else csv.QUOTE_MINIMAL
                
                # 尝试用用户选择的编码读取，失败则自动降级
                encoding_used = encoding
                encoding_fallback = False
                
                try:
                    if preview_mode:
                        df = pd.read_csv(tmp_path, encoding=encoding, sep=delim, 
                                         header=0 if hasHeader else None, engine="python", nrows=10,
                                         quotechar=quotechar_val if quotechar else '"',
                                         quoting=quoting_val)
                    else:
                        df = pd.read_csv(tmp_path, encoding=encoding, sep=delim,
                                         header=0 if hasHeader else None, engine="python",
                                         quotechar=quotechar_val if quotechar else '"',
                                         quoting=quoting_val)
                except pd.errors.ParserError as e:
                    # CSV 解析失败（可能是分隔符不匹配）
                    print(f"   ❌ CSV 解析失败：{str(e)}")
                    print(f"   使用的分隔符：{repr(delim)}")
                    raise Exception(f"无法使用分隔符 '{delimiter}' 解析文件，请尝试其他分隔符。详细信息：{str(e)}")
                except UnicodeDecodeError:
                    # 编码失败，尝试使用 latin1（几乎不会失败）
                    print(f"   ⚠️ {encoding} 编码失败，尝试使用 latin1 编码...")
                    encoding_used = 'latin1'
                    encoding_fallback = True
                    
                    if preview_mode:
                        df = pd.read_csv(tmp_path, encoding='latin1', sep=delim, 
                                         header=0 if hasHeader else None, engine="python", nrows=10,
                                         quotechar=quotechar_val if quotechar else '"',
                                         quoting=quoting_val)
                    else:
                        df = pd.read_csv(tmp_path, encoding='latin1', sep=delim,
                                         header=0 if hasHeader else None, engine="python",
                                         quotechar=quotechar_val if quotechar else '"',
                                         quoting=quoting_val)
                
                sheets = []

            # 处理 NaN 值，转换为空格
            df = df.fillna('')
            
            # 转为二维字符串数组
            if hasHeader and df.columns is not None:
                all_rows = [list(df.columns.astype(str))] + df.astype(str).values.tolist()
            else:
                all_rows = df.astype(str).values.tolist()

            # 预览模式：只返回前 10 行
            rows = all_rows[:10] if preview_mode else all_rows

            # 获取列名列表
            if hasHeader and df.columns is not None:
                columns = list(df.columns.astype(str))
            elif len(rows) > 0:
                columns = [f"列{i+1}" for i in range(len(rows[0]))]
            else:
                columns = []

            # 获取列类型信息
            columns_with_type = []
            if len(columns) > 0 and len(rows) > 0:
                # 检查是否有数据行（跳过表头）
                data_start = 1 if hasHeader else 0
                if data_start < len(all_rows):
                    # 分析每一列的类型
                    for col_idx, col_name in enumerate(columns):
                        # 收集该列的所有非空值
                        column_values = []
                        for row in all_rows[data_start:]:
                            if col_idx < len(row) and row[col_idx].strip():
                                column_values.append(row[col_idx])
                        
                        # 确定列类型
                        col_type = "string"
                        if column_values:
                            # 尝试判断是否为数字
                            is_numeric = True
                            for val in column_values:
                                try:
                                    float(val)
                                except ValueError:
                                    is_numeric = False
                                    break
                            if is_numeric:
                                col_type = "number"
                        
                        columns_with_type.append({"name": col_name, "type": col_type})

            result = {
                "success": True,
                "fileName": file.filename,
                "rows": rows,
                "columns": columns,
                "columnsWithType": columns_with_type,
                "rowCount": len(all_rows) - (1 if hasHeader else 0),
                "colCount": len(columns),
                "encodingUsed": encoding_used,
                "encodingFallback": encoding_fallback,
            }
            
            if sheets:
                result["sheets"] = sheets
            if preview_mode and suffix.lower() not in (".xlsx", ".xls"):
                result["detectedDelimiter"] = delim
            if preview_mode:
                result["totalRows"] = len(all_rows)
                result["isPreview"] = True

            return JSONResponse(content=result)
        except Exception as e:
            # 发生错误时也要删除临时文件
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except:
                pass
            raise
        finally:
            # 确保删除临时文件
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception as e:
                print(f"   ⚠️ 删除临时文件失败：{e}")

    except pd.errors.ParserError as e:
        return JSONResponse(content={
            "success": False,
            "error": f"解析错误：文件格式不正确 - {str(e)}",
        })
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": str(e),
        })


@app.post("/api/save")
async def save_file(request: Request):
    """导出数据为 Excel 或 CSV，支持编码、分隔符、标题行选项
    
    支持嵌套的 exportSettings：
    {
        "fileName": "文件名",
        "format": "xlsx" | "csv",
        "columns": [...],
        "rows": [...],
        "exportSettings": {
            "encoding": "utf-8-sig",
            "delimiter": ",",
            "includeHeader": true
        }
    }
    """
    try:
        data = await request.json()
        file_name = data.get("fileName", "未命名")
        fmt = data.get("format", "xlsx")
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        
        # 支持嵌套的 exportSettings
        export_settings = data.get("exportSettings", {})
        encoding = export_settings.get("encoding") or data.get("encoding") or "utf-8"
        delimiter = export_settings.get("delimiter") or data.get("delimiter") or ","
        include_header = export_settings.get("includeHeader") if export_settings.get("includeHeader") is not None else data.get("hasHeader", True)
        
        overwrite = data.get("overwrite", False)
        original_path = data.get("originalPath", "")

        delim = delimiter.replace("\\t", "\t")

        if not rows or len(rows) == 0:
            return JSONResponse(content={"success": False, "error": "没有可导出的数据"})

        # 构建 DataFrame
        if include_header and len(rows) > 0:
            col_names = rows[0]
            data_rows = rows[1:]
            df = pd.DataFrame(data_rows, columns=col_names)
        else:
            df = pd.DataFrame(rows)

        # 保存到 uploads 目录
        save_dir = "uploads"
        os.makedirs(save_dir, exist_ok=True)
        
        ext = f".{fmt}" if not file_name.lower().endswith(f".{fmt}") else ""
        full_name = f"{file_name}{ext}"
        save_path = os.path.join(save_dir, full_name)

        if fmt == "xlsx":
            df.to_excel(save_path, index=False, engine="openpyxl")
        elif fmt == "csv":
            df.to_csv(save_path, index=False, encoding=encoding, sep=delim)
        else:
            return JSONResponse(content={"success": False, "error": f"不支持的格式：{fmt}"})

        # 区分保存和另存为：
        # - overwrite=True 是保存（只保存到后端，不下载）
        # - overwrite=False 或不传是另存为（保存到后端 + 浏览器下载）
        if overwrite:
            # 保存模式：只返回成功信息
            return JSONResponse(content={
                "success": True,
                "message": "保存成功",
                "savePath": save_path,
                "fileName": full_name
            })
        else:
            # 另存为模式：保存到后端并返回文件下载
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if fmt == "xlsx" else "text/csv"
            return FileResponse(
                path=save_path,
                media_type=media_type,
                filename=full_name,
            )

    except UnicodeEncodeError:
        return JSONResponse(content={
            "success": False,
            "error": f"编码错误：无法使用 {encoding} 编码文件，中文内容请尝试 GBK 编码",
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e),
        })


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载已保存的文件"""
    # 在桌面和 Downloads 目录中搜索
    search_dirs = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
    ]
    
    for search_dir in search_dirs:
        filepath = os.path.join(search_dir, filename)
        if os.path.exists(filepath):
            def iterfile():
                with open(filepath, "rb") as f:
                    yield from f
            return StreamingResponse(
                iterfile(),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    return JSONResponse(content={"success": False, "error": "文件未找到"})


# ============================================
# 运行服务器
# ============================================
if __name__ == "__main__":
    import uvicorn
    # host=0.0.0.0：允许局域网/外网访问；port=8000：后端端口
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
