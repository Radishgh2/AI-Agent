import pytest
import json
from unittest.mock import MagicMock, patch
from src.tools import analyze_jd, match_resume, generate_cover_letter, mock_interview_tool
from src.models import JDAnalysis, ResumeMatch, CoverLetter, MockInterview, InterviewQA

# Mocking LLM calls for tools
class MockChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages, *args, **kwargs):
        # Simulate LLM responses based on tool function
        if "分析以下职位描述" in messages[0].content:
            return MagicMock(content=json.dumps({
                "company_name": "测试公司",
                "job_title": "测试职位",
                "required_skills": ["Python", "测试"],
                "experience_level": "3年",
                "responsibilities": ["职责1"],
                "qualifications": ["资格1"],
                "preferred_qualifications": ["优先资格1"]
            }))
        elif "对比以下JD分析和简历" in messages[0].content:
            return MagicMock(content=json.dumps({
                "overall_score": 85.5,
                "skill_match": 90.0,
                "experience_match": 80.0,
                "missing_skills": ["云部署"],
                "suggestions": "建议优化项目经验描述。"
            }))
        elif "根据以下JD分析和简历" in messages[0].content and "生成求职信" in messages[0].content:
            return MagicMock(content="尊敬的测试公司招聘经理，我很荣幸申请贵公司的测试职位...")
        elif "根据以下JD分析生成5个面试问题" in messages[0].content:
            return MagicMock(content=json.dumps({
                "questions": [
                    {"question": "请介绍一下您在Python开发方面的经验。", "answer_reference": "应强调实际项目经验。"},
                    {"question": "您对测试职位有什么理解？", "answer_reference": "结合公司文化和职位要求回答。"}
                ]
            }))
        return MagicMock(content="Mocked LLM response")


@pytest.fixture
def mock_llm():
    with patch('src.tools.ChatOpenAI', new=MockChatOpenAI) as mock:
        yield mock

@pytest.fixture
def mock_rag_kb():
    mock = MagicMock()
    mock.get_relevant_experience.return_value = "Relevant experience from RAG"
    return mock


# Sample data for testing
sample_jd_text = "招聘：测试公司，招聘测试职位，要求Python、测试经验3年。"
sample_jd_analysis_json = json.dumps({
    "company_name": "测试公司",
    "job_title": "测试职位",
    "required_skills": ["Python", "测试"],
    "experience_level": "3年",
    "responsibilities": ["职责1"],
    "qualifications": ["资格1"],
    "preferred_qualifications": ["优先资格1"]
})
sample_resume_text = "我叫李明，有5年Python开发经验，熟悉单元测试、集成测试。"


def test_analyze_jd(mock_llm):
    result_json = analyze_jd(sample_jd_text)
    assert isinstance(result_json, str)
    jd_analysis = JDAnalysis.parse_raw(result_json)
    assert jd_analysis.job_title == "测试职位"
    assert "Python" in jd_analysis.required_skills


def test_match_resume(mock_llm, mock_rag_kb):
    result_json = match_resume(sample_jd_analysis_json, sample_resume_text, rag_kb=mock_rag_kb)
    assert isinstance(result_json, str)
    resume_match = ResumeMatch.parse_raw(result_json)
    assert resume_match.overall_score == 85.5
    assert "云部署" in resume_match.missing_skills


def test_generate_cover_letter(mock_llm, mock_rag_kb):
    cover_letter_content = generate_cover_letter(
        sample_jd_analysis_json, sample_resume_text, "专业正式", rag_kb=mock_rag_kb
    )
    assert isinstance(cover_letter_content, str)
    assert "尊敬的测试公司招聘经理" in cover_letter_content


def test_mock_interview(mock_llm):
    result_json = mock_interview_tool(sample_jd_analysis_json)
    assert isinstance(result_json, str)
    mock_interview = MockInterview.parse_raw(result_json)
    assert len(mock_interview.questions) > 0
    assert isinstance(mock_interview.questions[0], InterviewQA)
    assert "Python开发" in mock_interview.questions[0].question

