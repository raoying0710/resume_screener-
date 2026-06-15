# services/analyzer.py
import json
import re
from datetime import datetime
import openai
from config.defaults import DEEPSEEK_API_KEY

def call_deepseek(prompt, max_tokens=2000):
    try:
        client = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的HR招聘助手，擅长分析简历与岗位匹配度。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API调用失败: {str(e)}"

def auto_generate_job_config(job_title):
    """生成岗位JD、必须项、加分项"""
    prompt = f"""
请为「{job_title}」岗位撰写：
1. 一份专业的招聘JD（职位描述），包含岗位职责和任职要求
2. 必须项（候选人必须满足的条件，3-5条）
3. 加分项（优先考虑的条件，3-5条）

请输出JSON格式：
{{"jd": "JD内容...", "must_have": ["条件1", "条件2", ...], "plus": ["加分1", "加分2", ...]}}
只输出JSON，不要其他文字。
"""
    result = call_deepseek(prompt, max_tokens=1000)
    
    print("=" * 50)
    print("【调试】AI原始返回内容：")
    print(result)
    print("=" * 50)
    
    if result.startswith("ERROR:"):
        return {"error": result}
    try:
        return json.loads(result.strip())
    except:
        print("【调试】JSON解析失败，尝试手动提取...")
        print(f"原始内容：{result}")
        return {"jd": result.strip(), "must_have": [], "plus": []}

def extract_requirements_from_jd(jd_text):
    if not jd_text or jd_text.strip() == "":
        return {"must_have": [], "plus": [], "error": "JD为空"}
    prompt = f"""
请分析以下岗位描述（JD），提取出该岗位的"必须项"（候选人必须满足的条件）和"加分项"（优先考虑的条件）。

JD内容：
{jd_text[:4000]}

请输出JSON格式：
{{
    "must_have": ["条件1", "条件2", ...],
    "plus": ["加分1", "加分2", ...]
}}
只输出JSON，不要其他解释。
"""
    result_text = call_deepseek(prompt, max_tokens=800)
    if result_text.startswith("ERROR:"):
        return {"error": result_text}
    try:
        result_text = re.sub(r'```json\n?', '', result_text)
        result_text = re.sub(r'```\n?', '', result_text)
        return json.loads(result_text)
    except:
        return {"error": "解析AI响应失败"}

def analyze_resume(candidate_name, resume_text, job_desc, company_bg, portfolio_text=""):
    portfolio_section = ""
    if portfolio_text and portfolio_text.strip():
        portfolio_section = f"\n\n【候选人作品集内容】\n{portfolio_text[:4000]}\n"

    prompt = f"""
你是一位资深招聘主管。请严格按照以下岗位信息，对候选人简历和作品集（如有）进行专业评估，并生成一份完整的招聘评估报告。

【公司背景】
{company_bg}

【岗位描述（JD）】
{job_desc}

【候选人简历内容】
{resume_text[:8000]}
{portfolio_section}

请输出以下JSON格式，不要有任何额外文字：

{{
    "summary": "HR专业总结（100~200字）",
    "dimensions": {{
        "匹配度": 8,
        "项目经验": 8,
        "沟通表达": 7,
        "稳定性": 8
    }},
    "status": "通过",   // 可选值：通过 / 存疑 / 淘汰
    "questions": ["面试追问问题1", "面试追问问题2", "面试追问问题3"]
}}

重要规则：
1. 四个维度（匹配度、项目经验、沟通表达、稳定性）请分别打分，分数可以是整数或小数（如7.5）。
2. 最终的总分 = 这四个维度的算术平均值，请计算后保留一位小数。
3. 在生成完整报告时，报告中的匹配度评分必须使用这个平均值。

请根据上面的规则，额外计算出 total_score 字段，并将平均值填入。
同时，按照以下格式生成 full_report（使用 **加粗** 标题，不要用 #）：

**1. 【HR专业总结】**  
[summary内容]

**2. 【匹配度评分】**  
[total_score]分 / 10分

**3. 【维度评估】**  
- **匹配度**：[匹配度]分 ...
- **项目经验**：[项目经验]分 ...
- **沟通表达**：[沟通表达]分 ...
- **稳定性**：[稳定性]分 ...

**4. 【简历状态】**  
【status】

**5. 【面试追问】**  
1. [追问1]
2. [追问2]
3. [追问3]

现在，请输出完整的JSON，包含以下字段：
{{
    "summary": "...",
    "dimensions": {{"匹配度": 数字, "项目经验": 数字, "沟通表达": 数字, "稳定性": 数字}},
    "status": "...",
    "questions": ["...", "...", "..."],
    "total_score": 数字（四个维度的平均值，保留一位小数）,
    "full_report": "上面格式的完整报告文本"
}}
"""
    result_text = call_deepseek(prompt, max_tokens=2500)
    if result_text.startswith("ERROR:"):
        error_msg = result_text
        return {
            "summary": f"AI分析失败: {error_msg}",
            "total_score": 0,
            "dimensions": {"匹配度": 0, "项目经验": 0, "沟通表达": 0, "稳定性": 0},
            "status": "存疑",
            "questions": ["请检查API Key和网络连接"],
            "full_report": f"**分析失败**\n{error_msg}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    try:
        result_text = re.sub(r'```json\n?', '', result_text)
        result_text = re.sub(r'```\n?', '', result_text)
        result = json.loads(result_text)

        if "total_score" not in result or result["total_score"] is None:
            dims = result.get("dimensions", {})
            avg = (dims.get("匹配度", 0) + dims.get("项目经验", 0) + dims.get("沟通表达", 0) + dims.get("稳定性", 0)) / 4.0
            result["total_score"] = round(avg, 1)

        if "full_report" not in result or not result["full_report"]:
            report = f"**1. 【HR专业总结】**\n{result.get('summary', '')}\n\n"
            report += f"**2. 【匹配度评分】**\n{result['total_score']}分 / 10分\n\n"
            report += "**3. 【维度评估】**\n"
            for k, v in result.get('dimensions', {}).items():
                report += f"- **{k}**：{v}分 ...\n"
            report += f"\n**4. 【简历状态】**\n【{result.get('status', '存疑')}】\n\n"
            report += "**5. 【面试追问】**\n"
            for i, q in enumerate(result.get('questions', []), 1):
                report += f"{i}. {q}\n"
            result["full_report"] = report

    except Exception as e:
        error_msg = f"解析异常: {str(e)}"
        result = {
            "summary": error_msg,
            "total_score": 0,
            "dimensions": {"匹配度": 0, "项目经验": 0, "沟通表达": 0, "稳定性": 0},
            "status": "存疑",
            "questions": ["无法生成追问"],
            "full_report": f"**分析失败**\n{error_msg}"
        }
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return result

# 兼容旧函数名
auto_generate_jd = auto_generate_job_config