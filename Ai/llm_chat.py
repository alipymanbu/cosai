import os
from langchain_community.chat_models.tongyi import ChatTongyi
from dashscope import Generation
def create_chat_model(model_name: str = "tongyi-xiaomi-analysis-flash"):
    os.environ["DASHSCOPE_API_KEY"] = "sk-d16cf6ba5aca4cea881c7259a417710b"
    
    """创建并返回 ChatTongyi 模型实例"""
    return ChatTongyi(model=model_name)

if __name__ == "__main__":
    chat_model = create_chat_model()
    response = chat_model.invoke("你好")
    print(response.content)