/**
 * api.js —— 统一后端请求封装（混合模式：真实 API + 演示回退）
 *
 * 依赖：assets/lib/axios.min.js（需先于本文件引入）
 * 约定：后端统一响应 { code, message, data }；code === 0 视为成功。
 *
 * 说明：
 *  - 默认请求地址指向本机 FastAPI（http://127.0.0.1:8000/api/v1）。
 *  - 登录 token 存于 localStorage（key: buct_access_token），请求时自动注入。
 *  - 所有方法都返回 Promise<data>；请求失败（未登录 / 后端未启动 / 网络错误）
 *    时，调用方可使用 api.request(promise, fallback) 优雅回退到演示数据。
 *  - 可用 localStorage 覆盖：
 *      apiBaseUrl     —— 后端前缀地址
 *      buct_access_token —— 登录令牌（手动登录后写入）
 */
(function (global) {
    'use strict';

    var DEFAULT_BASE_URL = 'http://127.0.0.1:8000/api/v1';
    var TOKEN_KEY = 'buct_access_token';

    var BASE_URL = localStorage.getItem('apiBaseUrl') || DEFAULT_BASE_URL;

    // 浏览器可能以 file:// 方式直接打开页面，此时无法注入 token，全部回退演示数据
    var http = axios.create({
        baseURL: BASE_URL,
        timeout: 15000,
        headers: { 'Content-Type': 'application/json' }
    });

    // ---------- 请求拦截：注入 token ----------
    http.interceptors.request.use(function (config) {
        var token = localStorage.getItem(TOKEN_KEY);
        if (token) {
            config.headers = config.headers || {};
            config.headers.Authorization = 'Bearer ' + token;
        }
        return config;
    });

    // ---------- 错误类型 ----------
    function ApiError(code, message) {
        this.name = 'ApiError';
        this.code = code;
        this.message = message || '请求失败';
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, ApiError);
        }
    }
    ApiError.prototype = Object.create(Error.prototype);
    ApiError.prototype.constructor = ApiError;

    // ---------- 响应拦截：统一解包 ----------
    http.interceptors.response.use(
        function (resp) {
            var body = resp.data;
            if (body && typeof body === 'object' && Object.prototype.hasOwnProperty.call(body, 'code')) {
                if (body.code === 0) {
                    return body.data;
                }
                return Promise.reject(new ApiError(body.code, body.message));
            }
            return body;
        },
        function (err) {
            var resp = err.response;
            if (resp && resp.data) {
                var d = resp.data;
                return Promise.reject(new ApiError(resp.status, (d && d.message) || err.message));
            }
            return Promise.reject(new ApiError(0, err.message || '网络错误'));
        }
    );

    // ---------- 兜底请求：失败时返回 fallback ----------
    function request(promise, fallback) {
        return Promise.resolve(promise).catch(function () {
            if (fallback !== undefined) {
                return fallback;
            }
            return Promise.reject(new ApiError(0, '请求失败'));
        });
    }

    // ---------- 接口清单 ----------
    var api = {
        http: http,
        ApiError: ApiError,
        request: request,
        BASE_URL: BASE_URL,

        // 认证
        login: function (data) { return http.post('/auth/login', data); },
        register: function (data) { return http.post('/auth/register', data); },

        // 用户
        getMe: function () { return http.get('/users/me'); },
        updateMe: function (data) { return http.put('/users/me', data); },
        uploadAvatar: function (formData) { return http.post('/users/me/avatar', formData, { headers: { 'Content-Type': 'multipart/form-data' } }); },
        changePassword: function (data) { return http.post('/users/me/password', data); },
        listUsers: function (params) { return http.get('/users', { params: params }); },

        // 课程
        listCourses: function (params) { return http.get('/courses', { params: params }); },
        getCourse: function (id) { return http.get('/courses/' + id); },
        createCourse: function (data) { return http.post('/courses', data); },
        updateCourse: function (id, data) { return http.put('/courses/' + id, data); },
        deleteCourse: function (id) { return http.delete('/courses/' + id); },
        cloneCourse: function (id) { return http.post('/courses/' + id + '/clone'); },
        archiveCourse: function (id) { return http.post('/courses/' + id + '/archive'); },
        publishCourse: function (id) { return http.post('/courses/' + id + '/publish'); },
        uploadCourseCover: function (id, formData) { return http.post('/courses/' + id + '/cover', formData, { headers: { 'Content-Type': 'multipart/form-data' } }); },
        listChapters: function (courseId) { return http.get('/courses/' + courseId + '/chapters'); },
        createChapter: function (courseId, data) { return http.post('/courses/' + courseId + '/chapters', data); },
        updateChapter: function (chapterId, data) { return http.put('/courses/chapters/' + chapterId, data); },
        deleteChapter: function (chapterId) { return http.delete('/courses/chapters/' + chapterId); },
        listKnowledgePoints: function (chapterId) { return http.get('/courses/chapters/' + chapterId + '/knowledge-points'); },
        createKnowledgePoint: function (chapterId, data) { return http.post('/courses/chapters/' + chapterId + '/knowledge-points', data); },
        updateKnowledgePoint: function (chapterId, kpId, data) { return http.put('/courses/chapters/' + chapterId + '/knowledge-points/' + kpId, data); },
        deleteKnowledgePoint: function (chapterId, kpId) { return http.delete('/courses/chapters/' + chapterId + '/knowledge-points/' + kpId); },

        // 班级
        listClasses: function (params) { return http.get('/classes', { params: params }); },
        createClass: function (data) { return http.post('/classes', data); },
        updateClass: function (id, data) { return http.put('/classes/' + id, data); },
        deleteClass: function (id) { return http.delete('/classes/' + id); },
        listClassStudents: function (id) { return http.get('/classes/' + id + '/students'); },
        addClassStudents: function (id, studentIds) { return http.post('/classes/' + id + '/students', { student_ids: studentIds }); },
        removeClassStudent: function (id, studentId) { return http.delete('/classes/' + id + '/students/' + studentId); },

        // 教学资源
        uploadResource: function (formData) { return http.post('/resources', formData, { headers: { 'Content-Type': 'multipart/form-data' } }); },
        listResources: function (params) { return http.get('/resources', { params: params }); },
        setResourceVisibility: function (id, visibility) { return http.patch('/resources/' + id + '/visibility', { visibility: visibility }); },
        deleteResource: function (id) { return http.delete('/resources/' + id); },

        // 作业
        listAssignments: function (courseId) { return http.get('/assignments', { params: { course_id: courseId } }); },
        createAssignment: function (data) { return http.post('/assignments', data); },
        listSubmissions: function (id) { return http.get('/assignments/' + id + '/submissions'); },
        judgeAssignment: function (id) { return http.post('/assignments/' + id + '/judge'); },
        checkPlagiarism: function (id) { return http.post('/assignments/' + id + '/plagiarism'); },

        // 消息通知（教师端发布通知 / 作业，与学生端消息系统对接）
        listSentMessages: function () { return http.get('/messages/sent'); },
        sendMessage: function (formData) { return http.post('/messages', formData, { headers: { 'Content-Type': 'multipart/form-data' } }); },

        // AI 问答助手（学生提问 -> 自动分流 -> 教师人工回复）
        askQuestion: function (data) { return http.post('/qa/ask', data); },
        listQaQuestions: function () { return http.get('/qa/questions'); },
        answerQuestion: function (id, data) { return http.post('/qa/' + id + '/answer', data); },

        // AI 备课中心
        generatePlan: function (data) { return http.post('/teaching/plan', data); },
        generateOutline: function (data) { return http.post('/teaching/outline', data); },
        generatePpt: function (data) { return http.post('/teaching/ppt', data); },
        generateQuiz: function (data) { return http.post('/teaching/quiz', data); },
        generateExamPaper: function (data) { return http.post('/teaching/exam-paper', data); },
        reviewQuestion: function (question) { return http.post('/teaching/question-review', { question: question }); },
        designProject: function (data) { return http.post('/teaching/project', data); },
        generateReport: function (data) { return http.post('/teaching/report', data); },
        summarizeResource: function (content) { return http.post('/teaching/summarize', { content: content }); },

        // 主题讨论区
        listPosts: function (courseId) { return http.get('/discussions', { params: { course_id: courseId } }); },
        createPost: function (data) { return http.post('/discussions', data); },
        setPostFlags: function (postId, data) { return http.patch('/discussions/' + postId, data); },
        deletePost: function (postId) { return http.delete('/discussions/' + postId); },
        listReplies: function (postId) { return http.get('/discussions/' + postId + '/replies'); },
        createReply: function (postId, data) { return http.post('/discussions/' + postId + '/replies', data); },

        // 学习小组
        listTeams: function (params) { return http.get('/teams', { params: params }); },
        createTeam: function (data) { return http.post('/teams', data); },
        updateTeam: function (id, data) { return http.put('/teams/' + id, data); },
        deleteTeam: function (id) { return http.delete('/teams/' + id); },
        addTeamMembers: function (id, studentIds) { return http.post('/teams/' + id + '/members', { student_ids: studentIds }); },
        removeTeamMember: function (id, studentId) { return http.delete('/teams/' + id + '/members/' + studentId); },

        // 学习任务
        listTasks: function (params) { return http.get('/tasks', { params: params }); },
        createTask: function (data) { return http.post('/tasks', data); },
        updateTask: function (id, data) { return http.put('/tasks/' + id, data); },
        deleteTask: function (id) { return http.delete('/tasks/' + id); },
        completeTask: function (id) { return http.post('/tasks/' + id + '/complete'); },

        // 学情预警
        scanWarnings: function () { return http.post('/warnings/scan'); },
        listWarnings: function (params) { return http.get('/warnings', { params: params }); },
        aiSuggestion: function (id) { return http.post('/warnings/' + id + '/suggestion'); },
        resolveWarning: function (id, intervention) { return http.post('/warnings/' + id + '/resolve', { intervention: intervention }); },

        // 数据驾驶舱
        dashboardOverview: function () { return http.get('/dashboard/overview'); },
        dashboardHeatmap: function (courseId) { return http.get('/dashboard/heatmap', { params: courseId ? { course_id: courseId } : {} }); },
        taskProgress: function () { return http.get('/dashboard/task-progress'); },
        scoreDistribution: function () { return http.get('/dashboard/score-distribution'); },
        effectCompare: function () { return http.get('/dashboard/effect-compare'); }
    };

    global.api = api;
    global.ApiError = ApiError;
    global.API_BASE_URL = BASE_URL;
})(window);
