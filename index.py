from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np

app = FastAPI(
    title="数据处理API",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def to_dataframe(data):
    """
    将前端传来的数据字典转换为DataFrame
    参数格式: {"row-col": "value", ...} 如 {"1-1": "A1", "1-2": "B1"}
    """
    if data is None or len(data) == 0:
        return pd.DataFrame()

    max_row = 0
    max_col = 0
    for k in data.keys():
        row, col = map(int, k.split('-'))
        max_row = max(max_row, row)
        max_col = max(max_col, col)

    df = pd.DataFrame(index=range(max_row), columns=range(max_col))
    for k, y in data.items():
        row, col = map(int, k.split('-'))
        df.iloc[row-1, col-1] = y

    df = df.fillna('')
    return df

@app.post("/api/post-data")
async def post_data(data: dict):
    """接收前端传来的单元格数据"""
    global df
    df = to_dataframe(data)
    print(f"接收到数据: {len(data)} 个单元格")
    print(f"数据形状: {df.shape}")
    return {"success": True, "message": "数据已接收", "rows": len(df), "cols": len(df.columns)}

@app.get("/api/get-data")
async def get_data():
    """返回当前数据"""
    if 'df' in globals():
        df_clean = df.replace({np.nan: ''})
        return df_clean.to_dict()
    else:
        return {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8001, reload=True)