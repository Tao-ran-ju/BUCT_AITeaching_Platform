/**
 * class_management.js —— 班级管理页逻辑（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 班级列表 / 新建 / 编辑 / 删除
 *  2. 选中班级查看学生名单
 *  3. 批量添加学生 / 移除学生
 */
(function () {
    'use strict';

    var demoId = 2000;
    var DEMO = {
        classes: [
            { id: 1, name: '计科 2401 班', grade: '2024', major: '计算机科学与技术', description: '算法竞赛重点班', created_at: '2024-09-01' },
            { id: 2, name: '软件 2402 班', grade: '2024', major: '软件工程', description: '', created_at: '2024-09-01' },
            { id: 3, name: '计科 2301 班', grade: '2023', major: '计算机科学与技术', description: '', created_at: '2023-09-01' }
        ],
        students: {
            1: [
                { id: 101, username: '20240001', name: '张伟', department: '计算机科学与技术', phone: '13800000001' },
                { id: 102, username: '20240002', name: '李娜', department: '计算机科学与技术', phone: '13800000002' },
                { id: 103, username: '20240003', name: '王强', department: '计算机科学与技术', phone: '13800000003' }
            ],
            2: [
                { id: 201, username: '20240010', name: '赵敏', department: '软件工程', phone: '13800000010' },
                { id: 202, username: '20240011', name: '刘洋', department: '软件工程', phone: '13800000011' }
            ],
            3: [
                { id: 301, username: '20230001', name: '陈晨', department: '计算机科学与技术', phone: '13800000020' }
            ]
        }
    };

    var state = { classId: null };

    function $(id) { return document.getElementById(id); }

    // ---------- 班级 ----------
    async function loadClasses() {
        var data = await api.request(
            api.listClasses({ page: 1, page_size: 100 }),
            { items: DEMO.classes, total: DEMO.classes.length }
        );
        DEMO.classes = (data && data.items) || [];
        renderClasses();
        if (!state.classId && DEMO.classes.length) {
            selectClass(DEMO.classes[0].id);
        }
    }

    function renderClasses() {
        var tbody = $('classTableBody');
        if (!DEMO.classes.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty">暂无班级</td></tr>';
            return;
        }
        tbody.innerHTML = DEMO.classes.map(function (c) {
            var active = c.id === state.classId ? ' active' : '';
            return '<tr class="class-row' + active + '" data-id="' + c.id + '">' +
                '<td><div class="class-name">' + esc(c.name) + '</div>' +
                (c.description ? '<div class="class-desc">' + esc(c.description) + '</div>' : '') + '</td>' +
                '<td>' + esc(c.grade || '-') + '</td>' +
                '<td>' + esc(c.major || '-') + '</td>' +
                '<td><div class="row-actions">' +
                '<button class="btn secondary small" data-act="edit">编辑</button>' +
                '<button class="btn danger small" data-act="del">删除</button>' +
                '</div></td></tr>';
        }).join('');

        tbody.querySelectorAll('tr').forEach(function (tr) {
            tr.addEventListener('click', function (e) {
                var act = e.target.getAttribute('data-act');
                var id = Number(tr.getAttribute('data-id'));
                if (act === 'edit') { openClassModal(id); return; }
                if (act === 'del') { deleteClass(id); return; }
                selectClass(id);
            });
        });
    }

    function selectClass(id) {
        state.classId = id;
        renderClasses();
        $('studentClassHint').textContent = '（' + className(id) + '）';
        loadStudents(id);
    }

    function className(id) {
        for (var i = 0; i < DEMO.classes.length; i++) {
            if (DEMO.classes[i].id === id) return DEMO.classes[i].name;
        }
        return '';
    }

    function openClassModal(id) {
        var editing = DEMO.classes.filter(function (c) { return c.id === id; })[0] || null;
        var title = editing ? '编辑班级' : '新建班级';
        openModal(title,
            '<div class="form-row"><label class="form-label">班级名称</label>' +
            '<input class="form-input" id="mName" value="' + esc(editing ? editing.name : '') + '" placeholder="如：计科 2401 班"></div>' +
            '<div class="form-row"><label class="form-label">年级</label>' +
            '<input class="form-input" id="mGrade" value="' + esc(editing ? editing.grade : '') + '" placeholder="如：2024"></div>' +
            '<div class="form-row"><label class="form-label">专业</label>' +
            '<input class="form-input" id="mMajor" value="' + esc(editing ? editing.major : '') + '" placeholder="如：计算机科学与技术"></div>' +
            '<div class="form-row"><label class="form-label">班级简介</label>' +
            '<textarea class="form-textarea" id="mDesc" placeholder="选填">' + esc(editing ? editing.description : '') + '</textarea></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('班级名称不能为空', 'error'); return; }
                var data = {
                    name: name,
                    grade: $('mGrade').value.trim(),
                    major: $('mMajor').value.trim(),
                    description: $('mDesc').value.trim()
                };
                if (editing) {
                    api.request(api.updateClass(id, data)).then(function () {
                        showToast('班级已更新');
                        loadClasses();
                    }).catch(function () {
                        Object.keys(data).forEach(function (k) { editing[k] = data[k]; });
                        showToast('演示模式：班级已本地更新');
                        close();
                        renderClasses();
                    });
                } else {
                    api.request(api.createClass(data)).then(function () {
                        showToast('班级创建成功');
                        loadClasses();
                    }).catch(function () {
                        DEMO.classes.push(Object.assign({ id: ++demoId, created_at: '' }, data));
                        showToast('演示模式：班级已本地创建');
                        close();
                        renderClasses();
                    });
                }
                close();
            });
    }

    async function deleteClass(id) {
        if (!confirm('确定删除该班级？')) return;
        try {
            await api.deleteClass(id);
            showToast('班级已删除');
        } catch (e) {
            DEMO.classes = DEMO.classes.filter(function (c) { return c.id !== id; });
            delete DEMO.students[id];
            showToast('演示模式：班级已本地删除');
        }
        if (state.classId === id) {
            state.classId = null;
            $('studentTableBody').innerHTML = '<tr><td colspan="5" class="empty">请选择班级</td></tr>';
            $('studentClassHint').textContent = '';
        }
        loadClasses();
    }

    // ---------- 学生 ----------
    async function loadStudents(classId) {
        var data = await api.request(api.listClassStudents(classId), DEMO.students[classId] || []);
        DEMO.students[classId] = data;
        renderStudents();
    }

    function renderStudents() {
        var tbody = $('studentTableBody');
        var items = (state.classId && DEMO.students[state.classId]) || [];
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">暂无学生，点击右上角「批量添加学生」</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (s) {
            return '<tr data-id="' + s.id + '">' +
                '<td>' + esc(s.username || '-') + '</td>' +
                '<td>' + esc(s.name || '-') + '</td>' +
                '<td>' + esc(s.department || '-') + '</td>' +
                '<td>' + esc(s.phone || '-') + '</td>' +
                '<td><button class="btn danger small" data-act="remove">移除</button></td>' +
                '</tr>';
        }).join('');

        tbody.querySelectorAll('tr').forEach(function (tr) {
            tr.querySelector('[data-act="remove"]').addEventListener('click', function () {
                removeStudent(Number(tr.getAttribute('data-id')));
            });
        });
    }

    function openAddStudentsModal() {
        if (!state.classId) { showToast('请先选择班级', 'error'); return; }
        openModal('批量添加学生',
            '<div class="form-row"><label class="form-label">学生学号 / 用户ID（逗号或换行分隔）</label>' +
            '<textarea class="form-textarea" id="mIds" placeholder="20240004, 20240005&#10;20240006"></textarea></div>' +
            '<div class="form-row"><p style="font-size:12px;color:#999;">可粘贴多个学号，系统将自动去重并跳过已在班学生。</p></div>',
            function (close) {
                var raw = $('mIds').value.trim();
                var ids = raw.split(/[\s,，;；]+/).map(function (s) {
                    return Number(s);
                }).filter(function (n) { return Number.isFinite(n) && n > 0; });
                if (!ids.length) { showToast('请输入有效的学生 ID', 'error'); return; }

                api.request(api.addClassStudents(state.classId, ids), { added: 0 }).then(function (res) {
                    showToast('成功添加 ' + (res.added != null ? res.added : ids.length) + ' 名学生');
                    loadStudents(state.classId);
                }).catch(function () {
                    var existing = DEMO.students[state.classId] || [];
                    var existIds = existing.map(function (s) { return s.id; });
                    ids.forEach(function (sid) {
                        if (existIds.indexOf(sid) < 0) {
                            existing.push({ id: sid, username: String(sid), name: '学生' + sid, department: '', phone: '' });
                            existIds.push(sid);
                        }
                    });
                    DEMO.students[state.classId] = existing;
                    showToast('演示模式：已本地添加 ' + ids.length + ' 名学生');
                    close();
                    renderStudents();
                });
                close();
            });
    }

    async function removeStudent(studentId) {
        if (!confirm('确定从班级移除该学生？')) return;
        try {
            await api.removeClassStudent(state.classId, studentId);
            showToast('已移除该学生');
        } catch (e) {
            DEMO.students[state.classId] = (DEMO.students[state.classId] || [])
                .filter(function (s) { return s.id !== studentId; });
            showToast('演示模式：已本地移除该学生');
        }
        renderStudents();
    }

    // ---------- 初始化 ----------
    $('btnNewClass').addEventListener('click', function () { openClassModal(null); });
    $('btnAddStudents').addEventListener('click', openAddStudentsModal);

    $('studentTableBody').innerHTML = '<tr><td colspan="5" class="empty">请选择班级</td></tr>';

    loadClasses();
})();
