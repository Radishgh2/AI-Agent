import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/zhu/.openclaw/credentials/vertex-key.json"
import json
import time
from typing import List, Dict, Any
from collections import defaultdict

from tools import analyze_jd, match_resume
from models import JDAnalysis, ResumeMatch
from rag import RAGKnowledgeBase

# 配置LLM环境变量
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE", "http://localhost:4000/v1")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-mock-key")
os.environ["OPENAI_MODEL_NAME"] = os.getenv("OPENAI_MODEL_NAME", "gemini-2.5-flash")

# 初始化RAG知识库 (用于match_resume)
rag_kb = RAGKnowledgeBase(persist_directory="./chroma_db_eval") # 使用独立的持久化目录

def load_dataset(filepath: str) -> List[Dict[str, Any]]:
    """加载JSON数据集"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_analyze_jd(jd_dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """评估 analyze_jd 工具的提取准确率和响应时间"""
    results = []
    total_time = 0
    correct_extractions = defaultdict(int) # 用于统计每个字段的正确提取数量
    total_extractions = defaultdict(int) # 用于统计每个字段的总提取尝试数量

    # 简单定义JD分析的“准确性”标准：主要字段非空且与原JD内容相关
    # 更准确的评估需要人工标注的ground truth
    target_fields = ["company_name", "job_title", "required_skills", "experience_level"]

    for i, jd_entry in enumerate(jd_dataset):
        jd_text = f"公司: {jd_entry['company']}\n职位: {jd_entry['title']}\n描述: {jd_entry['description']}\n要求: {jd_entry['requirements']}"
        start_time = time.time()
        try:
            extracted_json_str = analyze_jd.invoke({"jd_text": jd_text})
            extracted_data = JDAnalysis.parse_raw(extracted_json_str)
            end_time = time.time()
            
            is_accurate = True
            for field in target_fields:
                total_extractions[field] += 1
                extracted_value = getattr(extracted_data, field)
                
                # 简单检查：字段非空，且对于字符串类型，部分匹配原始JD中的关键字
                field_accurate = False
                if isinstance(extracted_value, str) and extracted_value:
                    if field == "company_name" and jd_entry['company'] in extracted_value:
                        field_accurate = True
                    elif field == "job_title" and jd_entry['title'] in extracted_value:
                        field_accurate = True
                    elif field == "experience_level" and (any(exp in extracted_value for exp in ["年", "经验", "资深", "不限"]) or not extracted_value):
                        field_accurate = True # 经验要求比较模糊，只要有提取或为空都算对
                    elif field == "required_skills" and isinstance(extracted_value, list) and len(extracted_value) > 0:
                        # 对于技能，只要提取出列表且不为空就视为成功
                        field_accurate = True
                    elif extracted_value: # 其他字段只要非空就认为提取成功
                         field_accurate = True
                elif isinstance(extracted_value, list) and len(extracted_value) > 0: # 对于列表类型，只要非空就成功
                    field_accurate = True
                
                if field_accurate:
                    correct_extractions[field] += 1
                else:
                    is_accurate = False # 只要有一个核心字段不准确，则该条JD分析不准确
                    print(f"JD分析不准确: JD ID {i}, 字段 {field}, 期望 {jd_entry.get(field)}, 实际 {extracted_value}")

            results.append({
                "jd_id": i,
                "jd_text": jd_text,
                "extracted_data": extracted_data.dict(),
                "time_taken": end_time - start_time,
                "is_accurate": is_accurate # 整体准确性判断
            })
            total_time += (end_time - start_time)
        except Exception as e:
            print(f"Error analyzing JD ID {i}: {e}")
            results.append({
                "jd_id": i,
                "jd_text": jd_text,
                "error": str(e),
                "time_taken": time.time() - start_time,
                "is_accurate": False
            })
            total_time += (time.time() - start_time)
    
    # 计算准确率和平均时间
    overall_accurate_count = sum(1 for res in results if res.get("is_accurate", False))
    overall_accuracy = (overall_accurate_count / len(results)) * 100 if results else 0
    average_time = total_time / len(results) if results else 0
    
    field_accuracies = {field: (correct_extractions[field] / total_extractions[field]) * 100 
                            for field in total_extractions}

    return {
        "overall_accuracy": overall_accuracy,
        "field_accuracies": field_accuracies,
        "average_response_time_seconds": average_time,
        "total_jds_evaluated": len(jd_dataset),
        "detailed_results": results
    }

def evaluate_match_resume(jd_dataset: List[Dict[str, Any]], 
                          resume_dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """评估 match_resume 工具的合理性和响应时间"""
    results = []
    total_time = 0
    
    # 简化评估“合理性”：检查输出格式是否正确，分数是否在合理范围，建议是否存在
    # 更准确的评估需要人工标注的ground truth和复杂的逻辑
    
    for i, jd_entry in enumerate(jd_dataset[:5]): # 仅评估前5条JD，以节省LLM调用和时间
        jd_text = f"公司: {jd_entry['company']}\n职位: {jd_entry['title']}\n描述: {jd_entry['description']}\n要求: {jd_entry['requirements']}"
        
        # 首先分析JD，因为match_resume需要JDAnalysis对象
        try:
            extracted_jd_json_str = analyze_jd.invoke({"jd_text": jd_text})
            jd_analysis = JDAnalysis.parse_raw(extracted_jd_json_str)
        except Exception as e:
            print(f"Skipping match_resume for JD ID {i} due to JD analysis error: {e}")
            continue

        for j, resume_entry in enumerate(resume_dataset): # 评估所有简历
            resume_text = (
                f"姓名: {resume_entry['name']}\n" +
                "教育经历:\n" + "\n".join([f"  - {edu['university']} {edu['major']} {edu['degree']}" for edu in resume_entry['education']]) +
                "\n技能:\n" + ", ".join(resume_entry['skills']) +
                "\n工作经验:\n" + "\n".join([f"  - {exp['company']} {exp['title']} ({exp['duration']}): {exp['description']}" for exp in resume_entry['experience']]) +
                "\n项目经验:\n" + "\n".join([f"  - {proj['name']}: {proj['description']}" for proj in resume_entry['projects']])
            )
            
            start_time = time.time()
            try:
                extracted_match_json_str = match_resume.invoke({"jd_analysis_json": jd_analysis.json(), "resume_text": resume_text, "rag_kb_instance": rag_kb})
                match_data = ResumeMatch.parse_raw(extracted_match_json_str)
                end_time = time.time()

                # 检查合理性：分数在0-100，有建议
                is_reasonable = (
                    0 <= match_data.match_score.overall <= 100 and
                    0 <= match_data.match_score.skill_match <= 100 and
                    0 <= match_data.match_score.experience_match <= 100 and
                    0 <= match_data.match_score.education_match <= 100 and
                    bool(match_data.suggestions)
                )

                results.append({
                    "jd_id": i,
                    "resume_id": j,
                    "jd_title": jd_entry['title'],
                    "resume_name": resume_entry['name'],
                    "match_data": match_data.dict(),
                    "time_taken": end_time - start_time,
                    "is_reasonable": is_reasonable
                })
                total_time += (end_time - start_time)
            except Exception as e:
                print(f"Error matching JD ID {i} with Resume ID {j}: {e}")
                results.append({
                    "jd_id": i,
                    "resume_id": j,
                    "jd_title": jd_entry['title'],
                    "resume_name": resume_entry['name'],
                    "error": str(e),
                    "time_taken": time.time() - start_time,
                    "is_reasonable": False
                })
                total_time += (time.time() - start_time)

    reasonable_count = sum(1 for res in results if res.get("is_reasonable", False))
    reasonableness_rate = (reasonable_count / len(results)) * 100 if results else 0
    average_time = total_time / len(results) if results else 0

    return {
        "reasonableness_rate": reasonableness_rate,
        "average_response_time_seconds": average_time,
        "total_matches_evaluated": len(results),
        "detailed_results": results
    }

def main():
    jd_dataset = load_dataset("data/jd_dataset.json")
    resume_dataset = load_dataset("data/resume_dataset.json")

    print("\n--- 评估 analyze_jd 工具 ---")
    analyze_jd_eval_results = evaluate_analyze_jd(jd_dataset)
    print("Analyze JD 评估完成。")

    print("\n--- 评估 match_resume 工具 ---")
    match_resume_eval_results = evaluate_match_resume(jd_dataset, resume_dataset)
    print("Match Resume 评估完成。")
    
    # 整合所有评估结果
    evaluation_report = {
        "analyze_jd_evaluation": analyze_jd_eval_results,
        "match_resume_evaluation": match_resume_eval_results,
        "timestamp": time.time()
    }

    # 保存评估结果到文件
    output_path = "data/eval_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation_report, f, ensure_ascii=False, indent=2)
    print(f"评估结果已保存到 {output_path}")

    print("\n评估流程已完成。")

if __name__ == "__main__":
    main()
