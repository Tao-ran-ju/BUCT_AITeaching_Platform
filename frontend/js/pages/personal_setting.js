/**
 * personal_setting.js —— 个人设置页（混合模式：真实 API + 演示回退）
 *
 * 功能：
 *  1. 加载当前用户信息并回填表单（工号只读）
 *  2. 上传新头像（本地预览 + 真实上传到 /users/me/avatar）
 *  3. 保存基本信息（真实写入 /users/me，持久化到 MySQL）
 */
(function () {
    'use strict';

    var DEFAULT_AVATAR = '../assets/images/default_avatar.png';

    var DEMO_USER = {
        id: 1, username: 'T2024001', name: '张老师', role: 'teacher',
        department: '计算机科学与技术学院', email: 'teacher@buct.edu.cn',
        phone: '13800138000', position: '副教授', avatar: null, status: 'active'
    };

    var currentUser = null;

    function $(id) { return document.getElementById(id); }

    // 把后端返回的相对路径（/uploads/...）拼成可访问的完整地址
    function fullUrl(path) {
        if (!path) return DEFAULT_AVATAR;
        if (/^https?:\/\//.test(path)) return path;
        var origin = (window.api && api.BASE_URL)
            ? api.BASE_URL.replace(/\/api\/v1\/?$/, '')
            : '';
        var clean = path.charAt(0) === '/' ? path : '/' + path;
        return origin ? origin + clean : clean;
    }

    function setAvatar(path) {
        var url = fullUrl(path);
        $('avatarImg').src = url;
        $('previewImg').src = url;
    }

    function fillForm(user) {
        currentUser = user;
        $('teacherId').value = user.username || '';
        $('name').value = user.name || '';
        $('department').value = user.department || '';
        $('email').value = user.email || '';
        $('phone').value = user.phone || '';
        $('position').value = user.position || '';
        setAvatar(user.avatar || null);
    }

    function saveTip(msg, isError) {
        var el = $('saveTip');
        el.textContent = msg || '';
        el.style.color = isError ? '#c62828' : '#2e7d32';
        if (msg) {
            setTimeout(function () { el.textContent = ''; }, 4000);
        }
    }

    // ---------- 加载 ----------
    async function loadProfile() {
        var data = await api.request(api.getMe(), DEMO_USER);
        fillForm(data || DEMO_USER);
    }

    // ---------- 头像上传 ----------
    $('avatarFile').addEventListener('change', function (e) {
        var file = e.target.files[0];
        if (!file) return;
        if (!file.type || file.type.indexOf('image/') !== 0) {
            showToast('请选择图片文件', 'error');
            return;
        }

        // 先本地预览，再真实上传
        var reader = new FileReader();
        reader.onload = function (ev) {
            $('avatarImg').src = ev.target.result;
            $('previewImg').src = ev.target.result;
        };
        reader.readAsDataURL(file);

        var fd = new FormData();
        fd.append('file', file);
        api.request(api.uploadAvatar(fd)).then(function (res) {
            if (res && res.avatar) {
                setAvatar(res.avatar);
                if (currentUser) currentUser.avatar = res.avatar;
            }
            showToast('头像已上传并保存');
        }).catch(function () {
            showToast('演示模式：头像仅本地预览，未上传', 'error');
        });

        e.target.value = ''; // 允许再次选择同一文件
    });

    // ---------- 保存基本信息 ----------
    $('infoForm').addEventListener('submit', function (e) {
        e.preventDefault();

        var payload = {
            name: $('name').value.trim(),
            email: $('email').value.trim(),
            phone: $('phone').value.trim(),
            department: $('department').value.trim(),
            position: $('position').value.trim()
        };

        if (!payload.name) { saveTip('姓名不能为空', true); return; }
        if (!payload.email) { saveTip('邮箱不能为空', true); return; }

        var btn = document.querySelector('.save_btn');
        btn.disabled = true;
        btn.textContent = '保存中…';

        api.request(api.updateMe(payload)).then(function (res) {
            if (res && res.name) fillForm(res);
            saveTip('保存成功，已写入数据库', false);
            btn.disabled = false;
            btn.textContent = '保存修改';
        }).catch(function () {
            saveTip('演示模式：未连接后端，信息未真正保存', true);
            btn.disabled = false;
            btn.textContent = '保存修改';
        });
    });

    // 重置时回到最近一次成功加载/保存的数据
    $('infoForm').addEventListener('reset', function () {
        if (currentUser) fillForm(currentUser);
        saveTip('', false);
    });

    // ---------- 初始化 ----------
    loadProfile();
})();
