# AI Job Assistant Agent

## 1. 项目简介

AI Job Assistant 是一个基于大语言模型(LLM)构建的智能求职助手。它旨在帮助求职者自动化和优化求职流程,提供从职位分析、简历匹配到求职信生成和模拟面试的全方位支持。

**核心功能:**
- **智能职位分析 (JD Analysis):** 自动从冗长的职位描述中提取关键信息,如公司名称、职位、所需技能、经验要求等。
- **简历与职位匹配 (Resume-JD Matching):** 深度分析简历与目标职位的匹配度,给出量化评分,并提供优势、劣势及改进建议。
- **定制化求职信生成 (Cover Letter Generation):** 结合职位要求和个人简历,一键生成针对性强、风格多样的求职信。
- **模拟面试 (Mock Interview):** 根据职位要求,生成高度相关的面试问题及参考答案,帮助用户进行面试准备。

## 2. 技术栈 (Tech Stack)

- **前端界面:** Streamlit
- **核心框架:** LangChain
- **Agent & LLM 调用:** LangChain Expression Language (LCEL), LiteLLM (直接调用 Google Vertex AI Gemini-2.5-pro)
- **API 服务:** FastAPI, Uvicorn
- **数据模型:** Pydantic
- **向量数据库 & RAG:** ChromaDB, PyPDF
- **容器化:** Docker, Docker Compose

## 3. 架构设计 (Architecture Design)

本项目采用模块化和Agent驱动的架构,以确保可扩展性和可维护性。

- **前端层 (Frontend Layer):** 基于 Streamlit 构建的Web界面,提供用户友好的交互,包括简历/JD输入、功能选择和结果展示,以及与Agent的聊天接口。
- **API 层 (API Layer):** 使用 FastAPI 构建的后端服务,负责接收前端请求,调度Agent任务,并提供标准的RESTful API接口。
- **Agent 层 (Agent Layer):** 核心业务逻辑层,基于 LangChain AgentExecutor 实现。它运用 ReAct 范式,根据用户意图智能地选择并执行工具,进行决策和规划。
- **工具层 (Tools Layer):** 封装了Agent所需的核心功能,如 `analyze_jd`(JD分析)、`match_resume`(简历匹配)、`generate_cover_letter`(求职信生成)和 `mock_interview`(模拟面试)。这些工具通过 LiteLLM 调用 Google Vertex AI 上的 `gemini-2.5-pro` 模型执行复杂的自然语言处理任务。
- **RAG 层 (Retrieval-Augmented Generation Layer):** 利用 ChromaDB 作为向量数据库,存储和检索知识文档(例如简历、JD上下文),为LLM提供增强的上下文信息,提升生成内容的准确性和相关性。
- **数据层 (Data Layer):** 存储原始数据集(如JD、简历)、评估结果和配置信息。

项目的整体数据流向为:**Frontend -> API -> Agent -> Tools/RAG -> LLM -> Agent -> API -> Frontend**。

## 4. 性能指标 (Performance Metrics)

根据对 `data/jd_dataset.json` (30条JD) 和 `data/resume_dataset.json` (10份简历) 的评估结果,使用 `gemini-2.5-pro` 模型在 Google Vertex AI 上运行:

### `analyze_jd` 工具:
- **总体准确率**: 100.00%
- **关键字段准确率**:
    - `company_name`: 100.00%
    - `job_title`: 100.00%
    - `required_skills`: 100.00%
    - `experience_level`: 100.00%
- **平均响应时间**: 7.08 秒/次

### `match_resume` 工具:
- **匹配结果合理性比例**: 94.00%
- **平均响应时间**: 22.55 秒/次

*注:本次评估主要关注功能实现的准确性和合理性,未来将引入更全面的评估体系,并对LLM的Token消耗进行精确计算。*

## 5. 未来改进方向 (Future Improvements)

- **`match_resume` 工具优化**:
    - 进一步优化LLM的提示词和Few-shot示例,提升匹配分数的精确性和一致性。
    - 引入更精细的匹配逻辑,例如根据技能等级、经验年限等进行加权,以提高匹配的粒度。
    - 提升RAG的召回准确性,确保提供给LLM的上下文信息更全面、更相关。
- **LLM 调用策略**: 增加缓存机制,减少重复计算,以降低成本和提高响应速度。
- **评估体系完善**: 扩展评估维度,纳入人工标注的Golden Set,进行更严格的定量评估。
- **功能扩展**: 逐步完善求职信生成和模拟面试功能,提升用户体验。
- **容器化与部署**: 优化Docker镜像,简化生产环境部署流程。



## 6. 安装与启动 (Installation & Startup)

**先决条件:**
- Docker
- Docker Compose
- Python 3.9+ 及 Poetry (用于本地开发和Streamlit运行)

**步骤:**
1.  克隆本项目到本地：
    ```bash
    git clone https://github.com/your-username/ai-job-assistant.git
    cd ai-job-assistant
    ```

2.  配置环境变量：
    根据您的LLM服务商，修改 `docker-compose.yml` 中的 `OPENAI_API_BASE` 和 `OPENAI_API_KEY` 环境变量。对于 Vertex AI，请确保您的 Google Cloud 凭证文件已正确配置（通常通过 `GOOGLE_APPLICATION_CREDENTIALS` 环境变量）。

3.  使用 Docker Compose 启动后端服务和数据库：
    ```bash
    docker-compose up -d --build
    ```
    这将同时启动 FastAPI 应用服务器和 ChromaDB 数据库服务。

4.  **运行 Streamlit 前端界面 (本地)**：
    ```bash
    # 进入项目根目录
    cd ~/Projects/ai-job-assistant/
    # 激活虚拟环境 (如果已创建)
    source .venv/bin/activate
    # 或安装依赖并创建虚拟环境 (如果首次运行)
    # poetry install
    # poetry shell
    # 运行 Streamlit 应用
    streamlit run src/frontend.py
    ```
    Streamlit 界面通常会在 `http://localhost:8501` 启动。

5.  **API 服务** 现在应该在 `http://localhost:8000` 上运行。API 文档可在 `http://localhost:8000/docs` 访问。

## 7. 使用方法 (Usage)

您可以通过 Streamlit 前端界面进行交互，也可以通过任何 HTTP 客户端（如 `curl`, Postman）或自己编写的客户端来与API进行交互。

**示例：分析一个职位描述 (通过API)**
```bash
curl -X 'POST' \
  'http://localhost:8000/analyze-jd' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "jd_text": "我们正在寻找一名资深的AI工程师..."
}'
```

详细的API端点和请求/响应模型请参考 `http://localhost:8000/docs`。

## 8. 演示截图 (Demo Screenshots)

`[此处放置 Streamlit 前端界面的截图]`

`[此处放置交互式API文档截图]`

`[此处放置一个成功匹配的响应结果截图]`
