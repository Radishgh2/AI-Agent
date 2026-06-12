import os
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from models import (
    JDAnalysis, ResumeMatch, CoverLetter, MockInterview,
    AnalyzeJDRequest, MatchResumeRequest, GenerateCoverLetterRequest,
    MockInterviewRequest, ChatMessage, ChatRequest, ChatResponse
)
from agent import create_job_assistant_agent # 假设agent.py中定义了创建agent的函数
from tools import (
    analyze_jd, match_resume, generate_cover_letter, mock_interview_tool
) # 从tools.py导入具体工具
from rag import RAGKnowledgeBase

# 初始化RAG知识库
# 在API启动时初始化一次RAGKnowledgeBase，并作为依赖注入到需要它的工具中
rag_kb_instance: Optional[RAGKnowledgeBase] = None

def get_rag_kb() -> RAGKnowledgeBase:
    global rag_kb_instance
    if rag_kb_instance is None:
        rag_kb_instance = RAGKnowledgeBase(persist_directory="./chroma_db_api")
    return rag_kb_instance

app = FastAPI(
    title="AI Job Assistant API",
    description="为求职者提供JD分析、简历匹配、求职信生成和模拟面试的AI助手。"
)

# 初始化Agent
# 注意：在实际生产环境中，agent的初始化可能需要更复杂的管理，例如单例模式或延迟加载。
# 这里为了简化，直接初始化。
# 这里的tools列表需要确保和create_job_assistant_agent中的一致，并且match_resume需要绑定rag_kb_instance
@app.on_event("startup")
async def startup_event():
    get_rag_kb() # 确保RAG知识库在启动时初始化
    # 这里的tools列表需要包含lambda函数来传递rag_kb
    global job_assistant_agent
    job_assistant_agent = create_job_assistant_agent(
        tools=[
            analyze_jd,
            # 使用lambda来封装match_resume，以便在调用时传递rag_kb_instance
            # tool装饰器期望一个可调用对象，这里我们创建一个适配器
            # func=lambda jd_analysis, resume_text: match_resume(jd_analysis, resume_text, get_rag_kb()),
            # 为了让langchain的tool装饰器正常工作，我们不能直接在这里用lambda绑定，
            # 而是在tools.py中确保match_resume能接受可选的rag_kb_instance。
            # 这里我们直接传递原始的tool函数，并在工具内部处理rag_kb的获取
            # 在这里，由于match_resume函数内部会调用get_rag_kb()，所以不需要额外传递
            match_resume, # match_resume现在内部会调用get_rag_kb()
            generate_cover_letter,
            mock_interview_tool
        ],
        rag_kb=rag_kb_instance # 传递RAG知识库实例
    )


job_assistant_agent: Any # Type hint for agent

@app.post("/analyze-jd", response_model=JDAnalysis)
async def analyze_jd_endpoint(request: AnalyzeJDRequest):
    """分析职位描述，提取关键信息"""
    try:
        # 直接调用工具函数
        result_json = analyze_jd.func(request.jd_text)
        return JDAnalysis.parse_raw(result_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match", response_model=ResumeMatch)
async def match_resume_endpoint(request: MatchResumeRequest, rag_kb: RAGKnowledgeBase = Depends(get_rag_kb)):
    """匹配简历与JD，给出匹配度评分和建议"""
    try:
        # 调用工具函数，注意这里需要将JDAnalysis转换为JSON字符串或其内部表示
        jd_analysis_str = request.jd_analysis.json()
        result_json = match_resume.func(jd_analysis_str, request.resume_text, rag_kb_instance=rag_kb)
        return ResumeMatch.parse_raw(result_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cover-letter", response_model=CoverLetter)
async def generate_cover_letter_endpoint(request: GenerateCoverLetterRequest):
    """生成定制化求职信"""
    try:
        jd_analysis_str = request.jd_analysis.json()
        result_str = generate_cover_letter.func(jd_analysis_str, request.resume_text, request.style)
        return CoverLetter(content=result_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mock-interview", response_model=MockInterview)
async def mock_interview_endpoint(request: MockInterviewRequest):
    """根据JD生成模拟面试问题"""
    try:
        jd_analysis_str = request.jd_analysis.json()
        result_json = mock_interview_tool.func(jd_analysis_str) # 注意这里调用的是工具函数名
        return MockInterview.parse_raw(result_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """与AI求职顾问进行多轮对话"""
    try:
        # 将Pydantic ChatMessage转换为LangChain BaseMessage
        langchain_history: List[BaseMessage] = []
        if request.history:
            for msg in request.history:
                if msg.role == "user":
                    langchain_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_history.append(AIMessage(content=msg.content))

        response = await job_assistant_agent.ainvoke(
            {"input": request.message, "chat_history": langchain_history}
        )

        # 更新对话历史
        updated_history = request.history if request.history else []
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=response["output"]))

        return ChatResponse(response=response["output"], history=updated_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), rag_kb: RAGKnowledgeBase = Depends(get_rag_kb)):
    """上传PDF简历并建立索引"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    # 确保保存目录存在
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_location = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        rag_kb.upload_pdf_resume(file_location)
        os.remove(file_location) # 索引后删除临时文件
        return {"message": f"简历 {file.filename} 上传并索引成功！"}
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location) # 失败也删除
        raise HTTPException(status_code=500, detail=f"简历处理失败: {str(e)}")
