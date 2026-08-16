/**
 * team.js —— 学习小组页（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 按课程 / 班级组建学习小组，指定组长
 *  2. 小组列表（成员构成）
 *  3. 添加成员 / 移除成员 / 删除小组
 *
 * 说明：学生来自班级（listClassStudents 返回真实用户 id / 姓名 / 学号），
 *      组长与成员均按真实用户 id 提交。
 */
(function () {
    'use strict';

    var demoId = 1000;
    var DEMO = {
        courses: [
            { id: 1, name: '算法设计与分析' },
            { id: 2, name: '数据结构' }
        ],
        classes: [
            { id: 1, name: '计科 2401 班' },
            { id: 2, name: '软件 2402 班' }
        ],
        students: {
            1: [
                { id: 101, username: '2022040101', name: '张伟' },
                { id: 102, username: '2022040102', name: '李娜' },
                { id: 103, username: '2022040103', name: '王强' }
            ],
            2: [
                { id: 201, username: '2022040104', name: '赵敏' },
                { id: 202, username: '2022040105', name: '刘洋' }
            ]
        },
        teams: [
            {
                id: 1, name: 'DP 攻坚组', course_id: 1, leader_id: 101,
                description: '围绕动态规划专题互助学习',
                created_at: '2024-09-10 10:00',
                members: [
                    { student_id: 101, name: '张伟', username: '2022040101' },
                    { student_id: 102, name: '李娜', username: '2022040102' }
                ]
            }
        ]
    };
    var teams = [];
    var studentsCache = {};   // classId -> [{id, username, name}]

    function $(id) { return document.getElementById(id); }

    // ---------- 加载 ----------
    async function loadCourses() {
        var data = await api.request(
            api.listCourses({ page: 1, page_size: 100 }),
            { items: DEMO.courses, total: DEMO.courses.length }
        );
        DEMO.courses = (data && data.items) || [];
        $('teamCourse').innerHTML = '<option value="">（不归属课程）</option>' +
            DEMO.courses.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
    }

    async function loadClasses() {
        var data = await api.request(
            api.listClasses({ page: 1, page_size: 100 }),
            { items: DEMO.classes, total: DEMO.classes.length }
        );
        DEMO.classes = (data && data.items) || [];
        $('teamClass').innerHTML = '<option value="">请选择班级</option>' +
            DEMO.classes.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
    }

    async function loadClassStudents(classId) {
        if (!classId) { $('teamLeader').innerHTML = '<option value="">请先选择班级</option>'; return []; }
        var fallback = DEMO.students[classId] || [];
        var students = await api.request(api.listClassStudents(classId), fallback);
        studentsCache[classId] = students || [];
        // 同步刷新「组长」下拉（创建表单场景使用）
        $('teamLeader').innerHTML = '<option value="">请选择组长</option>' +
            (studentsCache[classId] || []).map(function (s) {
                return '<option value="' + s.id + '">' + esc(s.name) + '（' + esc(s.username) + '）</option>';
            }).join('');
        return studentsCache[classId];
    }

    async function loadTeams() {
        var data = await api.request(api.listTeams(), DEMO.teams);
        teams = Array.isArray(data) ? data : [];
        renderTeams();
    }

    // ---------- 渲染 ----------
    function renderTeams() {
        var box = $('teamList');
        if (!teams.length) {
            box.innerHTML = '<div class="empty-tip">暂无学习小组，左侧创建第一个</div>';
            return;
        }
        box.innerHTML = teams.map(function (t) {
            var leader = (t.members || []).find(function (m) { return m.student_id === t.leader_id; });
            var leaderName = leader ? leader.name : ('成员#' + t.leader_id);
            var members = (t.members || []).map(function (m) {
                return '<span class="member-chip" title="' + esc(m.username) + '">' + esc(m.name) + '</span>';
            }).join('');
            return '<li class="team-card">' +
                '<div class="team-head">' +
                '<span class="team-name">' + esc(t.name) + '</span>' +
                '<span class="badge course">' + esc(courseName(t.course_id)) + '</span>' +
                '</div>' +
                '<div class="team-meta">组长：' + esc(leaderName) + ' · ' + (t.member_count || (t.members || []).length) + ' 人</div>' +
                (t.description ? '<div class="team-desc">' + esc(t.description) + '</div>' : '') +
                '<div class="team-members">' + members + '</div>' +
                '<div class="team-actions">' +
                '<button class="btn secondary small" data-act="add" data-id="' + t.id + '">添加成员</button>' +
                '<button class="btn secondary small" data-act="edit" data-id="' + t.id + '">编辑</button>' +
                '<button class="btn danger small" data-act="del" data-id="' + t.id + '">删除</button>' +
                '</div></li>';
        }).join('');

        box.querySelectorAll('[data-act]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var id = Number(btn.getAttribute('data-id'));
                var act = btn.getAttribute('data-act');
                if (act === 'add') openAddMember(id);
                else if (act === 'edit') openEditTeam(id);
                else if (act === 'del') deleteTeam(id);
            });
        });
    }

    function courseName(id) {
        if (!id) return '通用';
        var c = DEMO.courses.find(function (x) { return x.id === id; });
        return c ? c.name : '课程#' + id;
    }

    function studentLabel(s) {
        return esc(s.name) + '（' + esc(s.username) + '）';
    }

    // ---------- 创建 / 编辑 ----------
    $('teamClass').addEventListener('change', function () {
        loadClassStudents(Number(this.value));
    });

    $('teamForm').addEventListener('submit', function (e) {
        e.preventDefault();
        var name = $('teamName').value.trim();
        var courseId = $('teamCourse').value ? Number($('teamCourse').value) : null;
        var leaderId = $('teamLeader').value ? Number($('teamLeader').value) : null;
        var desc = $('teamDesc').value.trim();
        if (!name) { showToast('请填写小组名称', 'error'); return; }
        if (!leaderId) { showToast('请选择组长', 'error'); return; }

        api.request(api.createTeam({ name: name, course_id: courseId, leader_id: leaderId, description: desc })).then(function () {
            showToast('小组创建成功');
            this.reset();
            $('teamLeader').innerHTML = '<option value="">请选择组长</option>';
            loadTeams();
        }.bind(this)).catch(function () {
            teams.push({
                id: ++demoId, name: name, course_id: courseId, leader_id: leaderId,
                description: desc, created_at: new Date().toISOString(),
                members: [{ student_id: leaderId, name: leaderName(leaderId), username: '' }]
            });
            showToast('演示模式：小组已本地创建');
            this.reset();
            loadTeams();
        }.bind(this));
    });

    function leaderName(leaderId) {
        for (var cid in studentsCache) {
            var s = (studentsCache[cid] || []).find(function (x) { return x.id === leaderId; });
            if (s) return s.name;
        }
        return '组长';
    }

    function openEditTeam(id) {
        var t = teams.find(function (x) { return x.id === id; });
        if (!t) return;
        openModal('编辑小组',
            '<div class="form-row"><label class="form-label">小组名称</label>' +
            '<input class="form-input" id="mName" value="' + esc(t.name || '') + '"></div>' +
            '<div class="form-row"><label class="form-label">简介</label>' +
            '<textarea class="form-textarea" id="mDesc">' + esc(t.description || '') + '</textarea></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('小组名称不能为空', 'error'); return; }
                var payload = { name: name, description: $('mDesc').value.trim() };
                api.request(api.updateTeam(id, payload)).then(function () {
                    showToast('小组已更新');
                    loadTeams();
                }).catch(function () {
                    t.name = payload.name; t.description = payload.description;
                    showToast('演示模式：小组已本地更新');
                    close();
                    renderTeams();
                });
                close();
            });
    }

    function openAddMember(id) {
        var classHtml = '<option value="">请选择班级</option>' +
            DEMO.classes.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
        openModal('添加成员',
            '<div class="form-row"><label class="form-label">选择班级</label>' +
            '<select class="form-select" id="mClass">' + classHtml + '</select></div>' +
            '<div class="form-row"><label class="form-label">勾选学生</label>' +
            '<div class="member-picker" id="mStudents">请先选择班级</div></div>',
            function (close) {
                var checks = document.querySelectorAll('#mStudents input[type="checkbox"]:checked');
                var ids = Array.prototype.map.call(checks, function (c) { return Number(c.value); });
                if (!ids.length) { showToast('请勾选要添加的学生', 'error'); return; }
                api.request(api.addTeamMembers(id, ids)).then(function (res) {
                    showToast('已添加 ' + ((res && res.added) || ids.length) + ' 名成员');
                    loadTeams();
                }).catch(function () {
                    var t = teams.find(function (x) { return x.id === id; });
                    if (t) {
                        ids.forEach(function (sid) {
                            var s = findStudent(sid);
                            t.members = t.members || [];
                            if (!t.members.some(function (m) { return m.student_id === sid; })) {
                                t.members.push({ student_id: sid, name: s ? s.name : '学生', username: s ? s.username : '' });
                            }
                        });
                    }
                    showToast('演示模式：成员已本地添加');
                    close();
                    renderTeams();
                });
                close();
            });

        document.getElementById('mClass').addEventListener('change', function () {
            var cid = Number(this.value);
            if (!cid) { $('mStudents').innerHTML = '请先选择班级'; return; }
            loadClassStudents(cid).then(function (list) {
                $('mStudents').innerHTML = list.map(function (s) {
                    return '<label class="member-check"><input type="checkbox" value="' + s.id + '">' + studentLabel(s) + '</label>';
                }).join('');
            });
        });
    }

    function findStudent(sid) {
        for (var cid in studentsCache) {
            var s = (studentsCache[cid] || []).find(function (x) { return x.id === sid; });
            if (s) return s;
        }
        return null;
    }

    function deleteTeam(id) {
        if (!confirm('确定删除该学习小组？')) return;
        api.request(api.deleteTeam(id)).then(function () {
            showToast('小组已删除');
            loadTeams();
        }).catch(function () {
            teams = teams.filter(function (x) { return x.id !== id; });
            showToast('演示模式：小组已本地删除');
            renderTeams();
        });
    }

    // ---------- 初始化 ----------
    loadCourses();
    loadClasses();
    loadTeams();
})();
