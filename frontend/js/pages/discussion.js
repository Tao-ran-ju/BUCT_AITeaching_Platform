/**
 * discussion.js —— 主题讨论区页（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 按课程浏览 / 发布主题帖子
 *  2. 置顶 / 精华帖标记（教师操作）
 *  3. 帖子回复（展开查看 + 回复）
 */
(function () {
    'use strict';

    var demoId = 1000;
    var DEMO = {
        courses: [
            { id: 1, name: '算法设计与分析' },
            { id: 2, name: '数据结构' }
        ],
        posts: [
            {
                id: 1, course_id: 1, author_id: 1, author_name: '张老师',
                title: '分治法 vs 动态规划，如何给学生讲清楚区别？',
                content: '学生在做「最长公共子序列」时总把分治和 DP 搞混，有没有好的类比或例题建议？',
                is_top: true, is_essence: true, created_at: '2024-09-20 10:00'
            },
            {
                id: 2, course_id: 1, author_id: 2, author_name: '李老师',
                title: '关于归并排序复杂度的疑问',
                content: '归并排序的辅助数组空间复杂度如何向学生解释为 O(n)？',
                is_top: false, is_essence: false, created_at: '2024-09-19 09:30'
            }
        ],
        replies: {
            1: [
                { id: 1, post_id: 1, author_id: 3, author_name: '王老师', content: '可以用「重叠子问题」作为切入点：DP 有重叠子问题，分治没有。', created_at: '2024-09-20 11:00' }
            ]
        }
    };

    var state = { courseId: null, expanded: null };

    function $(id) { return document.getElementById(id); }

    function fmtTime(t) {
        if (!t) return '-';
        return String(t).replace('T', ' ').slice(0, 16);
    }

    // ---------- 课程 ----------
    async function loadCourses() {
        var data = await api.request(
            api.listCourses({ page: 1, page_size: 100 }),
            { items: DEMO.courses, total: DEMO.courses.length }
        );
        DEMO.courses = (data && data.items) || [];
        var sel = $('postCourse');
        sel.innerHTML = DEMO.courses.map(function (c) {
            return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
        }).join('');
        if (DEMO.courses.length) {
            state.courseId = DEMO.courses[0].id;
            sel.value = String(state.courseId);
            $('postHint').textContent = '（' + DEMO.courses[0].name + '）';
            loadPosts();
        }
    }

    function courseName(id) {
        var c = DEMO.courses.find(function (x) { return x.id === id; });
        return c ? c.name : '';
    }

    $('postCourse').addEventListener('change', function () {
        state.courseId = Number(this.value);
        state.expanded = null;
        $('postHint').textContent = '（' + courseName(state.courseId) + '）';
        loadPosts();
    });

    // ---------- 帖子 ----------
    async function loadPosts() {
        if (!state.courseId) return;
        var fallback = DEMO.posts.filter(function (p) { return p.course_id === state.courseId; });
        var data = await api.request(api.listPosts(state.courseId), fallback);
        DEMO.posts = Array.isArray(data) ? data : ((data && data.items) || []);
        renderPosts();
    }

    function renderPosts() {
        var box = $('postList');
        var posts = DEMO.posts.filter(function (p) { return p.course_id === state.courseId; });
        if (!posts.length) {
            box.innerHTML = '<div class="empty-tip">暂无帖子，左侧发起第一个讨论吧</div>';
            return;
        }
        posts.sort(function (a, b) {
            if (!!b.is_top !== !!a.is_top) return b.is_top ? 1 : -1;
            return String(b.created_at || '').localeCompare(String(a.created_at || ''));
        });
        box.innerHTML = posts.map(function (p) {
            var badges = (p.is_top ? '<span class="badge medium">置顶</span>' : '') +
                (p.is_essence ? '<span class="badge low">精华</span>' : '');
            var actions = '<div class="post-actions">' +
                '<button class="btn secondary small" data-act="essence" data-id="' + p.id + '">' + (p.is_essence ? '取消精华' : '设精华') + '</button>' +
                '<button class="btn secondary small" data-act="top" data-id="' + p.id + '">' + (p.is_top ? '取消置顶' : '置顶') + '</button>' +
                '<button class="btn secondary small" data-act="reply" data-id="' + p.id + '">回复</button>' +
                '<button class="btn danger small" data-act="del" data-id="' + p.id + '">删除</button>' +
                '</div>';
            var replyArea = state.expanded === p.id
                ? '<div class="reply-area" data-replies="' + p.id + '"></div>'
                : '';
            return '<li class="post-item' + (p.is_essence ? ' essence' : '') + '">' +
                '<div class="post-head"><span class="post-title">' + esc(p.title) + '</span>' +
                badges + '</div>' +
                '<div class="post-meta">' + esc(p.author_name || ('教师#' + p.author_id)) + ' · ' + esc(fmtTime(p.created_at)) + '</div>' +
                '<div class="post-content">' + esc(p.content || '') + '</div>' +
                actions + replyArea +
                '</li>';
        }).join('');

        box.querySelectorAll('[data-act]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var id = Number(btn.getAttribute('data-id'));
                var act = btn.getAttribute('data-act');
                if (act === 'essence') toggleFlag(id, 'is_essence');
                else if (act === 'top') toggleFlag(id, 'is_top');
                else if (act === 'reply') toggleReplies(id);
                else if (act === 'del') deletePost(id);
            });
        });
    }

    function toggleFlag(id, key) {
        var p = DEMO.posts.find(function (x) { return x.id === id; });
        if (!p) return;
        var payload = {};
        payload[key] = !p[key];
        api.request(api.setPostFlags(id, payload)).then(function () {
            showToast('已更新');
            loadPosts();
        }).catch(function () {
            p[key] = !p[key];
            showToast('演示模式：已本地更新');
            renderPosts();
        });
    }

    function deletePost(id) {
        if (!confirm('确定删除该帖子？')) return;
        api.request(api.deletePost(id)).then(function () {
            showToast('帖子已删除');
            loadPosts();
        }).catch(function () {
            DEMO.posts = DEMO.posts.filter(function (x) { return x.id !== id; });
            showToast('演示模式：帖子已本地删除');
            renderPosts();
        });
    }

    // ---------- 回复 ----------
    function toggleReplies(id) {
        state.expanded = (state.expanded === id) ? null : id;
        renderPosts();
        if (state.expanded === id) loadReplies(id);
    }

    async function loadReplies(postId) {
        var fallback = DEMO.replies[postId] || [];
        var data = await api.request(api.listReplies(postId), fallback);
        DEMO.replies[postId] = Array.isArray(data) ? data : [];
        var box = document.querySelector('[data-replies="' + postId + '"]');
        if (!box) return;
        var replies = DEMO.replies[postId] || [];
        box.innerHTML = (replies.length ? '' : '<div class="empty-tip">暂无回复</div>') +
            replies.map(function (r) {
                return '<div class="reply-item">' +
                    '<span class="reply-author">' + esc(r.author_name || ('教师#' + r.author_id)) + '</span>' +
                    '<span class="reply-time">' + esc(fmtTime(r.created_at)) + '</span>' +
                    '<div class="reply-content">' + esc(r.content) + '</div></div>';
            }).join('') +
            '<div class="reply-form">' +
            '<input class="form-input" id="replyInput-' + postId + '" placeholder="写下你的回复…">' +
            '<button class="btn small" id="replyBtn-' + postId + '">回复</button></div>';

        document.getElementById('replyBtn-' + postId).addEventListener('click', function () {
            submitReply(postId);
        });
    }

    function submitReply(postId) {
        var input = document.getElementById('replyInput-' + postId);
        var content = input.value.trim();
        if (!content) { showToast('回复内容不能为空', 'error'); return; }
        api.request(api.createReply(postId, { content: content })).then(function () {
            showToast('回复成功');
            input.value = '';
            loadReplies(postId);
        }).catch(function () {
            (DEMO.replies[postId] = DEMO.replies[postId] || []).push({
                id: ++demoId, post_id: postId, author_id: 1, author_name: '我',
                content: content, created_at: new Date().toISOString()
            });
            showToast('演示模式：回复已本地添加');
            input.value = '';
            loadReplies(postId);
        });
    }

    // ---------- 发帖 ----------
    $('postForm').addEventListener('submit', function (e) {
        e.preventDefault();
        var courseId = Number($('postCourse').value);
        var title = $('postTitle').value.trim();
        var content = $('postContent').value.trim();
        if (!title) { showToast('请填写标题', 'error'); return; }
        if (!content) { showToast('请填写内容', 'error'); return; }

        api.request(api.createPost({ course_id: courseId, title: title, content: content })).then(function () {
            showToast('帖子发布成功');
            $('postTitle').value = '';
            $('postContent').value = '';
            loadPosts();
        }).catch(function () {
            DEMO.posts.unshift({
                id: ++demoId, course_id: courseId, author_id: 1, author_name: '我',
                title: title, content: content, is_top: false, is_essence: false,
                created_at: new Date().toISOString()
            });
            showToast('演示模式：帖子已本地发布');
            $('postTitle').value = '';
            $('postContent').value = '';
            renderPosts();
        });
    });

    // ---------- 初始化 ----------
    loadCourses();
})();
