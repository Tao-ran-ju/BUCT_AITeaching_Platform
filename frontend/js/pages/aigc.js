/**
 * aigc.js —— AI 备课中心页逻辑（混合模式：真实 API + 演示回退）
 *
 * 功能：教案生成 / 智能题库 / 资源摘要。未配置 LLM_API_KEY 或后端未连接时，
 * 回退到本地模板生成的演示内容，保证页面可用。
 */
(function () {
    'use strict';

    function $(id) { return document.getElementById(id); }

    var output = $('output');

    // ---------- 工具切换 ----------
    document.querySelectorAll('.tool-tab').forEach(function (tab) {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.tool-tab').forEach(function (t) { t.classList.remove('active'); });
            document.querySelectorAll('.tool-form').forEach(function (f) { f.classList.remove('active'); });
            tab.classList.add('active');
            $('form-' + tab.getAttribute('data-tool')).classList.add('active');
        });
    });

    // ---------- 通用提交 ----------
    function setLoading() {
        output.textContent = '正在生成，请稍候…';
        output.classList.add('loading');
    }

    function setResult(text) {
        output.classList.remove('loading');
        output.textContent = text || '（无内容）';
    }

    async function run(apiCall, demoText) {
        setLoading();
        var content = await api.request(apiCall, { content: demoText });
        setResult(content.content);
    }

    // ---------- 演示内容模板 ----------
    function planDemo(kp, goal) {
        var g = goal || '理解' + kp + '的核心概念与典型应用';
        return '【教案】' + kp + '\n' +
            '一、教学目标\n' +
            '  1. 知识与技能：' + g + '；\n' +
            '  2. 过程与方法：通过例题引导、代码演示与上机练习，掌握解题思路；\n' +
            '  3. 情感态度：培养算法思维与解决实际问题的兴趣。\n\n' +
            '二、教学重难点\n' +
            '  · 重点：核心概念的理解与经典模板的运用；\n' +
            '  · 难点：状态/递推关系的抽象与边界条件处理。\n\n' +
            '三、教学过程\n' +
            '  1. 导入（5 分钟）：由一个贴近竞赛的实例引入；\n' +
            '  2. 讲解（30 分钟）：概念推导 + 例题精讲；\n' +
            '  3. 练习（20 分钟）：2-3 道上机题分层训练；\n' +
            '  4. 小结（5 分钟）：梳理知识脉络与易错点。\n\n' +
            '四、课后作业\n' +
            '  · 基础题 2 道、提高题 1 道，附参考答案与解析。\n\n' +
            '（演示内容，接入大模型后将返回更完整的教案）';
    }

    function quizDemo(kp, count, difficulty) {
        var lines = ['【智能题库】知识点：' + kp + '（难度 ' + difficulty + '/5）\n'];
        var level = difficulty <= 2 ? '基础' : (difficulty <= 4 ? '进阶' : '困难');
        for (var i = 1; i <= count; i++) {
            lines.push(
                '第 ' + i + ' 题（' + level + '）\n' +
                '  题干：请设计一个与「' + kp + '」相关的' + level + '问题，并描述其输入输出格式。\n' +
                '  参考答案：（略，示例参考答案）\n' +
                '  解析：本题考察' + kp + '的基本思想与模板运用，注意边界条件与复杂度。\n'
            );
        }
        lines.push('（演示内容，接入大模型后将返回真实题目）');
        return lines.join('\n');
    }

    function summarizeDemo(text) {
        var snippet = text.length > 40 ? text.slice(0, 40) + '…' : text;
        return '【内容摘要】\n' +
            '  原文要点：' + snippet + '\n\n' +
            '  摘要：本文围绕所提供材料展开，主要阐述了相关概念、方法与应用场景，' +
            '强调理解核心思想并通过实例加以巩固。全文结构清晰、重点突出，适合作为' +
            '教学素材或自学材料使用。\n\n' +
            '  · 关键词：核心概念、方法、实例、应用\n' +
            '  （演示内容，接入大模型后将返回精准摘要）';
    }

    function outlineDemo(course, goal) {
        var g = goal || '掌握该课程核心知识与实践能力';
        return '【课程大纲】' + course + '\n' +
            '一、课程简介\n' +
            '  本课程系统讲授' + course + '的核心理论、经典方法与典型应用，注重算法思维与工程实践能力的培养。\n\n' +
            '二、教学目标\n' +
            '  ' + g + '。\n\n' +
            '三、章节安排\n' +
            '  第 1 章 绪论与基础（4 学时）——基本概念、复杂度分析；\n' +
            '  第 2 章 核心专题（12 学时）——重点方法与模板；\n' +
            '  第 3 章 进阶与综合（8 学时）——综合应用与竞赛真题；\n' +
            '  第 4 章 实践项目（8 学时）——小组项目开发。\n\n' +
            '四、实践环节\n' +
            '  上机练习 + 课程项目 + 竞赛训练。\n\n' +
            '五、考核方式\n' +
            '  平时作业 20% + 实验 20% + 项目 20% + 期末 40%。\n\n' +
            '（演示内容，接入大模型后将返回更贴合课程的大纲）';
    }

    function pptDemo(topic, objective) {
        return '【PPT 大纲】' + topic + '\n\n' +
            '第 1 页  封面：' + topic + '（' + (objective || '教学目标') + '）\n' +
            '第 2 页  导入：一个贴近竞赛/工程的实际问题\n' +
            '第 3 页  学习目标：明确本节要达成的能力\n' +
            '第 4 页  概念讲解：核心定义与直观理解\n' +
            '第 5 页  算法思想：流程 / 递推关系图解\n' +
            '第 6 页  例题演示 1：逐步推导\n' +
            '第 7 页  例题演示 2：边界与易错点\n' +
            '第 8 页  互动练习：课堂小测 1-2 题\n' +
            '第 9 页  小结：知识脉络与模板\n' +
            '第 10 页 课后作业与下节预告\n\n' +
            '（演示内容，接入大模型后将返回逐页详细要点）';
    }

    function examDemo(kp, count, diff) {
        var lines = ['【智能组卷】考核知识点：' + kp + '（共 ' + count + ' 题，难度 ' + diff + '/5）\n\n一、试卷说明\n  满分 100 分，考试时间 120 分钟。\n\n二、试题\n'];
        for (var i = 1; i <= count; i++) {
            var type = i % 4 === 0 ? '编程题' : (i % 3 === 0 ? '简答题' : (i % 2 === 0 ? '填空题' : '选择题'));
            lines.push('第 ' + i + ' 题（' + type + '，' + Math.round(100 / count) + ' 分）\n  围绕「' + kp + '」设问，考察基本概念与典型应用。\n');
        }
        lines.push('三、参考答案与评分标准（略，示例）\n四、难度分布：基础 / 进阶 / 综合 约为 4 : 4 : 2\n\n（演示内容，接入大模型后将返回真实试卷）');
        return lines.join('\n');
    }

    function reviewDemo(question) {
        var snippet = question.length > 30 ? question.slice(0, 30) + '…' : question;
        return '【题目质量评估】\n\n  题目：' + snippet + '\n\n' +
            '  1. 科学性：题意明确、结论正确，无歧义。\n' +
            '  2. 难度与区分度：难度适中，能较好区分不同水平学生。\n' +
            '  3. 表述清晰度：语言通顺、输入输出约定清楚。\n' +
            '  4. 答案正确性：参考答案逻辑自洽，边界考虑完整。\n' +
            '  5. 改进建议：可补充样例说明与复杂度要求。\n\n' +
            '  总体评分：8 / 10\n\n' +
            '（演示内容，接入大模型后将返回针对性评估）';
    }

    function projectDemo(topic, diff, goal) {
        return '【实践项目方案】' + topic + '\n\n' +
            '一、项目背景与目标\n' +
            '  ' + (goal || '通过动手实践巩固核心知识并完成一个小型系统') + '（难度 ' + diff + '/5）。\n\n' +
            '二、功能需求\n' +
            '  · 核心功能模块 2-3 个；· 数据输入 / 输出与可视化。\n\n' +
            '三、技术路线\n' +
            '  · 关键数据结构 / 算法选型；· 开发语言与框架建议。\n\n' +
            '四、分阶段任务拆解\n' +
            '  阶段 1（需求与设计）→ 阶段 2（核心实现）→ 阶段 3（测试与优化）→ 阶段 4（答辩与报告）。\n\n' +
            '五、验收标准与评分细则\n' +
            '  功能完整 40% + 代码质量 20% + 创新性 20% + 答辩 20%。\n\n' +
            '（演示内容，接入大模型后将返回定制化方案）';
    }

    function reportDemo(course, data) {
        return '【教学报告】' + course + '\n\n' +
            '一、教学基本情况\n' +
            '  本课程按大纲完成既定教学任务' + (data ? '，并结合所提供数据进行了分析。' : '。') + '\n\n' +
            '二、教学成效\n' +
            '  多数学生掌握核心知识点，作业完成率与到课率保持稳定。\n\n' +
            '三、存在问题与原因分析\n' +
            '  部分学生基础薄弱、练习投入不足，导致成绩分化明显。\n\n' +
            '四、改进措施与下学期计划\n' +
            '  加强分层教学、增加过程性评价与学情预警干预。\n\n' +
            '（演示内容，接入大模型后将结合真实数据生成总结）';
    }

    // ---------- 提交事件 ----------
    document.querySelectorAll('[data-submit]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var tool = btn.getAttribute('data-submit');

            if (tool === 'plan') {
                var kp = $('planKp').value.trim();
                if (!kp) { showToast('请填写知识点', 'error'); return; }
                var goal = $('planGoal').value.trim();
                run(api.generatePlan({ knowledge_point: kp, goal: goal || undefined }), planDemo(kp, goal));

            } else if (tool === 'outline') {
                var course = $('outlineCourse').value.trim();
                if (!course) { showToast('请填写课程名称', 'error'); return; }
                var oGoal = $('outlineGoal').value.trim();
                run(api.generateOutline({ course_name: course, goal: oGoal || undefined }), outlineDemo(course, oGoal));

            } else if (tool === 'ppt') {
                var topic = $('pptTopic').value.trim();
                if (!topic) { showToast('请填写授课主题', 'error'); return; }
                var pObj = $('pptObjective').value.trim();
                var pOutline = $('pptOutline').value.trim();
                run(api.generatePpt({ topic: topic, objective: pObj || undefined, outline: pOutline || undefined }), pptDemo(topic, pObj));

            } else if (tool === 'quiz') {
                var qKp = $('quizKp').value.trim();
                if (!qKp) { showToast('请填写知识点', 'error'); return; }
                var count = Math.min(20, Math.max(1, Number($('quizCount').value) || 5));
                var diff = Math.min(5, Math.max(1, Number($('quizDifficulty').value) || 3));
                run(api.generateQuiz({ knowledge_point: qKp, count: count, difficulty: diff }), quizDemo(qKp, count, diff));

            } else if (tool === 'exam') {
                var eKp = $('examKp').value.trim();
                if (!eKp) { showToast('请填写考核知识点', 'error'); return; }
                var eCount = Math.min(30, Math.max(1, Number($('examCount').value) || 10));
                var eDiff = Math.min(5, Math.max(1, Number($('examDifficulty').value) || 3));
                var eTypes = $('examTypes').value.trim();
                run(api.generateExamPaper({ knowledge_point: eKp, count: eCount, difficulty: eDiff, question_types: eTypes || undefined }), examDemo(eKp, eCount, eDiff));

            } else if (tool === 'review') {
                var qText = $('reviewQuestion').value.trim();
                if (qText.length < 10) { showToast('请粘贴至少 10 字的题目', 'error'); return; }
                run(api.reviewQuestion(qText), reviewDemo(qText));

            } else if (tool === 'project') {
                var pTopic = $('projectTopic').value.trim();
                if (!pTopic) { showToast('请填写项目主题', 'error'); return; }
                var pDiff = Math.min(5, Math.max(1, Number($('projectDifficulty').value) || 3));
                var pGoal = $('projectGoal').value.trim();
                run(api.designProject({ topic: pTopic, difficulty: pDiff, goal: pGoal || undefined }), projectDemo(pTopic, pDiff, pGoal));

            } else if (tool === 'report') {
                var rCourse = $('reportCourse').value.trim();
                if (!rCourse) { showToast('请填写课程名称', 'error'); return; }
                var rData = $('reportData').value.trim();
                run(api.generateReport({ course_name: rCourse, semester_data: rData || undefined }), reportDemo(rCourse, rData));

            } else if (tool === 'summarize') {
                var text = $('sumText').value.trim();
                if (text.length < 10) { showToast('请粘贴至少 10 字的原文', 'error'); return; }
                run(api.summarizeResource(text), summarizeDemo(text));
            }
        });
    });

    // ---------- 复制结果 ----------
    $('btnCopy').addEventListener('click', function () {
        var text = output.textContent;
        if (!text || output.classList.contains('loading')) { showToast('暂无可复制内容', 'error'); return; }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                showToast('已复制到剪贴板');
            }).catch(function () {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    });

    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('已复制到剪贴板');
    }
})();
