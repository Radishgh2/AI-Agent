# AI求职助手Agent评估报告

## 1. 评估概述

本报告旨在评估AI求职助手Agent中核心工具的性能，包括`analyze_jd`（JD分析）和`match_resume`（简历匹配）工具的准确性、合理性和响应时间。评估基于`data/jd_dataset.json`和`data/resume_dataset.json`中提供的模拟数据集。

## 2. 评估环境

- **Agent 版本**: [待填写，例如：v0.1.0]
- **LLM 模型**: [待填写，例如：gemini-2.5-flash via LiteLLM proxy]
- **硬件环境**: [待填写，例如：MacBook Pro M1 Max, 32GB RAM]
- **软件环境**: [待填写，例如：Python 3.11, Docker, Docker Compose]

## 3. `analyze_jd` 工具评估结果

### 3.1. 准确率

- **总体JD分析准确率**: [待填写，例如：XX.XX%]
- **各字段准确率**:
    - `company_name` 准确率: [待填写，例如：XX.XX%]
    - `job_title` 准确率: [待填写，例如：XX.XX%]
    - `required_skills` 准确率: [待填写，例如：XX.XX%]
    - `experience_level` 准确率: [待填写，例如：XX.XX%]
    - （其他字段如 `responsibilities`, `qualifications` 因评估标准复杂，暂不进行精确统计，主要依赖人工抽查）

### 3.2. 响应时间

- **平均响应时间**: [待填写，例如：X.XX] 秒/次

### 3.3. 成本预估

- 每次 `analyze_jd` 调用平均 token 消耗: [待填写]
- 总 token 消耗: [待填写]
- 评估总成本: [待填写]

## 4. `match_resume` 工具评估结果

### 4.1. 合理性

- **匹配结果合理性比例**: [待填写，例如：XX.XX%]
    （定义：匹配结果的格式是否正确，分数是否在合理范围（0-100），且包含有意义的建议。）

### 4.2. 响应时间

- **平均响应时间**: [待填写，例如：Y.YY] 秒/次

### 4.3. 成本预估

- 每次 `match_resume` 调用平均 token 消耗: [待填写]
- 总 token 消耗: [待填写]
- 评估总成本: [待填写]

## 5. 总结与建议

### 5.1. 评估总结

[待填写，例如：`analyze_jd` 工具在关键字段提取上表现良好，`match_resume` 工具也能生成格式正确且初步合理的匹配结果。]

### 5.2. 改进建议

- 针对 `analyze_jd` 工具：[待填写，例如：进一步优化提示词，提升对复杂JD结构的解析能力。]
- 针对 `match_resume` 工具：[待填写，例如：引入更精细的匹配逻辑，例如根据技能等级、经验年限等进行加权。提升RAG的召回准确性。]
- 优化LLM调用策略，如增加缓存机制，减少重复计算，以降低成本和提高响应速度。
- 扩展评估维度，纳入人工标注的Golden Set，进行更严格的定量评估。

## 附录

- `data/eval_results.json`：详细评估数据

