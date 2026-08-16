/**
 * homework_correction.js —— 作业批改页逻辑（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 按课程查看 / 发布作业
 *  2. 查看某作业的提交记录
 *  3. 触发评测（OJ 判题 + AI 评语），未连接后端时本地模拟结果
 */
(function () {
    'use strict';

    var demoId = 3000;
    var DEMO = {
        courses: [
            { id: 1, name: '算法设计与分析' },
            { id: 2, name: '数据结构' }
        ],
        names: { 101: '张伟', 102: '李娜', 103: '王强', 201: '赵敏', 202: '刘洋' },
        assignments: {
            1: [
                { id: 1, title: '第一次作业：分治法', description: '完成归并排序与快速排序的实现', deadline: '2024-09-20 23:59', status: 'published' },
                { id: 2, title: '第二次作业：动态规划', description: '01 背包与最长公共子序列', deadline: '2024-10-10 23:59', status: 'published' }
            ],
            2: [
                { id: 3, title: '第一次作业：链表操作', description: '实现单链表的增删查改', deadline: '2024-09-25 23:59', status: 'published' }
            ]
        },
        submissions: {
            1: [
                { id: 1, student_id: 101, submit_time: '2024-09-19 20:15', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null },
                { id: 2, student_id: 102, submit_time: '2024-09-19 21:30', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null },
                { id: 3, student_id: 103, submit_time: '2024-09-19 22:05', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null }
            ],
            2: [
                { id: 4, student_id: 101, submit_time: '2024-10-08 19:10', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null }
            ],
            3: [
                { id: 5, student_id: 201, submit_time: '2024-09-24 18:40', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null },
                { id: 6, student_id: 202, submit_time: '2024-09-24 19:55', judge_status: 'pending', score: null, plagiarism_rate: null, ai_comment: null }
            ]
        }
    };

    var state = { courseId: null, assignmentId: null };

    var STATUS_LABEL = { pending: '待评测', judging: '评测中', accepted: '通过', failed: '未通过' };
    var STATUS_CLASS = { pending: 'medium', judging: 'medium', accepted: 'low', failed: 'high' };

    function $(id) { return document.getElementById(id); }

    function studentName(id) {
        return DEMO.names[id] || ('学生 #' + id);
    }

    // ---------- 课程 ----------
    async function loadCourses() {
        var data = await api.request(
            api.listCourses({ page: 1, page_size: 100 }),
            { items: DEMO.courses, total: DEMO.courses.length }
        );
        DEMO.courses = (data && data.items) || [];
        var sel = $('courseFilter');
        sel.innerHTML = DEMO.courses.map(function (c) {
            return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
        }).join('');
        if (DEMO.courses.length) {
            state.courseId = DEMO.courses[0].id;
            loadAssignments(state.courseId);
        }
    }

    $('courseFilter').addEventListener('change', function () {
        state.courseId = Number(this.value);
        state.assignmentId = null;
        $('submissionTableBody').innerHTML = '<tr><td colspan="6" class="empty">请选择作业</td></tr>';
        $('submissionHint').textContent = '';
        loadAssignments(state.courseId);
    });

    // ---------- 作业 ----------
    async function loadAssignments(courseId) {
        var data = await api.request(
            api.listAssignments(courseId),
            { items: DEMO.assignments[courseId] || [], total: (DEMO.assignments[courseId] || []).length }
        );
        DEMO.assignments[courseId] = data.items || [];
        renderAssignments();
        if (!state.assignmentId && (data.items || []).length) {
            selectAssignment((data.items || [])[0].id);
        }
    }

    function renderAssignments() {
        var tbody = $('assignmentTableBody');
        var items = (state.courseId && DEMO.assignments[state.courseId]) || [];
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty">暂无作业，点击右上角「发布作业」</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (a) {
            var active = a.id === state.assignmentId ? ' active' : '';
            return '<tr class="assignment-row' + active + '" data-id="' + a.id + '">' +
                '<td><div class="title">' + esc(a.title) + '</div>' +
                (a.description ? '<div class="desc">' + esc(a.description) + '</div>' : '') + '</td>' +
                '<td>' + esc(a.deadline || '-') + '</td>' +
                '<td><span class="badge ' + (a.status === 'published' ? 'low' : 'medium') + '">' +
                (a.status === 'published' ? '已发布' : (a.status === 'closed' ? '已关闭' : '草稿')) + '</span></td>' +
                '<td><button class="btn secondary small" data-act="view">查看提交</button></td>' +
                '</tr>';
        }).join('');

        tbody.querySelectorAll('tr').forEach(function (tr) {
            tr.addEventListener('click', function (e) {
                var act = e.target.getAttribute('data-act');
                var id = Number(tr.getAttribute('data-id'));
                if (act === 'view') { selectAssignment(id); return; }
                selectAssignment(id);
            });
        });
    }

    function selectAssignment(id) {
        state.assignmentId = id;
        renderAssignments();
        $('submissionHint').textContent = '（' + assignmentTitle(id) + '）';
        loadSubmissions(id);
    }

    function assignmentTitle(id) {
        var items = (state.courseId && DEMO.assignments[state.courseId]) || [];
        for (var i = 0; i < items.length; i++) {
            if (items[i].id === id) return items[i].title;
        }
        return '';
    }

    function openAssignmentModal() {
        if (!state.courseId) { showToast('请先选择课程', 'error'); return; }
        openModal('发布作业',
            '<div class="form-row"><label class="form-label">作业标题</label>' +
            '<input class="form-input" id="mTitle" placeholder="如：第一次作业：分治法"></div>' +
            '<div class="form-row"><label class="form-label">作业说明</label>' +
            '<textarea class="form-textarea" id="mDesc" placeholder="选填"></textarea></div>' +
            '<div class="form-row"><label class="form-label">OJ 题目 ID <span class="muted">（选填，关联 buctcoder 题目后自动判题）</span></label>' +
            '<input class="form-input" id="mOjProblem" type="number" placeholder="如：1000（A+B Problem）"></div>' +
            '<div class="form-row"><label class="form-label">判题语言</label>' +
            '<select class="form-select" id="mOjLang">' +
            '<option value="python" selected>Python</option>' +
            '<option value="cpp">C++</option>' +
            '<option value="c">C</option>' +
            '<option value="java">Java</option>' +
            '<option value="go">Go</option>' +
            '<option value="javascript">JavaScript</option>' +
            '<option value="sql">SQL</option>' +
            '</select></div>' +
            '<div class="form-row"><label class="form-label">截止时间</label>' +
            '<input class="form-input" id="mDeadline" placeholder="如：2024-09-20 23:59"></div>',
            function (close) {
                var title = $('mTitle').value.trim();
                if (!title) { showToast('作业标题不能为空', 'error'); return; }
                var ojProblem = $('mOjProblem').value.trim();
                var data = {
                    course_id: state.courseId,
                    title: title,
                    description: $('mDesc').value.trim(),
                    oj_problem_id: ojProblem ? Number(ojProblem) : null,
                    oj_language: $('mOjLang').value,
                    deadline: $('mDeadline').value.trim() || null
                };
                api.request(api.createAssignment(data)).then(function () {
                    showToast('作业发布成功');
                    loadAssignments(state.courseId);
                }).catch(function () {
                    (DEMO.assignments[state.courseId] = DEMO.assignments[state.courseId] || [])
                        .push(Object.assign({ id: ++demoId, status: 'published' }, data));
                    showToast('演示模式：作业已本地发布');
                    close();
                    renderAssignments();
                });
                close();
            });
    }

    // ---------- 提交 ----------
    async function loadSubmissions(assignmentId) {
        var data = await api.request(api.listSubmissions(assignmentId), DEMO.submissions[assignmentId] || []);
        DEMO.submissions[assignmentId] = data;
        renderSubmissions();
    }

    function renderSubmissions() {
        var tbody = $('submissionTableBody');
        var items = (state.assignmentId && DEMO.submissions[state.assignmentId]) || [];
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty">暂无提交记录</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (s) {
            var st = s.judge_status || 'pending';
            return '<tr>' +
                '<td>' + esc(studentName(s.student_id)) + '</td>' +
                '<td>' + esc(s.submit_time || '-') + '</td>' +
                '<td><span class="badge ' + (STATUS_CLASS[st] || 'medium') + '">' + (STATUS_LABEL[st] || st) + '</span></td>' +
                '<td>' + (s.score != null ? s.score : '-') + '</td>' +
                '<td>' + (s.plagiarism_rate != null ? (Math.round(s.plagiarism_rate * 100)) + '%' : '-') + '</td>' +
                '<td>' + (s.ai_comment ? '<div class="ai-comment">' + esc(s.ai_comment) + '</div>' : '<span class="pending-tip">待评测</span>') + '</td>' +
                '</tr>';
        }).join('');
    }

    async function triggerJudge() {
        if (!state.assignmentId) { showToast('请先选择作业', 'error'); return; }
        var items = DEMO.submissions[state.assignmentId] || [];
        if (!items.length) { showToast('暂无提交可评测', 'error'); return; }

        var btn = $('btnJudge');
        btn.disabled = true;
        btn.textContent = '评测中…';

        var results = await api.request(api.judgeAssignment(state.assignmentId), null);
        if (results) {
            DEMO.submissions[state.assignmentId] = results;
            showToast('评测完成（后端）');
        } else {
            // 演示模式：本地模拟评测结果
            items.forEach(function (s, idx) {
                var ok = idx % 4 !== 3; // 每第 4 个模拟一次未通过
                s.judge_status = ok ? 'accepted' : 'failed';
                s.score = ok ? Math.min(100, 82 + idx * 4) : 55;
                s.plagiarism_rate = Math.min(0.3, 0.02 + idx * 0.03);
                s.ai_comment = ok
                    ? '代码结构清晰，思路正确，时间复杂度符合要求。建议进一步优化边界条件的处理，并补充必要的注释。'
                    : '部分测试用例未通过，存在数组越界风险，请检查边界条件后重新提交。';
            });
            DEMO.submissions[state.assignmentId] = items;
            showToast('演示模式：已完成本地模拟评测');
        }
        btn.disabled = false;
        btn.textContent = '触发评测（OJ + AI 评语）';
        renderSubmissions();
    }

    async function triggerPlagiarism() {
        if (!state.assignmentId) { showToast('请先选择作业', 'error'); return; }
        var items = DEMO.submissions[state.assignmentId] || [];
        if (items.length < 2) { showToast('提交少于 2 份，无法比对查重', 'error'); return; }

        var btn = $('btnPlagiarism');
        btn.disabled = true;
        btn.textContent = '查重中…';

        var results = await api.request(api.checkPlagiarism(state.assignmentId), null);
        if (results) {
            DEMO.submissions[state.assignmentId] = results;
            showToast('查重完成（后端 simhash）');
        } else {
            items.forEach(function (s, idx) {
                s.plagiarism_rate = idx === 0 ? 0.02 : Math.min(0.85, 0.15 + idx * 0.2);
            });
            DEMO.submissions[state.assignmentId] = items;
            showToast('演示模式：已完成本地查重');
        }
        btn.disabled = false;
        btn.textContent = '代码查重（simhash）';
        renderSubmissions();
    }

    // ---------- 初始化 ----------
    $('btnNewAssignment').addEventListener('click', openAssignmentModal);
    $('btnJudge').addEventListener('click', triggerJudge);
    $('btnPlagiarism').addEventListener('click', triggerPlagiarism);

    $('submissionTableBody').innerHTML = '<tr><td colspan="6" class="empty">请选择作业</td></tr>';

    loadCourses();
})();
