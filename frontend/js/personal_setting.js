// ========== 头像上传与实时预览 ==========
const avatarFile = document.getElementById('avatarFile');
const avatarImg = document.getElementById('avatarImg');
const previewImg = document.getElementById('previewImg');

avatarFile.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    // 校验文件类型
    if (!file.type.startsWith('image/')) {
        alert('请选择有效的图片文件');
        return;
    }

    // 读取本地图片并同步更新大图与预览
    const reader = new FileReader();
    reader.onload = function(event) {
        const imgUrl = event.target.result;
        avatarImg.src = imgUrl;
        previewImg.src = imgUrl;
    };
    reader.readAsDataURL(file);
});

// ========== 个人信息保存 ==========
const infoForm = document.getElementById('infoForm');
const saveTip = document.getElementById('saveTip');

infoForm.addEventListener('submit', function(e) {
    e.preventDefault();

    // 收集表单数据
    const userInfo = {
        teacherId: document.getElementById('teacherId').value,
        name: document.getElementById('name').value,
        department: document.getElementById('department').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        position: document.getElementById('position').value
    };

    // 基础校验
    if (!userInfo.name.trim()) {
        saveTip.textContent = '姓名不能为空';
        saveTip.style.color = '#c62828';
        return;
    }
    if (!userInfo.email.trim()) {
        saveTip.textContent = '邮箱不能为空';
        saveTip.style.color = '#c62828';
        return;
    }

    // 模拟提交（对接后端时替换为接口请求）
    saveTip.textContent = '保存成功，个人信息已更新';
    saveTip.style.color = '#2e7d32';

    setTimeout(() => {
        saveTip.textContent = '';
    }, 3000);
});

// 重置表单时清除提示
infoForm.addEventListener('reset', function() {
    saveTip.textContent = '';
});
