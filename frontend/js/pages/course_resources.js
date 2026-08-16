/**
 * course_resources.js —— 课程资源页逻辑（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 课程列表 / 新建 / 删除
 *  2. 章节目录（点击课程加载）与知识点（点击章节加载）
 *  3. 教学资源上传 / 列表 / 可见性 / 删除
 */
(function () {
    'use strict';

    // ---------- 演示数据 ----------
    var demoId = 1000;
    var DEMO = {
        courses: [
            { id: 1, name: '算法设计与分析', code: 'CS301', status: 'published', description: '面向算法竞赛的核心课程，覆盖分治、动态规划、图论等' },
            { id: 2, name: '数据结构', code: 'CS201', status: 'published', description: '线性表、树、图等基础数据结构' },
            { id: 3, name: '程序设计基础', code: 'CS101', status: 'draft', description: 'C 语言入门与程序设计' }
        ],
        chapters: {
            1: [
                { id: 1, title: '第一章 绪论', sort_order: 1, description: '算法与复杂度' },
                { id: 2, title: '第二章 分治法', sort_order: 2, description: '归并/快排' },
                { id: 3, title: '第三章 动态规划', sort_order: 3, description: '状态转移' }
            ],
            2: [
                { id: 4, title: '第一章 线性表', sort_order: 1, description: '' },
                { id: 5, title: '第二章 树与图', sort_order: 2, description: '' }
            ],
            3: [
                { id: 6, title: '第一章 C 语言基础', sort_order: 1, description: '' }
            ]
        },
        kps: {
            1: [{ id: 1, name: '算法复杂度分析', description: '时间/空间复杂度' }, { id: 2, name: '递归与主定理', description: '' }],
            2: [{ id: 3, name: '归并排序', description: '' }, { id: 4, name: '快速排序', description: '' }],
            3: [{ id: 5, name: '01 背包', description: '' }, { id: 6, name: '最长公共子序列', description: '' }],
            4: [{ id: 7, name: '顺序表', description: '' }, { id: 8, name: '链表', description: '' }],
            5: [{ id: 9, name: '二叉树遍历', description: '' }],
            6: [{ id: 10, name: '变量与数据类型', description: '' }]
        },
        resources: [
            { id: 1, title: '算法导论课件.pdf', resource_type: 'document', file_size: 2048000, visibility: 'course', course_id: 1, summary: '介绍算法复杂度分析、分治与动态规划等核心思想', keywords: '算法复杂度，分治，动态规划', created_at: '2024-09-01' },
            { id: 2, title: '动态规划讲解视频.mp4', resource_type: 'video', file_size: 52428800, visibility: 'course', course_id: 1, created_at: '2024-09-05' },
            { id: 3, title: '链表实现示例代码.zip', resource_type: 'code', file_size: 102400, visibility: 'private', course_id: 2, summary: '单链表与双链表的插入、删除、遍历实现', keywords: '链表，指针', created_at: '2024-09-10' },
            { id: 4, title: 'C 语言语法速查表.png', resource_type: 'image', file_size: 512000, visibility: 'public', course_id: 3, created_at: '2024-08-20' }
        ]
    };

    var state = {
        courseId: null,
        chapterId: null,
        resources: []
    };

    var TYPE_LABEL = {
        document: '文档', video: '视频', audio: '音频',
        image: '图片', code: '代码', other: '其他'
    };
    var VIS_LABEL = { public: '公开', course: '课程内', private: '私有' };

    // ---------- 工具函数 ----------
    function formatSize(bytes) {
        if (bytes === null || bytes === undefined) return '-';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    }

    function formatDuration(sec) {
        if (sec === null || sec === undefined || isNaN(sec)) return '';
        sec = Math.round(sec);
        var h = Math.floor(sec / 3600);
        var m = Math.floor((sec % 3600) / 60);
        var s = sec % 60;
        function p(n) { return n < 10 ? '0' + n : '' + n; }
        return h > 0 ? (h + ':' + p(m) + ':' + p(s)) : (m + ':' + p(s));
    }

    function truncate(s, n) {
        s = s || '';
        return s.length > n ? s.slice(0, n) + '…' : s;
    }

    function typeOfFilename(name) {
        var ext = (name || '').split('.').pop().toLowerCase();
        if (['mp4', 'avi', 'mov', 'mkv'].indexOf(ext) >= 0) return 'video';
        if (['mp3', 'wav', 'flac'].indexOf(ext) >= 0) return 'audio';
        if (['png', 'jpg', 'jpeg', 'gif', 'bmp'].indexOf(ext) >= 0) return 'image';
        if (['c', 'cpp', 'java', 'py', 'js', 'zip', 'tar', 'rar'].indexOf(ext) >= 0) return 'code';
        if (['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'md'].indexOf(ext) >= 0) return 'document';
        return 'other';
    }

    function $(id) { return document.getElementById(id); }

    // 后端返回的相对路径（/uploads/...）拼成完整地址
    function fullUrl(path) {
        if (!path) return '';
        if (/^https?:\/\//.test(path)) return path;
        var origin = (window.api && api.BASE_URL)
            ? api.BASE_URL.replace(/\/api\/v1\/?$/, '')
            : '';
        var clean = path.charAt(0) === '/' ? path : '/' + path;
        return origin ? origin + clean : clean;
    }

    // 资源文件的直链地址（302 到 OSS 签名 URL 或本地 /uploads）。
    // 浏览器 <img>/<a> 无法携带 Authorization 头，故把 JWT 放进 ?token= 查询参数。
    function resourceFileUrl(r, kind) {
        var base = (window.api && api.BASE_URL) || '/api/v1';
        base = base.replace(/\/+$/, '');
        var url = base + '/resources/' + r.id + '/file?kind=' + encodeURIComponent(kind || 'original');
        var token = localStorage.getItem('buct_access_token');
        if (token) url += '&token=' + encodeURIComponent(token);
        return url;
    }

    // 可在线预览的资源类型（对应后端 /resources/{id}/preview 的支持范围）
    function canPreview(r) {
        return ['document', 'video', 'audio', 'image'].indexOf(r.resource_type) >= 0;
    }

    function courseStatusLabel(status) {
        if (status === 'draft') return '草稿';
        if (status === 'archived') return '已归档';
        return '已发布';
    }

    // datetime-local 输入值 → 后端可解析的 ISO（补秒）
    function toIso(v) {
        if (!v) return null;
        return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v) ? v + ':00' : v;
    }

    // 后端 ISO → datetime-local 输入值（截到分钟）
    function toLocalInput(v) {
        return v ? String(v).slice(0, 16) : '';
    }

    // ---------- 课程 ----------
    async function loadCourses() {
        var data = await api.request(
            api.listCourses({ page: 1, page_size: 100 }),
            { items: DEMO.courses, total: DEMO.courses.length }
        );
        var items = (data && data.items) || [];
        DEMO.courses = items;
        renderCourses();
        populateResCourseSelect();
        if (!state.courseId && items.length) {
            selectCourse(items[0].id);
        }
    }

    function renderCourses() {
        var box = $('courseList');
        if (!DEMO.courses.length) {
            box.innerHTML = '<div class="empty-tip">暂无课程，点击右上角「新建课程」开始</div>';
            return;
        }
        box.innerHTML = DEMO.courses.map(function (c) {
            var active = c.id === state.courseId ? ' active' : '';
            var cover = c.cover
                ? '<img class="course-cover" src="' + esc(fullUrl(c.cover)) + '" alt="">'
                : '<span class="course-cover placeholder"></span>';
            var actions = '<div class="actions">' +
                '<button class="btn secondary small" data-act="edit">编辑</button>' +
                '<button class="btn secondary small" data-act="clone">克隆</button>' +
                (c.status !== 'published'
                    ? '<button class="btn small" data-act="publish">发布</button>' : '') +
                (c.status !== 'archived'
                    ? '<button class="btn secondary small" data-act="archive">归档</button>' : '') +
                '<button class="btn danger small" data-act="del">删除</button>' +
                '</div>';
            return '<li class="course-item' + active + '" data-id="' + c.id + '">' +
                cover +
                '<div class="course-main"><div class="name">' + esc(c.name) + '</div>' +
                '<div class="meta">编号 ' + esc(c.code || '-') + ' · ' + courseStatusLabel(c.status) + '</div></div>' +
                actions +
                '</li>';
        }).join('');

        box.querySelectorAll('.course-item').forEach(function (li) {
            li.addEventListener('click', function (e) {
                var act = e.target.getAttribute('data-act');
                var id = Number(li.getAttribute('data-id'));
                if (act) {
                    e.stopPropagation();
                    handleCourseAction(act, id);
                    return;
                }
                selectCourse(id);
            });
        });
    }

    function handleCourseAction(act, id) {
        if (act === 'del') return deleteCourse(id);
        if (act === 'edit') return openEditCourseModal(id);
        if (act === 'clone') return cloneCourse(id);
        if (act === 'archive') return archiveCourse(id);
        if (act === 'publish') return publishCourse(id);
    }

    function selectCourse(id) {
        state.courseId = id;
        state.chapterId = null;
        renderCourses();
        $('chapterCourseHint').textContent = courseName(id);
        loadChapters(id);
        loadResources(id);
        var sel = $('resCourse');
        for (var i = 0; i < sel.options.length; i++) {
            if (Number(sel.options[i].value) === id) {
                sel.selectedIndex = i;
                break;
            }
        }
    }

    function courseName(id) {
        for (var i = 0; i < DEMO.courses.length; i++) {
            if (DEMO.courses[i].id === id) return DEMO.courses[i].name;
        }
        return '';
    }

    function openCourseModal() {
        openModal('新建课程',
            '<div class="form-row"><label class="form-label">课程名称</label>' +
            '<input class="form-input" id="mName" placeholder="如：算法设计与分析"></div>' +
            '<div class="form-row"><label class="form-label">课程编号</label>' +
            '<input class="form-input" id="mCode" placeholder="如：CS301"></div>' +
            '<div class="form-row"><label class="form-label">课程简介</label>' +
            '<textarea class="form-textarea" id="mDesc" placeholder="选填"></textarea></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('课程名称不能为空', 'error'); return; }
                var data = { name: name, code: $('mCode').value.trim(), description: $('mDesc').value.trim() };
                api.request(api.createCourse(data)).then(function () {
                    showToast('课程创建成功');
                    loadCourses();
                }).catch(function () {
                    DEMO.courses.push({
                        id: ++demoId, name: data.name, code: data.code,
                        description: data.description, status: 'published'
                    });
                    showToast('演示模式：课程已本地创建');
                    close();
                    renderCourses();
                    populateResCourseSelect();
                });
                close();
            });
    }

    function openEditCourseModal(id) {
        var c = DEMO.courses.find(function (x) { return x.id === id; });
        if (!c) return;
        openModal('编辑课程',
            '<div class="form-row"><label class="form-label">课程名称</label>' +
            '<input class="form-input" id="mName" value="' + esc(c.name || '') + '"></div>' +
            '<div class="form-row"><label class="form-label">课程编号</label>' +
            '<input class="form-input" id="mCode" value="' + esc(c.code || '') + '"></div>' +
            '<div class="form-row"><label class="form-label">课程简介</label>' +
            '<textarea class="form-textarea" id="mDesc">' + esc(c.description || '') + '</textarea></div>' +
            '<div class="form-row"><label class="form-label">开放时间</label>' +
            '<input class="form-input" type="datetime-local" id="mOpenTime" value="' + toLocalInput(c.open_time) + '"></div>' +
            '<div class="form-row"><label class="form-label">封面图（选填，重新上传）</label>' +
            '<input class="form-input file-input" type="file" id="mCover" accept="image/*"></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('课程名称不能为空', 'error'); return; }
                var payload = {
                    name: name,
                    code: $('mCode').value.trim(),
                    description: $('mDesc').value.trim(),
                    open_time: toIso($('mOpenTime').value)
                };
                var coverFile = $('mCover').files && $('mCover').files[0];
                api.request(api.updateCourse(id, payload)).then(function () {
                    if (coverFile) {
                        var fd = new FormData();
                        fd.append('file', coverFile);
                        api.request(api.uploadCourseCover(id, fd)).then(function () {
                            showToast('课程与封面已更新');
                            loadCourses();
                        }).catch(function () { showToast('课程已更新'); loadCourses(); });
                    } else {
                        showToast('课程已更新');
                        loadCourses();
                    }
                }).catch(function () {
                    DEMO.courses.forEach(function (x) {
                        if (x.id === id) {
                            x.name = payload.name; x.code = payload.code;
                            x.description = payload.description; x.open_time = payload.open_time;
                        }
                    });
                    showToast('演示模式：课程已本地更新');
                    close();
                    renderCourses();
                    populateResCourseSelect();
                });
                close();
            });
    }

    function cloneCourse(id) {
        api.request(api.cloneCourse(id)).then(function () {
            showToast('课程已克隆为草稿');
            loadCourses();
        }).catch(function () {
            var src = DEMO.courses.find(function (c) { return c.id === id; });
            if (!src) return;
            DEMO.courses.push({
                id: ++demoId, name: src.name + '（副本）', code: src.code,
                description: src.description, cover: src.cover, status: 'draft'
            });
            showToast('演示模式：课程已本地克隆');
            renderCourses();
            populateResCourseSelect();
        });
    }

    function archiveCourse(id) {
        if (!confirm('确定归档该课程？归档后学生端不可见，可随时重新发布。')) return;
        api.request(api.archiveCourse(id)).then(function () {
            showToast('课程已归档');
            loadCourses();
        }).catch(function () {
            DEMO.courses.forEach(function (c) { if (c.id === id) c.status = 'archived'; });
            showToast('演示模式：课程已本地归档');
            renderCourses();
        });
    }

    function publishCourse(id) {
        api.request(api.publishCourse(id)).then(function () {
            showToast('课程已发布');
            loadCourses();
        }).catch(function () {
            DEMO.courses.forEach(function (c) { if (c.id === id) c.status = 'published'; });
            showToast('演示模式：课程已本地发布');
            renderCourses();
        });
    }

    async function deleteCourse(id) {
        if (!confirm('确定删除该课程？其下章节、知识点与资源将一并移除。')) return;
        try {
            await api.deleteCourse(id);
            showToast('课程已删除');
        } catch (e) {
            DEMO.courses = DEMO.courses.filter(function (c) { return c.id !== id; });
            showToast('演示模式：课程已本地删除');
        }
        if (state.courseId === id) {
            state.courseId = null;
            state.chapterId = null;
            $('chapterList').innerHTML = '<div class="empty-tip">请选择课程</div>';
            $('kpList').innerHTML = '<div class="empty-tip">请选择章节</div>';
            renderResources();
        }
        loadCourses();
    }

    // ---------- 章节 ----------
    async function loadChapters(courseId) {
        var data = await api.request(api.listChapters(courseId), DEMO.chapters[courseId] || []);
        DEMO.chapters[courseId] = data;
        if (data.length && !state.chapterId) {
            state.chapterId = data[0].id;
        }
        renderChapters();
        if (state.chapterId) {
            loadKps(state.chapterId);
        }
    }

    function renderChapters() {
        var box = $('chapterList');
        var items = (state.courseId && DEMO.chapters[state.courseId]) || [];
        if (!items.length) {
            box.innerHTML = '<div class="empty-tip">暂无章节</div>';
            return;
        }
        box.innerHTML = items.map(function (ch) {
            var active = ch.id === state.chapterId ? ' active' : '';
            return '<li class="tree-item' + active + '" data-id="' + ch.id + '">' +
                '<div class="tree-main">' + esc(ch.title) +
                (ch.description ? '<div class="desc">' + esc(ch.description) + '</div>' : '') + '</div>' +
                '<div class="tree-actions">' +
                '<button class="btn secondary small" data-act="edit">改</button>' +
                '<button class="btn danger small" data-act="del">删</button>' +
                '</div></li>';
        }).join('');
        box.querySelectorAll('.tree-item').forEach(function (li) {
            li.addEventListener('click', function (e) {
                var act = e.target.getAttribute('data-act');
                var id = Number(li.getAttribute('data-id'));
                if (act) {
                    e.stopPropagation();
                    if (act === 'edit') openEditChapterModal(id);
                    else if (act === 'del') deleteChapter(id);
                    return;
                }
                state.chapterId = id;
                renderChapters();
                $('kpChapterHint').textContent = chapterTitle(state.chapterId);
                loadKps(state.chapterId);
            });
        });
    }

    function openEditChapterModal(id) {
        var items = (state.courseId && DEMO.chapters[state.courseId]) || [];
        var ch = items.find(function (x) { return x.id === id; });
        if (!ch) return;
        openModal('编辑章节',
            '<div class="form-row"><label class="form-label">章节标题</label>' +
            '<input class="form-input" id="mTitle" value="' + esc(ch.title || '') + '"></div>' +
            '<div class="form-row"><label class="form-label">章节简介</label>' +
            '<textarea class="form-textarea" id="mDesc">' + esc(ch.description || '') + '</textarea></div>',
            function (close) {
                var title = $('mTitle').value.trim();
                if (!title) { showToast('章节标题不能为空', 'error'); return; }
                var payload = { title: title, description: $('mDesc').value.trim() };
                api.request(api.updateChapter(id, payload)).then(function () {
                    showToast('章节已更新');
                    loadChapters(state.courseId);
                }).catch(function () {
                    items.forEach(function (x) {
                        if (x.id === id) { x.title = payload.title; x.description = payload.description; }
                    });
                    showToast('演示模式：章节已本地更新');
                    close();
                    renderChapters();
                });
                close();
            });
    }

    function deleteChapter(id) {
        if (!confirm('确定删除该章节？其下知识点将一并删除。')) return;
        api.request(api.deleteChapter(id)).then(function () {
            showToast('章节已删除');
            if (state.chapterId === id) { state.chapterId = null; $('kpList').innerHTML = '<div class="empty-tip">请选择章节</div>'; }
            loadChapters(state.courseId);
        }).catch(function () {
            if (state.courseId) {
                DEMO.chapters[state.courseId] = (DEMO.chapters[state.courseId] || []).filter(function (x) { return x.id !== id; });
            }
            if (state.chapterId === id) { state.chapterId = null; $('kpList').innerHTML = '<div class="empty-tip">请选择章节</div>'; }
            showToast('演示模式：章节已本地删除');
            renderChapters();
        });
    }

    function chapterTitle(id) {
        var items = (state.courseId && DEMO.chapters[state.courseId]) || [];
        for (var i = 0; i < items.length; i++) {
            if (items[i].id === id) return items[i].title;
        }
        return '';
    }

    function openChapterModal() {
        if (!state.courseId) { showToast('请先选择课程', 'error'); return; }
        openModal('新建章节',
            '<div class="form-row"><label class="form-label">章节标题</label>' +
            '<input class="form-input" id="mTitle" placeholder="如：第一章 绪论"></div>' +
            '<div class="form-row"><label class="form-label">章节简介</label>' +
            '<textarea class="form-textarea" id="mDesc" placeholder="选填"></textarea></div>',
            function (close) {
                var title = $('mTitle').value.trim();
                if (!title) { showToast('章节标题不能为空', 'error'); return; }
                var data = { title: title, description: $('mDesc').value.trim(), sort_order: 0 };
                api.request(api.createChapter(state.courseId, data)).then(function () {
                    showToast('章节创建成功');
                    loadChapters(state.courseId);
                }).catch(function () {
                    (DEMO.chapters[state.courseId] = DEMO.chapters[state.courseId] || [])
                        .push({ id: ++demoId, title: data.title, description: data.description, sort_order: 0 });
                    showToast('演示模式：章节已本地创建');
                    close();
                    renderChapters();
                });
                close();
            });
    }

    // ---------- 知识点 ----------
    async function loadKps(chapterId) {
        var data = await api.request(api.listKnowledgePoints(chapterId), DEMO.kps[chapterId] || []);
        DEMO.kps[chapterId] = data;
        renderKps();
    }

    function renderKps() {
        var box = $('kpList');
        var items = (state.chapterId && DEMO.kps[state.chapterId]) || [];
        if (!items.length) {
            box.innerHTML = '<div class="empty-tip">暂无知识点</div>';
            return;
        }
        box.innerHTML = items.map(function (kp) {
            return '<li class="tree-item" data-id="' + kp.id + '">' +
                '<div class="tree-main">' + esc(kp.name) +
                (kp.description ? '<div class="desc">' + esc(kp.description) + '</div>' : '') + '</div>' +
                '<div class="tree-actions">' +
                '<button class="btn secondary small" data-act="edit">改</button>' +
                '<button class="btn danger small" data-act="del">删</button>' +
                '</div></li>';
        }).join('');
        box.querySelectorAll('.tree-item').forEach(function (li) {
            li.addEventListener('click', function (e) {
                var act = e.target.getAttribute('data-act');
                var id = Number(li.getAttribute('data-id'));
                if (act) {
                    e.stopPropagation();
                    if (act === 'edit') openEditKpModal(id);
                    else if (act === 'del') deleteKp(id);
                }
            });
        });
    }

    function openEditKpModal(id) {
        var items = (state.chapterId && DEMO.kps[state.chapterId]) || [];
        var kp = items.find(function (x) { return x.id === id; });
        if (!kp) return;
        openModal('编辑知识点',
            '<div class="form-row"><label class="form-label">知识点名称</label>' +
            '<input class="form-input" id="mName" value="' + esc(kp.name || '') + '"></div>' +
            '<div class="form-row"><label class="form-label">说明</label>' +
            '<textarea class="form-textarea" id="mDesc">' + esc(kp.description || '') + '</textarea></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('知识点名称不能为空', 'error'); return; }
                var payload = { name: name, description: $('mDesc').value.trim() };
                api.request(api.updateKnowledgePoint(state.chapterId, id, payload)).then(function () {
                    showToast('知识点已更新');
                    loadKps(state.chapterId);
                }).catch(function () {
                    items.forEach(function (x) {
                        if (x.id === id) { x.name = payload.name; x.description = payload.description; }
                    });
                    showToast('演示模式：知识点已本地更新');
                    close();
                    renderKps();
                });
                close();
            });
    }

    function deleteKp(id) {
        if (!confirm('确定删除该知识点？其子知识点将一并删除。')) return;
        api.request(api.deleteKnowledgePoint(state.chapterId, id)).then(function () {
            showToast('知识点已删除');
            loadKps(state.chapterId);
        }).catch(function () {
            if (state.chapterId) {
                DEMO.kps[state.chapterId] = (DEMO.kps[state.chapterId] || []).filter(function (x) { return x.id !== id; });
            }
            showToast('演示模式：知识点已本地删除');
            renderKps();
        });
    }

    function openKpModal() {
        if (!state.chapterId) { showToast('请先选择章节', 'error'); return; }
        openModal('新建知识点',
            '<div class="form-row"><label class="form-label">知识点名称</label>' +
            '<input class="form-input" id="mName" placeholder="如：递归与主定理"></div>' +
            '<div class="form-row"><label class="form-label">说明</label>' +
            '<textarea class="form-textarea" id="mDesc" placeholder="选填"></textarea></div>',
            function (close) {
                var name = $('mName').value.trim();
                if (!name) { showToast('知识点名称不能为空', 'error'); return; }
                var data = { name: name, description: $('mDesc').value.trim(), sort_order: 0 };
                api.request(api.createKnowledgePoint(state.chapterId, data)).then(function () {
                    showToast('知识点创建成功');
                    loadKps(state.chapterId);
                }).catch(function () {
                    (DEMO.kps[state.chapterId] = DEMO.kps[state.chapterId] || [])
                        .push({ id: ++demoId, name: data.name, description: data.description });
                    showToast('演示模式：知识点已本地创建');
                    close();
                    renderKps();
                });
                close();
            });
    }

    // ---------- 资源 ----------
    function populateResCourseSelect() {
        var sel = $('resCourse');
        var html = '<option value="">（个人库，不归属课程）</option>';
        DEMO.courses.forEach(function (c) {
            html += '<option value="' + c.id + '">' + esc(c.name) + '</option>';
        });
        sel.innerHTML = html;
        if (state.courseId) {
            sel.value = String(state.courseId);
        }
    }

    async function loadResources(courseId) {
        var data = await api.request(
            api.listResources(courseId ? { course_id: courseId, page: 1, page_size: 100 } : { page: 1, page_size: 100 }),
            null
        );
        if (data && data.items) {
            state.resources = data.items;
        } else {
            state.resources = DEMO.resources.filter(function (r) { return courseId ? r.course_id === courseId : true; });
        }
        renderResources();
        $('resHint').textContent = courseId ? '（' + courseName(courseId) + '）' : '（全部）';
    }

    function renderResources() {
        var tbody = $('resourceTable').querySelector('tbody');
        if (!state.resources.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty">暂无资源，请先上传</td></tr>';
            return;
        }
        tbody.innerHTML = state.resources.map(function (r) {
            var annot = (r.summary || r.keywords)
                ? '<div class="res-annot">' +
                    (r.summary ? '<div class="res-summary" title="' + esc(r.summary) + '">' + esc(truncate(r.summary, 40)) + '</div>' : '') +
                    (r.keywords ? '<div class="res-keywords">' + esc(r.keywords) + '</div>' : '') +
                    '</div>'
                : '<span class="pending-tip">—</span>';

            var sizeCell = formatSize(r.file_size);
            if (r.duration !== null && r.duration !== undefined) {
                sizeCell += ' · ' + formatDuration(r.duration);
            }

            var titleCell = esc(r.title);
            if (r.resource_type === 'video') {
                var thumb = r.thumbnail_path
                    ? '<img class="res-thumb" src="' + esc(resourceFileUrl(r, 'thumbnail')) + '" alt="">'
                    : '';
                var href = resourceFileUrl(r, r.transcoded_path ? 'transcoded' : 'original');
                titleCell = thumb +
                    '<a class="res-title" href="' + esc(href) + '" target="_blank" title="点击播放">' + esc(r.title) + '</a>';
            }

            return '<tr data-id="' + r.id + '">' +
                '<td>' + titleCell + '</td>' +
                '<td>' + (TYPE_LABEL[r.resource_type] || '其他') + '</td>' +
                '<td>' + sizeCell + '</td>' +
                '<td><select class="visibility-select" data-act="vis">' +
                ['public', 'course', 'private'].map(function (v) {
                    return '<option value="' + v + '"' + (r.visibility === v ? ' selected' : '') + '>' + VIS_LABEL[v] + '</option>';
                }).join('') + '</select></td>' +
                '<td>' + annot + '</td>' +
                '<td><div class="actions">' +
                (canPreview(r) ? '<button class="btn secondary small" data-act="preview">预览</button>' : '') +
                '<button class="btn danger small" data-act="del">删除</button></div></td>' +
                '</tr>';
        }).join('');

        tbody.querySelectorAll('tr').forEach(function (tr) {
            var id = Number(tr.getAttribute('data-id'));
            tr.querySelectorAll('[data-act]').forEach(function (el) {
                el.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var act = el.getAttribute('data-act');
                    if (act === 'del') {
                        deleteResource(id);
                    } else if (act === 'preview') {
                        previewResource(id);
                    }
                });
                el.addEventListener('change', function () {
                    if (el.getAttribute('data-act') === 'vis') {
                        setVisibility(id, el.value);
                    }
                });
            });
        });
    }

    function syncDemoResources() {
        state.resources = DEMO.resources.filter(function (r) {
            return state.courseId ? r.course_id === state.courseId : true;
        });
        renderResources();
    }

    async function setVisibility(id, visibility) {
        try {
            await api.setResourceVisibility(id, visibility);
            showToast('可见性已更新');
        } catch (e) {
            DEMO.resources.forEach(function (r) { if (r.id === id) r.visibility = visibility; });
            showToast('演示模式：可见性已本地更新');
            syncDemoResources();
        }
    }

    async function deleteResource(id) {
        if (!confirm('确定删除该资源？')) return;
        try {
            await api.deleteResource(id);
            showToast('资源已删除');
            loadResources(state.courseId);
        } catch (e) {
            DEMO.resources = DEMO.resources.filter(function (r) { return r.id !== id; });
            showToast('演示模式：资源已本地删除');
            syncDemoResources();
        }
    }

    // 在线预览：后端返回 { url, kind }（OSS 签名 URL 或本地 /uploads），浏览器新标签打开。
    async function previewResource(id) {
        try {
            var data = await api.getResourcePreview(id);
            var url = data && data.url;
            if (!url) { showToast('该资源暂不支持预览', 'error'); return; }
            window.open(fullUrl(url), '_blank');
        } catch (e) {
            showToast('预览失败：' + ((e && e.message) || '未知错误'), 'error');
        }
    }

    function handleUpload(e) {
        e.preventDefault();
        var title = $('resTitle').value.trim();
        var file = $('resFile').files[0];
        var courseId = $('resCourse').value ? Number($('resCourse').value) : null;
        if (!title && !file) { showToast('请填写标题或选择文件', 'error'); return; }
        if (!file) { showToast('请选择要上传的文件', 'error'); return; }

        var formData = new FormData();
        formData.append('title', title || file.name);
        formData.append('file', file);
        if (courseId) formData.append('course_id', String(courseId));

        api.request(api.uploadResource(formData)).then(function () {
            showToast('资源上传成功');
            loadResources(state.courseId);
        }).catch(function () {
            DEMO.resources.unshift({
                id: ++demoId, title: title || file.name,
                resource_type: typeOfFilename(file.name), file_size: file.size,
                visibility: 'course', course_id: courseId
            });
            showToast('演示模式：资源已本地添加');
            syncDemoResources();
        });
        e.target.reset();
    }

    // ---------- 初始化 ----------
    $('btnNewCourse').addEventListener('click', openCourseModal);
    $('btnNewChapter').addEventListener('click', openChapterModal);
    $('btnNewKp').addEventListener('click', openKpModal);
    $('uploadForm').addEventListener('submit', handleUpload);

    $('chapterList').innerHTML = '<div class="empty-tip">请选择课程</div>';
    $('kpList').innerHTML = '<div class="empty-tip">请选择章节</div>';

    loadCourses();
})();
