/**
 * message_queue.js —— 消息队列页（通知公告 + 任务发布看板）
 *
 * 混合模式：优先调用后端 /messages 接口（与学生端个人消息系统对接），
 * 后端未启动或请求失败时回退到本地演示数据。
 *
 * 数据约定（与学生端 personal_message_system.py 对齐）：
 *   message_type: assignment / notice / system
 *   接收学生 ID 使用「学号」（即 user.username，工号/学号）。
 */
(function () {
    'use strict';

    var STORE_KEY = 'buct_msg_sent_demo';
    var demoId = 100;

    // ---------- 演示数据 ----------
    var DEMO = {
        classes: [
            { id: 1, name: '计科 2401 班' },
            { id: 2, name: '软件 2402 班' }
        ],
        students: {
            1: [
                { id: 101, username: '20240001', name: '张伟' },
                { id: 102, username: '20240002', name: '李娜' },
                { id: 103, username: '20240003', name: '王强' }
            ],
            2: [
                { id: 201, username: '20240010', name: '赵敏' },
                { id: 202, username: '20240011', name: '刘洋' }
            ]
        },
        messages: [
            {
                id: 1, title: '关于算法竞赛校内选拔的通知',
                content: '2024 年算法竞赛校内选拔将于 10 月中旬举行，请各班级组织学生报名，并于 10 月 10 日前提交报名表。',
                message_type: 'notice', created_at: '2024-09-12 10:00',
                deadline: null, attachment_url: null, attachment_name: null,
                receiver_ids: [20240001, 20240002], receiver_count: 2, unread_count: 1
            },
            {
                id: 2, title: '数据结构实验三任务发布',
                content: '请完成「二叉树遍历」实验报告，包含代码实现与运行截图，截止前提交至作业系统。',
                message_type: 'assignment', created_at: '2024-09-15 09:00',
                deadline: '2024-09-25 23:59', attachment_url: null, attachment_name: null,
                receiver_ids: [20240010, 20240011], receiver_count: 2, unread_count: 2
            }
        ],
        courses: [
            { id: 1, name: '算法设计与分析' },
            { id: 2, name: '数据结构' }
        ],
        tasks: [
            {
                id: 1, course_id: 1, title: '完成「动态规划」知识点学习',
                description: '观看第三章动态规划视频并完成配套练习',
                task_type: 'knowledge_point', deadline: '2024-09-28 23:59',
                created_by: 1, created_at: '2024-09-16 09:00',
                student_count: 3, completed_count: 1,
                assignments: [
                    { student_id: 101, name: '张伟', username: '20240001', status: 'completed', completed_at: '2024-09-18 10:00' },
                    { student_id: 102, name: '李娜', username: '20240002', status: 'pending', completed_at: null },
                    { student_id: 103, name: '王强', username: '20240003', status: 'pending', completed_at: null }
                ]
            }
        ],
        qa: {
            pending: [
                { id: 1, student_id: 101, student_name: '张伟', content: '我在做动态规划作业时，01 背包的递推公式总是推不出来，能帮我看看思路吗？', classification: 'complex', created_at: '2024-09-20 14:30' },
                { id: 2, student_id: 102, student_name: '李娜', content: '运行归并排序代码时报了段错误，不知道哪里越界了，代码在作业里。', classification: 'complex', created_at: '2024-09-20 15:10' }
            ],
            stats: { pending: 2, auto_answered: 5, answered: 1 }
        }
    };

    var messages = [];
    var tasks = [];

    var TASK_TYPE_LABEL = { knowledge_point: '知识点', oj: 'OJ 题目', acdc: 'ACDC 任务', other: '其他' };

    function $(id) { return document.getElementById(id); }

    function nowStr() {
        var d = new Date();
        function p(n) { return n < 10 ? '0' + n : '' + n; }
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
            ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    }

    // 兼容后端 ISO 格式（2024-09-15T09:00:00）与演示格式（2024-09-15 09:00）
    function fmtTime(t) {
        if (!t) return '-';
        return String(t).replace('T', ' ').slice(0, 16);
    }

    // 附件的绝对访问地址（后端 /uploads 静态目录）
    function attachmentHref(url) {
        if (!url) return '';
        if (/^https?:/i.test(url)) return url;
        var origin = String(api.BASE_URL).replace(/\/api\/v\d+$/, '');
        return origin + (url.charAt(0) === '/' ? '' : '/') + url;
    }

    function parseReceivers(raw) {
        return (raw || '').split(/[\s,，;；]+/)
            .map(function (s) { return Number(s); })
            .filter(function (n) { return Number.isFinite(n) && n > 0; });
    }

    // ---------- 演示持久化 ----------
    function loadDemoStore() {
        try {
            var raw = localStorage.getItem(STORE_KEY);
            if (raw) {
                var arr = JSON.parse(raw);
                if (Array.isArray(arr) && arr.length) DEMO.messages = arr;
            }
        } catch (e) { /* ignore */ }
    }

    function saveDemo() {
        try { localStorage.setItem(STORE_KEY, JSON.stringify(DEMO.messages)); } catch (e) { /* ignore */ }
    }

    // ---------- 加载 ----------
    async function loadMessages() {
        var data = await api.request(api.listSentMessages(), DEMO.messages);
        messages = Array.isArray(data) ? data : ((data && data.items) || []);
        renderAll();
    }

    async function loadClasses() {
        var data = await api.request(
            api.listClasses({ page: 1, page_size: 100 }),
            { items: DEMO.classes, total: DEMO.classes.length }
        );
        DEMO.classes = (data && data.items) || [];
        var sel = $('classSelect');
        sel.innerHTML = '<option value="">手动填写学号</option>' +
            DEMO.classes.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
    }

    async function getClassStudents(classId) {
        var students = await api.request(api.listClassStudents(classId), DEMO.students[classId] || []);
        DEMO.students[classId] = students || [];
        return DEMO.students[classId];
    }

    async function loadClassStudents(classId) {
        var students = await getClassStudents(classId);
        $('msgReceivers').value = students
            .map(function (s) { return s.username; })
            .join(', ');
    }

    // ---------- 渲染 ----------
    function renderAll() {
        renderNotices();
        renderTasks();
    }

    function renderNotices() {
        var box = $('noticeList');
        var notices = messages.filter(function (m) {
            return m.message_type === 'notice' || m.message_type === 'system';
        });
        if (!notices.length) {
            box.innerHTML = '<div class="empty-tip">暂无通知公告</div>';
            return;
        }
        notices.sort(function (a, b) {
            return String(b.created_at || '').localeCompare(String(a.created_at || ''));
        });
        box.innerHTML = notices.map(function (m) {
            var badge = m.message_type === 'system'
                ? '<span class="badge medium">系统</span>'
                : '<span class="badge low">公告</span>';
            return '<li class="notice-item">' +
                '<div class="notice-head">' + badge +
                '<span class="notice-title">' + esc(m.title) + '</span>' +
                '<span class="notice-time">' + esc(fmtTime(m.created_at)) + '</span></div>' +
                '<div class="notice-content">' + esc(m.content) + '</div>' +
                (m.attachment_url
                    ? '<a class="attachment-link" href="' + esc(attachmentHref(m.attachment_url)) + '" target="_blank">📎 ' + esc(m.attachment_name || '附件') + '</a>'
                    : '') +
                '<div class="notice-meta">已发送给 ' + (m.receiver_count || 0) + ' 人 · ' + (m.unread_count || 0) + ' 人未读</div>' +
                '</li>';
        }).join('');
    }

    async function loadTasks() {
        var data = await api.request(api.listTasks(), DEMO.tasks);
        tasks = Array.isArray(data) ? data : [];
        renderTasks();
    }

    function renderTasks() {
        var box = $('taskList');
        $('taskHint').textContent = '共 ' + tasks.length + ' 项';
        if (!tasks.length) {
            box.innerHTML = '<div class="empty-tip">暂无学习任务，点击右上角「发布学习任务」</div>';
            return;
        }
        tasks.sort(function (a, b) {
            return String(b.created_at || '').localeCompare(String(a.created_at || ''));
        });
        box.innerHTML = tasks.map(function (t) {
            var done = t.completed_count || 0;
            var total = t.student_count || 0;
            var pct = total ? Math.round(done / total * 100) : 0;
            var st = taskStatus(t);
            var pendingNames = (t.assignments || [])
                .filter(function (a) { return a.status !== 'completed'; })
                .map(function (a) { return a.name; })
                .join('、');
            return '<li class="task-item">' +
                '<div class="task-info">' +
                '<div class="task-title">' + esc(t.title) + ' <span class="badge course">' + (TASK_TYPE_LABEL[t.task_type] || '其他') + '</span></div>' +
                '<div class="task-deadline">截止：' + (t.deadline ? esc(fmtTime(t.deadline)) : '不限') + '</div>' +
                '<div class="task-progress"><div class="task-progress-bar" style="width:' + pct + '%"></div></div>' +
                '<div class="task-receivers">完成进度：' + done + ' / ' + total + ' 人' +
                (pendingNames ? ' · 待完成：' + esc(truncateText(pendingNames, 30)) : '') + '</div>' +
                '</div>' +
                '<span class="badge ' + st.cls + '">' + st.label + '</span>' +
                '<button class="btn danger small" data-act="deltask" data-id="' + t.id + '">删除</button>' +
                '</li>';
        }).join('');

        box.querySelectorAll('[data-act="deltask"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                deleteTask(Number(btn.getAttribute('data-id')));
            });
        });
    }

    function truncateText(s, n) {
        s = s || '';
        return s.length > n ? s.slice(0, n) + '…' : s;
    }

    function taskStatus(t) {
        if (t.deadline && fmtTime(t.deadline) < nowStr()) {
            return { label: '已截止', cls: 'high' };
        }
        if ((t.completed_count || 0) >= (t.student_count || 0) && (t.student_count || 0) > 0) {
            return { label: '已全部完成', cls: 'low' };
        }
        return { label: '进行中', cls: 'medium' };
    }

    function deleteTask(id) {
        if (!confirm('确定删除该学习任务？')) return;
        api.request(api.deleteTask(id)).then(function () {
            showToast('任务已删除');
            loadTasks();
        }).catch(function () {
            tasks = tasks.filter(function (t) { return t.id !== id; });
            showToast('演示模式：任务已本地删除');
            renderTasks();
        });
    }

    // ---------- 发布学习任务（模态框） ----------
    function openTaskModal() {
        document.getElementById('modalOk').textContent = '发布';
        var courseHtml = '<option value="">（不归属课程）</option>' +
            DEMO.courses.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
        var classHtml = '<option value="">请选择班级</option>' +
            DEMO.classes.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
        openModal('发布学习任务',
            '<div class="form-row"><label class="form-label">任务标题</label>' +
            '<input class="form-input" id="tTitle" placeholder="如：完成动态规划知识点学习"></div>' +
            '<div class="form-row"><label class="form-label">任务类型</label>' +
            '<select class="form-select" id="tType">' +
            '<option value="knowledge_point">知识点学习</option>' +
            '<option value="oj">OJ 题目</option>' +
            '<option value="acdc">ACDC 任务</option>' +
            '<option value="other">其他</option></select></div>' +
            '<div class="form-row"><label class="form-label">截止时间</label>' +
            '<input class="form-input" type="datetime-local" id="tDeadline"></div>' +
            '<div class="form-row"><label class="form-label">所属课程（选填）</label>' +
            '<select class="form-select" id="tCourse">' + courseHtml + '</select></div>' +
            '<div class="form-row"><label class="form-label">任务描述（选填）</label>' +
            '<textarea class="form-textarea" id="tDesc" placeholder="任务要求、目标…"></textarea></div>' +
            '<div class="form-row"><label class="form-label">选择班级</label>' +
            '<select class="form-select" id="tClass">' + classHtml + '</select></div>' +
            '<div class="form-row"><label class="form-label">勾选指派学生</label>' +
            '<div class="member-picker" id="tStudents">请先选择班级</div></div>',
            function (close) {
                var title = $('tTitle').value.trim();
                var classId = Number($('tClass').value);
                var desc = $('tDesc').value.trim();
                if (!title) { showToast('请填写任务标题', 'error'); return; }
                if (!classId) { showToast('请选择班级', 'error'); return; }
                // 学校 class_tasks 为班级级任务：全班学生均需完成，按班级下发即可
                var content = title + (desc ? '\n' + desc : '');
                var payload = {
                    class_id: classId,
                    task_type: $('tType').value,
                    content: content,
                    deadline: $('tDeadline').value ? $('tDeadline').value + ':00' : null
                };
                api.request(api.createTask(payload)).then(function () {
                    showToast('学习任务已发布');
                    loadTasks();
                }).catch(function () {
                    var memberList = DEMO.students[classId] || [];
                    tasks.unshift({
                        id: ++demoId, class_id: classId, title: title,
                        description: desc, task_type: payload.task_type,
                        deadline: payload.deadline, created_by: 1, created_at: nowStr(),
                        student_count: memberList.length, completed_count: 0,
                        assignments: memberList.map(function (s) {
                            return { student_id: s.id, name: s.name, username: s.username, status: 'pending', completed_at: null };
                        })
                    });
                    showToast('演示模式：任务已本地发布');
                    close();
                    renderTasks();
                });
                close();
            });

        document.getElementById('tClass').addEventListener('change', function () {
            var cid = Number(this.value);
            if (!cid) { $('tStudents').innerHTML = '请先选择班级'; return; }
            getClassStudents(cid).then(function (list) {
                $('tStudents').innerHTML = list.map(function (s) {
                    return '<label class="member-check"><input type="checkbox" value="' + s.id + '">' + esc(s.name) + '（' + esc(s.username) + '）</label>';
                }).join('');
            });
        });
    }

    function findStudent(sid) {
        for (var cid in DEMO.students) {
            var s = (DEMO.students[cid] || []).find(function (x) { return x.id === sid; });
            if (s) return s;
        }
        return null;
    }

    // ---------- AI 问答助手 ----------
    var qaData = null;

    async function loadQaQuestions() {
        var data = await api.request(api.listQaQuestions(), DEMO.qa);
        qaData = data || { pending: [], stats: { pending: 0, auto_answered: 0, answered: 0 } };
        renderQa();
    }

    function renderQa() {
        if (!qaData) return;
        var stats = qaData.stats || { pending: 0, auto_answered: 0, answered: 0 };
        var pending = Array.isArray(qaData.pending) ? qaData.pending : [];

        $('qaStats').innerHTML =
            '<div class="qa-stat">' +
            '<span class="qa-stat-num high">' + (stats.pending || 0) + '</span>' +
            '<span class="qa-stat-label">待处理</span></div>' +
            '<div class="qa-stat">' +
            '<span class="qa-stat-num low">' + (stats.auto_answered || 0) + '</span>' +
            '<span class="qa-stat-label">已自动回复</span></div>' +
            '<div class="qa-stat">' +
            '<span class="qa-stat-num medium">' + (stats.answered || 0) + '</span>' +
            '<span class="qa-stat-label">已人工回复</span></div>';

        var box = $('qaList');
        if (!pending.length) {
            box.innerHTML = '<div class="empty-tip">暂无待处理问题 🎉</div>';
            return;
        }
        box.innerHTML = pending.map(function (q) {
            return '<li class="qa-item">' +
                '<div class="qa-item-head">' +
                '<span class="qa-student">' + esc(q.student_name || ('学生#' + q.student_id)) + '</span>' +
                '<span class="qa-time">' + esc(fmtTime(q.created_at)) + '</span>' +
                '</div>' +
                '<div class="qa-content">' + esc(q.content) + '</div>' +
                '<div class="qa-item-foot">' +
                '<span class="badge high">待处理</span>' +
                '<button class="btn small" data-act="answerqa" data-id="' + q.id + '">回答</button>' +
                '</div></li>';
        }).join('');

        box.querySelectorAll('[data-act="answerqa"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                openAnswerModal(Number(btn.getAttribute('data-id')));
            });
        });
    }

    function openAnswerModal(id) {
        var q = (qaData.pending || []).find(function (x) { return x.id === id; });
        if (!q) return;
        openModal('回答学生提问',
            '<div class="qa-question-box">' +
            '<div class="qa-question-meta">' + esc(q.student_name || ('学生#' + q.student_id)) + ' · ' + esc(fmtTime(q.created_at)) + '</div>' +
            '<div class="qa-question-text">' + esc(q.content) + '</div></div>' +
            '<div class="form-row"><label class="form-label">你的回答</label>' +
            '<textarea class="form-textarea" id="aAnswer" placeholder="输入解答内容，将直接回复给学生"></textarea></div>',
            function (close) {
                var answer = $('aAnswer').value.trim();
                if (!answer) { showToast('请填写回答内容', 'error'); return; }
                api.request(api.answerQuestion(id, { answer: answer })).then(function () {
                    showToast('已回复学生');
                    loadQaQuestions();
                }).catch(function () {
                    qaData.pending = (qaData.pending || []).filter(function (x) { return x.id !== id; });
                    if (qaData.stats) {
                        qaData.stats.pending = Math.max(0, (qaData.stats.pending || 0) - 1);
                        qaData.stats.answered = (qaData.stats.answered || 0) + 1;
                    }
                    showToast('演示模式：已本地回复');
                    renderQa();
                });
                close();
            });
        var okBtn = document.getElementById('modalOk');
        if (okBtn) okBtn.textContent = '回复';
    }

    // ---------- 发布 ----------
    $('msgType').addEventListener('change', function () {
        $('deadlineRow').style.display = this.value === 'assignment' ? 'block' : 'none';
    });

    $('classSelect').addEventListener('change', function () {
        var cid = Number(this.value);
        if (!cid) { $('msgReceivers').value = ''; return; }
        loadClassStudents(cid);
    });

    $('publishForm').addEventListener('submit', function (e) {
        e.preventDefault();
        var type = $('msgType').value;
        var title = $('msgTitle').value.trim();
        var content = $('msgContent').value.trim();
        var fileInput = $('msgFile');
        var deadline = $('msgDeadline').value.trim();

        if (!title) { showToast('请填写标题', 'error'); return; }
        if (!content) { showToast('请填写内容', 'error'); return; }
        var receiverIds = parseReceivers($('msgReceivers').value);
        if (!receiverIds.length) { showToast('请填写接收学生学号', 'error'); return; }

        var fd = new FormData();
        fd.append('title', title);
        fd.append('content', content);
        fd.append('message_type', type);
        fd.append('receiver_ids', JSON.stringify(receiverIds));
        if (type === 'assignment' && deadline) {
            fd.append('deadline', deadline);
        }
        if (fileInput.files && fileInput.files.length) {
            fd.append('file', fileInput.files[0]);
        }

        api.request(api.sendMessage(fd)).then(function () {
            showToast('发布成功');
            resetForm();
            loadMessages();
        }).catch(function () {
            // 演示模式：本地追加
            DEMO.messages.unshift({
                id: ++demoId, title: title, content: content,
                message_type: type, created_at: nowStr(),
                deadline: (type === 'assignment' && deadline) ? deadline : null,
                attachment_url: null,
                attachment_name: (fileInput.files && fileInput.files.length) ? fileInput.files[0].name : null,
                receiver_ids: receiverIds, receiver_count: receiverIds.length, unread_count: receiverIds.length
            });
            saveDemo();
            showToast('演示模式：消息已本地发布');
            resetForm();
            loadMessages();
        });
    });

    function resetForm() {
        var form = $('publishForm');
        form.reset();
        $('deadlineRow').style.display = 'none';
    }

    // ---------- 初始化 ----------
    $('btnNewTask').addEventListener('click', openTaskModal);
    loadDemoStore();
    loadMessages();
    loadTasks();
    loadClasses();
    loadQaQuestions();
})();
