import os
from typing import List

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from tools import analyze_jd, match_resume, generate_cover_letter, mock_interview_tool
from rag import RAGKnowledgeBase

def create_job_assistant_agent(tools: List[Tool], rag_kb: RAGKnowledgeBase) -> AgentExecutor:
    # 配置LLM
    llm = ChatOpenAI(
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    # 使用LangChain Hub的ReAct Prompt
    # prompt = hub.pull("hwchase17/react") # 这是一个标准的ReAct prompt
    
    # 自定义系统提示词，角色是“资深AI求职顾问”
    system_prompt_template = """你是一名资深AI求职顾问。你的任务是协助用户完成求职过程中的各种任务，包括：
- 分析职位描述（JD）
- 匹配简历与JD
- 生成定制化求职信
- 模拟面试

在与用户交流时，你需要：
1. 友好、专业、富有同情心。
2. 充分利用你所拥有的工具来完成任务。
3. 在需要信息时，主动向用户询问。
4. 支持多轮对话，记住之前的交互内容。
5. 在生成内容时，力求准确、个性化和有帮助。

你可以使用的工具包括：
{tools}

{human_input}

{agent_scratchpad}

祝你求职顺利！

注意：如果用户提供了PDF简历文件，请引导用户上传到RAG知识库，以便进行更精确的匹配和建议。
"""

    # 使用PromptTemplate来构建自定义prompt
    # React Agent的prompt需要包含tools, tool_names, input, agent_scratchpad
    # 这里简化为直接在system_prompt中包含tools和human_input，agent_scratchpad由框架处理
    # 实际上create_react_agent会构建一个更复杂的prompt，这里我们提供一个基础的框架

    prompt = PromptTemplate.from_template(
        system_prompt_template,
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
            "tool_names": ", ".join([tool.name for tool in tools])
        }
    )

    # 确保工具中包含rag_kb的get_relevant_experience方法
    # 这里为了简化，直接在create_job_assistant_agent中传递rag_kb
    # 工具函数内部可以调用rag_kb
    
    # 创建ReAct Agent
    agent = create_react_agent(llm, tools, prompt)

    # 创建AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        # conversational=True, # LangChain 2.x 中通常通过HistoryAwareRetriever进行会话管理
        max_iterations=15,
        early_stopping_method="generate"
    )

    return agent_executor


# 示例用法 (不会在实际运行时执行，仅为演示)
if __name__ == "__main__":
    # 设置环境变量
    os.environ["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    os.environ["OPENAI_API_KEY"] = "sk-zhu-litellm-2026"
    os.environ["OPENAI_MODEL_NAME"] = "gemini-2.5-flash"

    # 重新初始化RAG知识库
    mock_rag_kb = RAGKnowledgeBase(persist_directory="./chroma_db_test")

    # 重新定义工具 (agent.py中的工具需要和tools.py中的一致)
    mock_tools = [
        Tool(name="analyze_jd", func=analyze_jd, description="分析职位描述，提取关键信息"),
        Tool(name="match_resume", func=lambda jd, resume: match_resume(jd, resume, mock_rag_kb), description="匹配简历与JD，给出匹配度评分和建议"),
        Tool(name="generate_cover_letter", func=generate_cover_letter, description="生成定制化求职信"),
        Tool(name="mock_interview", func=mock_interview_tool, description="根据JD生成模拟面试问题")
    ]

    agent = create_job_assistant_agent(mock_tools, mock_rag_kb)
    
    # 模拟对话
    print("AI求职顾问：您好，有什么可以帮助您的吗？")
    chat_history = []

    while True:
        user_input = input("您：")
        if user_input.lower() == 'exit':
            break
        
        # LangChain Agent的调用方式，需要将历史转换为特定的格式
        response = agent.invoke({"input": user_input, "chat_history": chat_history})
        print("AI求职顾问：" + response["output"])
        
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response["output"]))

