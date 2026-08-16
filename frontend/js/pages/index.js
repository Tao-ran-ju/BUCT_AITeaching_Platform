// ========== 轮播图功能 ==========
(function() {
    const banner = document.getElementById('banner');
    const items = document.querySelectorAll('.banner-item');
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let currentIndex = 0;
    let timer = null;
    const interval = 3000; // 自动轮播间隔3秒

    // 切换到指定索引
    function switchTo(index) {
        if (index < 0) index = items.length - 1;
        if (index >= items.length) index = 0;
            
        items.forEach(item => item.classList.remove('active'));
        items[index].classList.add('active');
            
        indicators.forEach(ind => ind.classList.remove('active'));
        indicators[index].classList.add('active');
            
        currentIndex = index;
    }

    prevBtn.addEventListener('click', () => switchTo(currentIndex - 1));
    nextBtn.addEventListener('click', () => switchTo(currentIndex + 1));
        
    // 指示器点击切换
    indicators.forEach((ind, index) => {
        ind.addEventListener('click', () => switchTo(index));
    });

    // 自动播放控制
    function startAutoPlay() { timer = setInterval(() => switchTo(currentIndex + 1), interval); }
    function stopAutoPlay() { clearInterval(timer); }

    banner.addEventListener('mouseenter', stopAutoPlay);
    banner.addEventListener('mouseleave', startAutoPlay);
    startAutoPlay();
})();

// ========== 时钟功能 ==========
const digitalTimeEl = document.getElementById('digitalTime');
const hourHand = document.getElementById('hourHand');
const minHand = document.getElementById('minHand');
const secHand = document.getElementById('secHand');

function padZero(n) {
    return n.toString().padStart(2, '0');
}

function updateClock() {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth() + 1;
    const d = now.getDate();
    const h = now.getHours();
    const mi = now.getMinutes();
    const s = now.getSeconds();

    digitalTimeEl.textContent = `${y}年${padZero(m)}月${padZero(d)}日 ${padZero(h)}:${padZero(mi)}:${padZero(s)}`;

    const secDeg = s * 6;
    const minDeg = mi * 6 + s * 0.1;
    const hourDeg = (h % 12) * 30 + mi * 0.5;

    secHand.style.transform = `rotate(${secDeg}deg)`;
    minHand.style.transform = `rotate(${minDeg}deg)`;
    hourHand.style.transform = `rotate(${hourDeg}deg)`;
}

// ========== 日历功能 ==========
const calHeader = document.getElementById('calHeader');
const dayGrid = document.getElementById('dayGrid');

function renderCalendar() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const todayDate = now.getDate();

    calHeader.textContent = `${year}年${month + 1}月`;
    dayGrid.innerHTML = '';

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const totalDays = lastDay.getDate();
    const startWeek = firstDay.getDay();

    const prevMonthLast = new Date(year, month, 0).getDate();

    // 填充上月日期
    for (let i = 0; i < startWeek; i++) {
        const cell = document.createElement('div');
        cell.className = 'day-cell other-month';
        cell.textContent = prevMonthLast - startWeek + 1 + i;
        dayGrid.appendChild(cell);
    }

// 填充本月日期
    for (let day = 1; day <= totalDays; day++) {
        const cell = document.createElement('div');
        cell.className = 'day-cell';
        if (day === todayDate) cell.classList.add('today');
        cell.textContent = day;
        dayGrid.appendChild(cell);
    }

// 补齐下月日期填满网格
    const totalRendered = dayGrid.children.length;
    const needFill = 42 - totalRendered;
    for (let i = 1; i <= needFill; i++) {
        const cell = document.createElement('div');
        cell.className = 'day-cell other-month';
        cell.textContent = i;
        dayGrid.appendChild(cell);
    }
}

// 初始化
updateClock();
renderCalendar();
setInterval(updateClock, 1000);
    


//快捷导航区
    
const as=document.querySelectorAll(".shortcut .wrapper ul a");
const a=document.querySelector(".shortcut .wrapper ul li:nth-child(1) a");
const underline=document.querySelector(".shortcut .wrapper .underline");
const wrapper=document.querySelector(".shortcut .wrapper");

underline.style.left=`${a.getBoundingClientRect().left-wrapper.getBoundingClientRect().left+15}px`

for(let i=0;i<as.length;i++){
    as[i].addEventListener('mouseenter',function(e){
        this.classList.add('activated');
        const a_rect=as[i].getBoundingClientRect();
        const wrapper_rect=wrapper.getBoundingClientRect();
        underline.style.left=`${a_rect.left-wrapper_rect.left+15}px`;
    })
    as[i].addEventListener('mouseleave',function(e){
        this.classList.remove('activated');
    })
}
        
