/**
 * common.js —— 共享导航脚本
 *
 * 功能：
 *  1. 根据当前页面文件名高亮对应导航项（加 .activated，下划线定位到该项）。
 *  2. 鼠标悬停时下划线跟随，移开后回到当前激活项。
 *
 * 依赖 DOM 结构：.shortcut .wrapper 下 ul > li > a，以及 .underline 元素。
 * 各功能页只需引入本文件，无需再写内联导航脚本。
 */
(function () {
    'use strict';

    var links = document.querySelectorAll('.shortcut .wrapper ul a');
    var underline = document.querySelector('.shortcut .wrapper .underline');
    var wrapper = document.querySelector('.shortcut .wrapper');

    if (!links.length || !underline || !wrapper) {
        return;
    }

    // 当前文件名（去掉路径与查询串），空则视为 index.html
    var current = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    var activeLink = null;

    function moveUnderline(link) {
        var aRect = link.getBoundingClientRect();
        var wrapperRect = wrapper.getBoundingClientRect();
        underline.style.left = (aRect.left - wrapperRect.left + 15) + 'px';
    }

    // 高亮当前页
    links.forEach(function (link) {
        var href = (link.getAttribute('href') || '').split('?')[0];
        var name = (href.split('/').pop() || 'index.html').toLowerCase();
        if (name === current) {
            activeLink = link;
            link.classList.add('activated');
            moveUnderline(link);
        }

        link.addEventListener('mouseenter', function () {
            link.classList.add('activated');
            moveUnderline(link);
        });
        link.addEventListener('mouseleave', function () {
            link.classList.remove('activated');
            if (activeLink) {
                activeLink.classList.add('activated');
                moveUnderline(activeLink);
            }
        });
    });

    // 窗口尺寸变化时校正下划线位置
    window.addEventListener('resize', function () {
        if (activeLink) {
            moveUnderline(activeLink);
        }
    });
})();

/**
 * showToast —— 轻量提示条（各功能页共享）
 * @param {string} message 提示文本
 * @param {string} type    'success' | 'error'，默认 success
 */
window.showToast = function (message, type) {
    type = type || 'success';
    var toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
        toast.className = 'toast ' + type;
    }, 2500);
};

/**
 * esc —— HTML 转义，避免用户输入注入页面。
 * @param {*} value 任意值
 * @returns {string}
 */
window.esc = function (value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
};

/**
 * 通用模态框（依赖页面中存在 #modalMask / #modalTitle / #modalBody / #modalOk 等结构）
 * @param {string}   title    标题
 * @param {string}   bodyHTML 正文 HTML
 * @param {Function} onOk     点击「确定」时的回调
 */
window.openModal = function (title, bodyHTML, onOk) {
    var mask = document.getElementById('modalMask');
    if (!mask) {
        return;
    }
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = bodyHTML;

    var okBtn = document.getElementById('modalOk');
    var cancelBtn = document.getElementById('modalCancel');
    var closeBtn = document.getElementById('modalClose');

    function close() {
        mask.classList.remove('show');
        okBtn.onclick = null;
        cancelBtn.onclick = null;
        closeBtn.onclick = null;
    }

    okBtn.onclick = function () {
        if (onOk) {
            onOk(close);
        } else {
            close();
        }
    };
    cancelBtn.onclick = close;
    closeBtn.onclick = close;
    // 用 onmouseclick 覆盖赋值，避免重复 open 时累积监听器
    mask.onclick = function (e) {
        if (e.target === mask) {
            close();
        }
    };

    mask.classList.add('show');
};

window.closeModal = function () {
    var mask = document.getElementById('modalMask');
    if (mask) {
        mask.classList.remove('show');
    }
};
