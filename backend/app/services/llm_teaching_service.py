"""AI 教研服务：教案 / PPT 大纲 / 题库生成，统一走 llm_client。"""
import json
import re

from app.clients.llm_client import llm_client


class LLMTeachingService:
    """面向教师的 AI 备课能力封装（业务层编排提示词）。"""

    @staticmethod
    def generate_teaching_plan(knowledge_point: str, goal: str | None = None) -> str:
        """根据知识点生成教案。"""
        prompt = (
            f"请为知识点「{knowledge_point}」生成一份详细教案，"
            f"包含教学目标、重难点、教学过程、板书设计与课后练习。"
            f"教学目标：{goal or '掌握该知识点'}。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def generate_quiz(knowledge_point: str, count: int = 5,
                      difficulty: int = 3) -> str:
        """按知识点 / 难度生成题目。"""
        prompt = (
            f"请围绕知识点「{knowledge_point}」生成 {count} 道难度{difficulty}（1-5）的题目，"
            f"题型包含选择题与编程题，并附答案与解析。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def summarize_resource(content: str) -> str:
        """为教学资源生成摘要与关键词。"""
        prompt = f"请为以下教学资源生成 100 字以内摘要和 3-5 个关键词：\n{content[:2000]}"
        return llm_client.text_generate(prompt)

    @staticmethod
    def generate_outline(course_name: str, goal: str | None = None) -> str:
        """根据课程主题与教学目标生成课程大纲（章节安排、学时、考核方式）。"""
        prompt = (
            f"请为课程「{course_name}」生成一份完整、可直接用于教学的大纲，包含：\n"
            f"一、课程简介；二、教学目标（{goal or '掌握该课程核心知识与实践能力'}）；\n"
            f"三、章节安排（每章列知识点、重难点与建议学时）；四、实践环节；五、考核方式与成绩构成。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def generate_ppt(topic: str, objective: str | None = None,
                     outline: str | None = None) -> str:
        """根据主题 / 教学目标 / 大纲生成 PPT 演示文稿结构（逐页标题与要点）。"""
        prompt = (
            f"请围绕主题「{topic}」生成一份用于课堂讲授的 PPT 大纲，逐页给出：\n"
            f"第 N 页：页标题 + 3-5 条要点（bullet）。要求覆盖导入、概念讲解、案例演示、互动练习与小结，共 10-15 页。\n"
            f"教学目标：{objective or '帮助学生掌握该主题'}。\n"
            + (f"可参考大纲：\n{outline[:1500]}\n" if outline else "")
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def generate_exam_paper(knowledge_point: str, count: int = 10,
                            difficulty: int = 3, question_types: str | None = None) -> str:
        """智能组卷：按知识点 / 题量 / 难度 / 题型分布生成一套完整试卷。"""
        types = question_types or "选择题、填空题、简答题、编程题"
        prompt = (
            f"请围绕知识点「{knowledge_point}」编制一套完整试卷，共 {count} 道题，"
            f"整体难度 {difficulty}（1-5），题型覆盖：{types}。\n"
            f"输出格式：一、试卷说明；二、试题（逐题给出题型、分值、题干）；三、参考答案与评分标准；四、难度分布说明。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def review_question(question_text: str) -> str:
        """题目质量评估：从科学性、区分度、表述与答案正确性角度给题。"""
        prompt = (
            f"请对下面这道题进行质量评估，从「科学性、难度与区分度、表述清晰度、答案正确性、"
            f"改进建议」五个维度给出结论，并给出总体评分（满分 10 分）：\n\n{question_text[:3000]}"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def design_project(topic: str, difficulty: int = 3,
                       goal: str | None = None) -> str:
        """实践项目设计助手：生成项目需求、任务拆解、原型与评分标准。"""
        prompt = (
            f"请为「{topic}」设计一个面向大学生的实践项目（难度 {difficulty}/5），包含：\n"
            f"一、项目背景与目标（{goal or '通过动手实践巩固核心知识'}）；\n"
            f"二、功能需求与模块划分；三、技术路线与关键数据结构/算法；\n"
            f"四、分阶段任务拆解（含里程碑）；五、验收标准与评分细则。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def generate_teaching_report(course_name: str,
                                 semester_data: str | None = None) -> str:
        """教学报告：根据一学期数据生成课程教学总结（成效、问题、改进建议）。"""
        prompt = (
            f"请为课程「{course_name}」生成一份期末教学总结报告，包含：\n"
            f"一、教学基本情况；二、教学成效（结合数据：{semester_data or '无具体数据，请给出通用分析框架'}）；\n"
            f"三、存在问题与原因分析；四、改进措施与下学期计划。"
        )
        return llm_client.text_generate(prompt)

    @staticmethod
    def auto_tag_resource(content: str, title: str = "") -> dict:
        """为教学资源自动生成摘要 + 关键词标签，返回 {"summary": str, "keywords": str}。

        优先调用大模型；未配置 API Key 或调用失败时降级为规则抽取，
        保证「自动摘要关键词」功能在纯离线环境下也可用。
        """
        text = (content or "").strip()
        if llm_client.available and text:
            prompt = (
                f"请为以下教学资源生成元数据，严格输出 JSON（不要输出任何多余文字）：\n"
                f'{{"summary": "不超过100字的内容摘要", "keywords": ["关键词1", "关键词2", "关键词3"]}}\n\n'
                f"资源标题：{title}\n资源内容：\n{text[:3000]}"
            )
            try:
                raw = llm_client.text_generate(prompt)
                parsed = LLMTeachingService._parse_tag(raw)
                if parsed:
                    return parsed
            except Exception:
                pass  # 降级到规则抽取

        return LLMTeachingService._fallback_tag(text, title)

    @staticmethod
    def _parse_tag(raw: str) -> dict | None:
        """解析大模型返回的 JSON（容忍代码块包裹 / 前后杂质）。"""
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            try:
                data = json.loads(m.group(0))
            except (ValueError, TypeError):
                return None
        summary = str(data.get("summary") or "").strip()
        keywords = data.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [k.strip() for k in re.split(r"[，,、;；]", keywords) if k.strip()]
        keywords = [str(k).strip() for k in keywords if str(k).strip()]
        if not summary and not keywords:
            return None
        return {"summary": summary[:500], "keywords": "，".join(keywords[:8])}

    @staticmethod
    def _fallback_tag(text: str, title: str = "") -> dict:
        """无大模型时的规则降级：摘要取正文开头，关键词回退到标题。"""
        summary = (text[:120] + "…") if text else (title or "")
        keywords = title.strip() if title.strip() else ""
        return {"summary": summary[:500], "keywords": keywords}
