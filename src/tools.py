
import os
import json
from typing import List, Dict, Any, Optional
import litellm
from langchain.tools import tool

from models import JDAnalysis, ResumeMatch, CoverLetter, MockInterview

def _call_llm(messages: List[Dict[str, str]], json_output: bool = False) -> str:
    """使用litellm直接调用Vertex AI Gemini模型，并在调用时传递认证信息"""
    model_name = os.getenv("VERTEX_MODEL_NAME", "vertex_ai/gemini-2.5-flash")
    
    # 将认证信息直接在函数调用中传递
    api_kwargs = {
        "vertex_project": "my-vertex-ai-490805",
        "vertex_location": "us-central1",
        "vertex_credentials": "/Users/zhu/.openclaw/credentials/vertex-key.json"
    }

    if json_output:
        response = litellm.completion(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"},
            **api_kwargs
        )
    else:
        response = litellm.completion(
            model=model_name,
            messages=messages,
            **api_kwargs
        )
    
    return response.choices[0].message.content

@tool
def analyze_jd(jd_text: str) -> str:
    """分析职位描述，提取关键信息，返回JDAnalysis模型的JSON字符串。"""
    messages = [
        {"role": "system", "content": f"你是一个专业的职位描述分析助手。请从用户提供的职位描述中提取公司名、职位、技能要求、经验要求、薪资范围、工作地点、教育背景要求、职位职责和任职资格。如果某些信息未明确提及，请留空或使用'不详'。请确保输出严格符合以下JSONSchema格式：\n{JDAnalysis.schema_json(indent=2)}"},
        {"role": "user", "content": f"请分析以下职位描述：\n{jd_text}"}
    ]
    return _call_llm(messages, json_output=True)

@tool
def match_resume(jd_analysis_json: str, resume_text: str, rag_kb_instance: Any = None) -> str:
    """对比JD分析结果(JSON字符串)和简历文本，给出匹配度评分、优势、劣劣势和建议。可选的rag_kb_instance用于增强匹配。"""
    rag_context = ""
    if rag_kb_instance:
        # 这里可以加入RAG相关的逻辑
        pass

    messages = [
        {"role": "system", "content": f"你是一个专业的简历匹配助手。你需要根据提供的职位描述分析结果和简历文本，进行深入对比，并给出以下几个方面的评估：\n1. 综合匹配度评分 (0-100)\n2. 技能匹配度评分 (0-100)\n3. 经验匹配度评分 (0-100)\n4. 教育背景匹配度评分 (0-100)\n5. 简历的优势点：与JD要求高度匹配的具体点。\n6. 简历的劣势点：与JD要求不符或欠缺的具体点。\n7. 提升匹配度的建议：针对劣势点给出具体的改进建议。\n请严格按照以下JSONSchema格式输出结果：\n{ResumeMatch.schema_json(indent=2)}"},
        {"role": "user", "content": f"职位描述分析结果：\n{jd_analysis_json}\n\n简历文本：\n{resume_text}\n\n{rag_context}\n\n请开始评估。"}
    ]
    return _call_llm(messages, json_output=True)

@tool
def generate_cover_letter(jd_analysis_json: str, resume_text: str, style: str = "professional") -> str:
    """根据JD分析结果(JSON字符串)、简历文本和指定风格生成定制化求职信。"""
    style_prompt = ""
    if style == "concise":
        style_prompt = "请用简洁明了的风格，突出核心优势，长度不超过300字。"
    elif style == "enthusiastic":
        style_prompt = "请用热情洋溢的风格，展现积极主动性。"
    else: # Default to professional
        style_prompt = "请用专业的商务风格，结构清晰，语言严谨。"

    messages = [
        {"role": "system", "content": f"你是一个专业的求职信撰写助手。你需要根据提供的职位描述分析结果和简历文本，为用户生成一封定制化的求职信。\n{style_prompt}"},
        {"role": "user", "content": f"职位描述分析结果：\n{jd_analysis_json}\n\n简历文本：\n{resume_text}\n\n请生成求职信。"}
    ]
    return _call_llm(messages)

@tool
def mock_interview_tool(jd_analysis_json: str) -> str:
    """根据JD分析结果(JSON字符串)生成5个面试问题和参考答案，返回MockInterview模型的JSON字符串。"""
    messages = [
        {"role": "system", "content": f"你是一个专业的模拟面试官。你需要根据提供的职位描述分析结果，为该职位生成5个具有挑战性的面试问题和对应的参考答案。问题应涵盖技术、行为和情景方面。请确保输出严格符合以下JSONSchema格式：\n{MockInterview.schema_json(indent=2)}"},
        {"role": "user", "content": f"请为以下职位生成模拟面试问题：\n{jd_analysis_json}"}
    ]
    return _call_llm(messages, json_output=True)
