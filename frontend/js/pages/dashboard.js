/**
 * dashboard.js —— 数据驾驶舱（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 核心指标卡（学生/教师总数、资源数、作业通过率、平均分）
 *  2. 能力矩阵热力图（按知识点排行，顺序单色紫色渐变，直接标注数值）
 *  3. 学习不积极学生 · 学情预警（扫描 + 未处理预警列表，一键标记处理）
 *
 * 热力图取值 0–1，采用品牌紫的单色顺序渐变（浅 → 深，浅色表示接近 0）。
 */
(function () {
    'use strict';

    var DEMO = {
        metrics: [
            { key: 'total_users', label: '教师与学生总数', value: 128, unit: '', trend: null },
            { key: 'total_resources', label: '教学资源数', value: 46, unit: '', trend: null },
            { key: 'pass_rate', label: '作业通过率', value: 82.5, unit: '%', trend: null },
            { key: 'avg_score', label: '平均分', value: 78.3, unit: '分', trend: null }
        ],
        courses: [
            { id: 1, name: '算法设计与分析' },
            { id: 2, name: '数据结构' }
        ],
        heatmap: [
            { knowledge_point: '线性表', value: 0.91 },
            { knowledge_point: '分治法', value: 0.86 },
            { knowledge_point: '树与二叉树', value: 0.80 },
            { knowledge_point: '动态规划', value: 0.72 },
            { knowledge_point: '图论', value: 0.65 },
            { knowledge_point: '贪心算法', value: 0.58 },
            { knowledge_point: '排序算法', value: 0.49 }
        ],
        warnings: [
            { id: 1, student_id: 101, student_name: '张伟', course_id: 1, course_name: '算法设计与分析', risk_level: 'high', reason: '作业正确率低于 30%；近期日均登录时长 120 秒，学习不积极', suggestion: '', is_resolved: false },
            { id: 2, student_id: 102, student_name: '李娜', course_id: 1, course_name: '算法设计与分析', risk_level: 'medium', reason: '近期日均资源访问 1 次，学习不积极', suggestion: '', is_resolved: false },
            { id: 3, student_id: 103, student_name: '王强', course_id: 2, course_name: '数据结构', risk_level: 'medium', reason: '作业提交延迟 4 天', suggestion: '', is_resolved: false },
            { id: 4, student_id: 201, student_name: '赵敏', course_id: 2, course_name: '数据结构', risk_level: 'low', reason: '近期日均登录时长 540 秒，学习不积极', suggestion: '', is_resolved: false }
        ],
        taskProgress: {
            student_cols: [
                { student_id: 101, name: '张伟' },
                { student_id: 102, name: '李娜' },
                { student_id: 103, name: '王强' },
                { student_id: 201, name: '赵敏' },
                { student_id: 202, name: '刘洋' }
            ],
            tasks: [
                { task_id: 1, title: '完成「动态规划」知识点学习', course_name: '算法设计与分析', deadline: '2024-09-28 23:59', total: 3, completed: 1, rate: 0.33, cells: { 101: 'completed', 102: 'pending', 103: 'pending' } },
                { task_id: 2, title: '完成「二叉树遍历」实验', course_name: '数据结构', deadline: '2024-09-25 23:59', total: 2, completed: 2, rate: 1, cells: { 201: 'completed', 202: 'completed' } }
            ]
        },
        scoreDistribution: {
            buckets: [
                { range: '0-59', label: '不及格', count: 3 },
                { range: '60-69', label: '及格', count: 8 },
                { range: '70-79', label: '中等', count: 15 },
                { range: '80-89', label: '良好', count: 10 },
                { range: '90-100', label: '优秀', count: 4 }
            ],
            total: 40
        },
        effectCompare: [
            { course_id: 1, course_name: '算法设计与分析', avg_score: 82.4, pass_rate: 0.91, submission_count: 42 },
            { course_id: 2, course_name: '数据结构', avg_score: 74.8, pass_rate: 0.82, submission_count: 38 },
            { course_id: 3, course_name: '程序设计基础', avg_score: 68.5, pass_rate: 0.71, submission_count: 55 }
        ]
    };

    // 品牌紫单色顺序渐变（浅 → 深）
    var RAMP = [
        { t: 0.00, c: '#eadcfb' },
        { t: 0.25, c: '#c9a9ef' },
        { t: 0.50, c: '#a478e0' },
        { t: 0.75, c: '#7d3ec4' },
        { t: 1.00, c: '#5a1a9b' }
    ];

    var RISK_LABEL = { high: '高风险', medium: '中风险', low: '低风险' };
    var RISK_CLASS = { high: 'high', medium: 'medium', low: 'low' };
    var RISK_ICON = { high: '⛔', medium: '⚠', low: 'ℹ' };
    var RISK_ORDER = { high: 0, medium: 1, low: 2 };
    var demoId = 1000;

    function $(id) { return document.getElementById(id); }

    function nowStr() {
        var d = new Date();
        function p(n) { return n < 10 ? '0' + n : '' + n; }
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
            ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    }

    function fmtTime(t) {
        if (!t) return '';
        return String(t).replace('T', ' ').slice(0, 16);
    }

    function rampColor(v) {
        v = Math.max(0, Math.min(1, v));
        for (var i = 0; i < RAMP.length - 1; i++) {
            var a = RAMP[i], b = RAMP[i + 1];
            if (v >= a.t && v <= b.t) {
                return mix(a.c, b.c, (v - a.t) / (b.t - a.t));
            }
        }
        return RAMP[RAMP.length - 1].c;
    }

    function mix(c1, c2, t) {
        function ch(s, o) { return parseInt(s.substr(o, 2), 16); }
        var r = Math.round(ch(c1, 1) + (ch(c2, 1) - ch(c1, 1)) * t);
        var g = Math.round(ch(c1, 3) + (ch(c2, 3) - ch(c1, 3)) * t);
        var b = Math.round(ch(c1, 5) + (ch(c2, 5) - ch(c1, 5)) * t);
        return 'rgb(' + r + ',' + g + ',' + b + ')';
    }

    function fmtNumber(v) {
        if (typeof v === 'number' && !Number.isInteger(v)) return v.toFixed(1);
        return String(v);
    }

    function riskRank(r) {
        return Object.prototype.hasOwnProperty.call(RISK_ORDER, r) ? RISK_ORDER[r] : 2;
    }

    // ---------- 指标卡 ----------
    async function loadMetrics() {
        var data = await api.request(api.dashboardOverview(), { metrics: DEMO.metrics, heatmap: [] });
        var metrics = (data && data.metrics) || DEMO.metrics;
        renderMetrics(metrics);
    }

    function renderMetrics(metrics) {
        var box = $('metricGrid');
        if (!metrics.length) {
            box.innerHTML = '<div class="empty-tip">暂无数据</div>';
            return;
        }
        box.innerHTML = metrics.map(function (m) {
            var trend = '';
            if (m.trend != null && m.trend !== 0) {
                var up = m.trend > 0;
                trend = '<div class="metric-trend ' + (up ? 'up' : 'down') + '">' +
                    (up ? '▲' : '▼') + ' ' + Math.abs(m.trend) + '%</div>';
            }
            return '<div class="metric-card">' +
                '<div class="metric-label">' + esc(m.label) + '</div>' +
                '<div class="metric-value">' + fmtNumber(m.value) +
                '<span class="metric-unit">' + esc(m.unit || '') + '</span></div>' +
                trend + '</div>';
        }).join('');
    }

    // ---------- 能力矩阵热力图 ----------
    async function loadHeatmap(courseId) {
        var data = await api.request(api.dashboardHeatmap(courseId), DEMO.heatmap);
        var cells = Array.isArray(data) ? data : ((data && data.items) || []);
        renderHeatmap(cells);
    }

    function renderHeatmap(cells) {
        var box = $('heatmap');
        if (!cells.length) {
            box.innerHTML = '<div class="empty-tip">暂无能力数据</div>';
            return;
        }
        var sorted = cells.slice().sort(function (a, b) { return (b.value || 0) - (a.value || 0); });
        box.innerHTML = sorted.map(function (c) {
            var v = Math.max(0, Math.min(1, c.value || 0));
            var pct = Math.round(v * 100);
            return '<div class="heat-row">' +
                '<div class="heat-name" title="' + esc(c.knowledge_point) + '">' + esc(c.knowledge_point) + '</div>' +
                '<div class="heat-track"><div class="heat-fill" style="width:' + pct + '%;background:' + rampColor(v) + ';"></div></div>' +
                '<div class="heat-val">' + pct + '%</div>' +
                '</div>';
        }).join('');
    }

    // ---------- 任务进度热力图 ----------
    async function loadTaskProgress() {
        var data = await api.request(api.taskProgress(), DEMO.taskProgress);
        var cols = (data && data.student_cols) || [];
        var tasks = (data && data.tasks) || [];
        renderTaskProgress(cols, tasks);
    }

    function cellClass(status, deadline) {
        if (status === 'completed') return 'completed';
        if (deadline && fmtTime(deadline) < nowStr()) return 'overdue';
        return 'pending';
    }

    function renderTaskProgress(cols, tasks) {
        var box = $('taskHeatmap');
        if (!tasks.length) {
            box.innerHTML = '<div class="empty-tip">暂无学习任务</div>';
            return;
        }
        var head = '<div class="task-heat-row task-heat-head">' +
            '<div class="th-name">任务</div>' +
            cols.map(function (s) {
                return '<div class="th-cell">' + esc(s.name) + '</div>';
            }).join('') +
            '<div class="th-rate">进度</div></div>';
        var body = tasks.map(function (t) {
            var cellMap = t.cells || {};
            var cellsHtml = cols.map(function (s) {
                var status = cellMap[String(s.student_id)] || 'pending';
                var cls = cellClass(status, t.deadline);
                var label = status === 'completed' ? '已完成' : (cls === 'overdue' ? '已截止未完成' : '未完成');
                return '<div class="th-cell"><i class="cell ' + cls + '" title="' +
                    esc(s.name) + ' · ' + label + '"></i></div>';
            }).join('');
            return '<div class="task-heat-row">' +
                '<div class="th-name" title="' + esc(t.title) + '">' + esc(t.title) + '</div>' +
                cellsHtml +
                '<div class="th-rate">' + (t.completed || 0) + '/' + (t.total || 0) + '</div>' +
                '</div>';
        }).join('');
        box.innerHTML = head + body;
    }

    // ---------- 成绩分布 ----------
    async function loadScoreDistribution() {
        var data = await api.request(api.scoreDistribution(), DEMO.scoreDistribution);
        var buckets = (data && data.buckets) || [];
        renderScoreChart(buckets);
    }

    function renderScoreChart(buckets) {
        var box = $('scoreChart');
        if (!buckets.length) {
            box.innerHTML = '<div class="empty-tip">暂无成绩数据</div>';
            return;
        }
        var max = Math.max.apply(null, buckets.map(function (b) { return b.count || 0; })) || 1;
        box.innerHTML = buckets.map(function (b) {
            var h = Math.round((b.count || 0) / max * 100);
            return '<div class="bar-col">' +
                '<div class="bar-count">' + b.count + '</div>' +
                '<div class="bar" style="height:' + h + '%;background:' + rampColor((b.count || 0) / max) + ';"></div>' +
                '<div class="bar-label">' + esc(b.label) + '</div>' +
                '<div class="bar-range">' + esc(b.range) + '</div>' +
                '</div>';
        }).join('');
    }

    // ---------- 教学效果对比 ----------
    async function loadEffectCompare() {
        var data = await api.request(api.effectCompare(), DEMO.effectCompare);
        var items = Array.isArray(data) ? data : [];
        renderEffectChart(items);
    }

    function renderEffectChart(items) {
        var box = $('effectChart');
        if (!items.length) {
            box.innerHTML = '<div class="empty-tip">暂无数据</div>';
            return;
        }
        var max = Math.max.apply(null, items.map(function (i) { return i.avg_score || 0; })) || 100;
        box.innerHTML = items.map(function (i) {
            var w = Math.round((i.avg_score || 0) / max * 100);
            var pass = Math.round((i.pass_rate || 0) * 100);
            return '<div class="effect-row">' +
                '<div class="effect-name" title="' + esc(i.course_name) + '">' + esc(i.course_name) + '</div>' +
                '<div class="effect-track"><div class="effect-fill" style="width:' + w + '%;background:' + rampColor((i.avg_score || 0) / 100) + ';"></div></div>' +
                '<div class="effect-score">' + fmtNumber(i.avg_score) + ' 分</div>' +
                '<div class="effect-pass">通过率 ' + pass + '%</div>' +
                '</div>';
        }).join('');
    }

    // ---------- 课程筛选 ----------
    async function loadCourses() {
        var data = await api.request(
            api.listCourses({ page: 1, page_size: 100 }),
            { items: DEMO.courses, total: DEMO.courses.length }
        );
        var courses = (data && data.items) || [];
        $('courseFilter').innerHTML = '<option value="">全部课程</option>' +
            courses.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');
    }

    // ---------- 学习不积极学生 · 学情预警 ----------
    async function loadWarnings() {
        var data = await api.request(
            api.listWarnings({ page: 1, page_size: 100 }),
            { items: DEMO.warnings, total: DEMO.warnings.length }
        );
        var items = (data && data.items) || [];
        var active = items.filter(function (w) { return !w.is_resolved; });
        active.sort(function (a, b) { return riskRank(a.risk_level) - riskRank(b.risk_level); });
        renderWarnings(active.slice(0, 8));
    }

    function renderWarnings(items) {
        var box = $('dashWarningList');
        $('warnCount').textContent = items.length ? ('未处理 ' + items.length + ' 条') : '暂无待关注学生';
        if (!items.length) {
            box.innerHTML = '<div class="empty-tip">暂无学习不积极学生，点击「立即扫描」检测</div>';
            return;
        }
        box.innerHTML = items.map(function (w) {
            var cls = RISK_CLASS[w.risk_level] || 'medium';
            var label = RISK_LABEL[w.risk_level] || w.risk_level;
            var icon = RISK_ICON[w.risk_level] || '';
            return '<div class="dash-warn-item">' +
                '<div class="dash-warn-left">' +
                    '<span class="badge ' + cls + '">' + icon + ' ' + label + '</span>' +
                    '<span class="dash-warn-name">' + esc(w.student_name || ('学生#' + w.student_id)) + '</span>' +
                    (w.course_name ? '<span class="dash-warn-course">' + esc(w.course_name) + '</span>' : '') +
                '</div>' +
                '<div class="dash-warn-reason">' + esc(w.reason || '-') + '</div>' +
                '<button class="btn small secondary" data-act="resolve" data-id="' + w.id + '">标记已处理</button>' +
                '</div>';
        }).join('');

        box.querySelectorAll('[data-act="resolve"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                resolveWarning(Number(btn.getAttribute('data-id')));
            });
        });
    }

    function resolveWarning(id) {
        api.request(api.resolveWarning(id)).then(function () {
            showToast('已标记处理');
            loadWarnings();
        }).catch(function () {
            DEMO.warnings.forEach(function (w) { if (w.id === id) w.is_resolved = true; });
            showToast('演示模式：已本地标记处理');
            loadWarnings();
        });
    }

    function scan() {
        var btn = $('btnScan');
        btn.disabled = true;
        btn.textContent = '扫描中…';
        function done() {
            btn.disabled = false;
            btn.textContent = '立即扫描';
            loadWarnings();
        }
        api.request(api.scanWarnings()).then(function (res) {
            var n = (res && res.generated != null) ? res.generated : 0;
            showToast('扫描完成，生成 ' + n + ' 条新预警');
            done();
        }).catch(function () {
            DEMO.warnings.unshift({
                id: ++demoId, student_id: 301, student_name: '陈晨',
                course_id: 1, course_name: '算法设计与分析',
                risk_level: 'medium', reason: '近期日均登录时长 300 秒，学习不积极',
                suggestion: '', is_resolved: false
            });
            showToast('演示模式：扫描完成');
            done();
        });
    }

    // ---------- 事件 ----------
    $('courseFilter').addEventListener('change', function () {
        loadHeatmap(this.value ? Number(this.value) : null);
    });
    $('btnScan').addEventListener('click', scan);

    // ---------- 初始化 ----------
    loadMetrics();
    loadHeatmap(null);
    loadCourses();
    loadTaskProgress();
    loadScoreDistribution();
    loadEffectCompare();
    loadWarnings();
})();
