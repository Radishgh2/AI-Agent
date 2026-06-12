from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# JD Analysis Models
class JDAnalysis(BaseModel):
    company_name: str = Field(..., description="提取到的公司名称")
    job_title: str = Field(..., description="提取到的职位名称")
    required_skills: List[str] = Field(..., description="职位所需的技能列表")
    experience_level: str = Field(..., description="所需的经验级别，如'3-5年', '不限', '资深'")
    salary_range: Optional[str] = Field(None, description="薪资范围，如'20K-40K/月'")
    location: Optional[str] = Field(None, description="工作地点")
    education_requirements: Optional[str] = Field(None, description="教育背景要求，如'本科及以上'")
    responsibilities: Optional[List[str]] = Field(None, description="职位职责列表")
    qualifications: Optional[List[str]] = Field(None, description="任职资格列表")

# Resume Match Models
class MatchScore(BaseModel):
    overall: int = Field(..., ge=0, le=100, description="综合匹配度评分 (0-100)")
    skill_match: int = Field(..., ge=0, le=100, description="技能匹配度评分 (0-100)")
    experience_match: int = Field(..., ge=0, le=100, description="经验匹配度评分 (0-100)")
    education_match: int = Field(..., ge=0, le=100, description="教育背景匹配度评分 (0-100)")

class ResumeMatch(BaseModel):
    match_score: MatchScore = Field(..., description="各项匹配度评分")
    strengths: List[str] = Field(..., description="简历与JD匹配的优势点")
    weaknesses: List[str] = Field(..., description="简历与JD不匹配的弱势点或不足")
    suggestions: List[str] = Field(..., description="提升匹配度的建议")

# Cover Letter Model
class CoverLetter(BaseModel):
    content: str = Field(..., description="生成的求职信内容")

# Mock Interview Models
class InterviewQuestion(BaseModel):
    question: str = Field(..., description="面试问题")
    answer_reference: str = Field(..., description="参考答案")

class MockInterview(BaseModel):
    job_title: str = Field(..., description="模拟面试的职位")
    questions: List[InterviewQuestion] = Field(..., description="面试问题列表及参考答案")
    tips: List[str] = Field(..., description="面试技巧和建议")

# Chat Models for API
class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色，'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的消息")
    history: Optional[List[ChatMessage]] = Field(None, description="历史对话记录")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent的回复")
    history: Optional[List[ChatMessage]] = Field(None, description="更新后的对话记录")

# API Request Models (for direct tool calls via API)
class AnalyzeJDRequest(BaseModel):
    jd_text: str = Field(..., description="职位描述文本")

class MatchResumeRequest(BaseModel):
    jd_analysis: JDAnalysis = Field(..., description="已分析的JD数据")
    resume_text: str = Field(..., description="简历文本")

class GenerateCoverLetterRequest(BaseModel):
    jd_analysis: JDAnalysis = Field(..., description="已分析的JD数据")
    resume_text: str = Field(..., description="简历文本")
    style: str = Field("professional", description="求职信风格，如'professional', 'concise', 'enthusiastic'")

class MockInterviewRequest(BaseModel):
    jd_analysis: JDAnalysis = Field(..., description="已分析的JD数据")
