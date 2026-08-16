/**
 * warning.js —— 学情预警与干预页（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 触发规则引擎扫描（生成预警记录）
 *  2. 按风险等级筛选预警列表
 *  3. 对单条预警生成 AI 干预建议 / 标记已处理
 */
(function () {
    'use strict';

    var RISK_LABEL = { high: '高风险', medium: '中风险', low: '低风险' };
    var RISK_CLASS = { high: 'high', medium: 'medium', low: 'low' };
    var RISK_ICON = { high: '⛔', medium: '⚠', low: 'ℹ' };

    var DEMO = {
        warnings: [
            {
                id: 1, student_id: 101, student_name: '张伟', course_id: 1, course_name: '算法设计与分析',
                risk_level: 'high', reason: '作业正确率低于 30%；作业提交延迟 5 天',
                suggestion: '', is_resolved: false, created_at: '2024-09-20 10:00'
            },
            {
                id: 2, student_id: 102, student_name: '李娜', course_id: 1, course_name: '算法设计与分析',
                risk_level: 'medium', reason: '作业提交延迟 4 天',
                suggestion: '', is_resolved: false, created_at: '2024-09-19 09:30'
            },
            {
                id: 3, student_id: 103, student_name: '王强', course_id: 2, course_name: '数据结构',
                risk_level: 'low', reason: '作业提交延迟 1 天',
                suggestion: '', is_resolved: false, created_at: '2024-09-18 14:00'
            },
            {
                id: 4, student_id: 201, student_name: '赵敏', course_id: 2, course_name: '数据结构',
                risk_level: 'medium', reason: '作业正确率低于 30%',
                suggestion: '建议课后单独辅导，巩固线性表与指针基础，并布置针对性练习。',
                is_resolved: true, created_at: '2024-09-16 11:20'
            }
        ]
    };
    var demoId = 1000;
    var warningsCache = [];

    function $(id) { return document.getElementById(id); }

    function nowStr() {
        var d = new Date();
        function p(n) { return n < 10 ? '0' + n : '' + n; }
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
            ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    }

    // 兼容后端 ISO 格式（2024-09-20T10:00:00）与演示格式（2024-09-20 10:00）
    function fmtTime(t) {
        if (!t) return '';
        return String(t).replace('T', ' ').slice(0, 16);
    }

    function currentRisk() { return $('riskFilter').value || null; }

    // ---------- 列表 ----------
    async function loadWarnings() {
        var riskLevel = currentRisk();
        var params = { page: 1, page_size: 100 };
        if (riskLevel) params.risk_level = riskLevel;

        var fallbackItems = DEMO.warnings.filter(function (w) {
            return riskLevel ? w.risk_level === riskLevel : true;
        });
        var data = await api.request(
            api.listWarnings(params),
            { items: fallbackItems, total: fallbackItems.length }
        );
        renderWarnings((data && data.items) || []);
    }

    function renderWarnings(items) {
        warningsCache = items;
        var tbody = $('warnBody');
        $('warnCount').textContent = '共 ' + items.length + ' 条';
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty">暂无预警，点击「立即扫描」生成</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (w) {
            var cls = RISK_CLASS[w.risk_level] || 'medium';
            var label = RISK_LABEL[w.risk_level] || w.risk_level;
            var icon = RISK_ICON[w.risk_level] || '';
            var suggestionCell = w.suggestion
                ? '<div class="warn-suggestion">' + esc(w.suggestion) + '</div>'
                : '<span class="pending-tip">未生成</span>';
            var interventionCell = w.intervention
                ? '<div class="warn-intervention">' + esc(w.intervention) + '</div>'
                : '<span class="pending-tip">—</span>';
            var statusCell = w.is_resolved
                ? '<span class="badge low">已处理</span>' +
                  (w.resolved_at ? '<div class="warn-resolved-at">' + esc(fmtTime(w.resolved_at)) + '</div>' : '')
                : '<span class="badge medium">待处理</span>';
            var actions = '<div class="row-actions">' +
                '<button class="btn secondary small" data-act="suggest" data-id="' + w.id + '">AI 建议</button>' +
                (w.is_resolved
                    ? ''
                    : '<button class="btn small" data-act="resolve" data-id="' + w.id + '">标记已处理</button>') +
                '</div>';
            return '<tr>' +
                '<td>' + esc(w.student_name || ('学生#' + w.student_id)) + '</td>' +
                '<td>' + esc(w.course_name || '-') + '</td>' +
                '<td><span class="badge ' + cls + '">' + icon + ' ' + label + '</span></td>' +
                '<td><div class="warn-reason">' + esc(w.reason || '-') + '</div></td>' +
                '<td>' + suggestionCell + '</td>' +
                '<td>' + interventionCell + '</td>' +
                '<td>' + statusCell + '</td>' +
                '<td>' + actions + '</td>' +
                '</tr>';
        }).join('');

        tbody.querySelectorAll('[data-act]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var id = Number(btn.getAttribute('data-id'));
                var act = btn.getAttribute('data-act');
                if (act === 'suggest') generateSuggestion(id, btn);
                else if (act === 'resolve') resolveWarning(id);
            });
        });
    }

    // ---------- AI 建议 ----------
    function generateSuggestion(id, btn) {
        btn.disabled = true;
        btn.textContent = '生成中…';
        function done() {
            btn.disabled = false;
            btn.textContent = 'AI 建议';
            loadWarnings();
        }
        api.request(api.aiSuggestion(id)).then(function (res) {
            if (res && res.suggestion) {
                showToast('干预建议已生成');
            } else {
                showToast('后端未配置大模型，建议生成失败', 'error');
            }
            done();
        }).catch(function () {
            DEMO.warnings.forEach(function (w) {
                if (w.id === id && !w.suggestion) {
                    w.suggestion = '建议：课后安排一次 1 对 1 辅导，针对薄弱知识点布置针对性练习，并在一周后复查掌握情况。';
                }
            });
            showToast('演示模式：已本地生成建议');
            done();
        });
    }

    // ---------- 标记已处理（记录干预措施） ----------
    function resolveWarning(id) {
        var w = warningsCache.find(function (x) { return x.id === id; }) || {};
        openModal('标记预警已处理',
            '<div class="form-row"><label class="form-label">干预措施（选填）</label>' +
            '<textarea class="form-textarea" id="mIntervention" placeholder="记录本次采取的具体干预措施，如：课后 1 对 1 辅导、布置针对性练习…">' +
            esc(w.suggestion || '') + '</textarea></div>' +
            '<p class="form-hint">可先点「AI 建议」生成参考，再在此记录实际采取的措施。</p>',
            function (close) {
                var intervention = $('mIntervention').value.trim();
                api.request(api.resolveWarning(id, intervention)).then(function () {
                    showToast(intervention ? '已标记处理并记录干预措施' : '已标记处理');
                    loadWarnings();
                }).catch(function () {
                    DEMO.warnings.forEach(function (x) {
                        if (x.id === id) {
                            x.is_resolved = true;
                            x.intervention = intervention || x.suggestion || '';
                            x.resolved_at = nowStr();
                        }
                    });
                    showToast('演示模式：已本地标记处理');
                    loadWarnings();
                });
                close();
            });
    }

    // ---------- 扫描 ----------
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
            $('scanHint').textContent = '本次生成 ' + n + ' 条新预警';
            showToast('扫描完成');
            done();
        }).catch(function () {
            DEMO.warnings.unshift({
                id: ++demoId, student_id: 301, student_name: '陈晨',
                course_id: 1, course_name: '算法设计与分析',
                risk_level: 'medium', reason: '作业提交延迟 3 天',
                suggestion: '', is_resolved: false, created_at: nowStr()
            });
            $('scanHint').textContent = '演示模式：模拟生成 1 条新预警';
            showToast('演示模式：扫描完成');
            done();
        });
    }

    // ---------- 初始化 ----------
    $('btnScan').addEventListener('click', scan);
    $('riskFilter').addEventListener('change', loadWarnings);

    loadWarnings();
})();
