// 获取所有问答项
const qaItems = document.querySelectorAll('.qa-item');

// 遍历绑定点击事件
qaItems.forEach(item => {
    const question = item.querySelector('.question');
    question.addEventListener('click', () => {
        // 切换当前项展开状态
        item.classList.toggle('active');
    });
});
