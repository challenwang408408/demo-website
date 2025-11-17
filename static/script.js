// 页面交互脚本
document.addEventListener('DOMContentLoaded', function() {
    // 导航按钮切换
    const navButtons = document.querySelectorAll('.cyber-btn');
    const contentSections = document.querySelectorAll('.content-section');
    
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            
            // 移除所有活动状态
            navButtons.forEach(btn => btn.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));
            
            // 添加活动状态
            this.classList.add('active');
            const targetSection = document.getElementById(target);
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });
    
    // 朝代卡片点击跳转
    const dynastyCards = document.querySelectorAll('.dynasty-card');
    dynastyCards.forEach(card => {
        card.addEventListener('click', function() {
            const dynasty = this.getAttribute('data-dynasty');
            if (dynasty) {
                // 找到对应的按钮并点击
                const targetButton = Array.from(navButtons).find(btn => 
                    btn.getAttribute('data-target') === dynasty
                );
                if (targetButton) {
                    targetButton.click();
                }
            }
        });
    });
    
    // 添加鼠标跟随效果
    document.addEventListener('mousemove', function(e) {
        const cursor = document.querySelector('.cursor-glow');
        if (!cursor) {
            const glow = document.createElement('div');
            glow.className = 'cursor-glow';
            glow.style.cssText = `
                position: fixed;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(0,255,255,0.5), transparent);
                pointer-events: none;
                z-index: 9999;
                transition: transform 0.1s;
            `;
            document.body.appendChild(glow);
        }
        
        const glow = document.querySelector('.cursor-glow');
        glow.style.left = e.clientX - 10 + 'px';
        glow.style.top = e.clientY - 10 + 'px';
    });
    
    // 添加粒子效果
    createParticles();
});

// 创建背景粒子效果
function createParticles() {
    const particleCount = 50;
    const container = document.querySelector('.cyber-container');
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: fixed;
            width: 2px;
            height: 2px;
            background: var(--cyber-cyan);
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            box-shadow: 0 0 6px var(--cyber-cyan);
            opacity: ${Math.random() * 0.5 + 0.2};
        `;
        
        const startX = Math.random() * window.innerWidth;
        const startY = Math.random() * window.innerHeight;
        const duration = Math.random() * 3 + 2;
        const delay = Math.random() * 2;
        
        particle.style.left = startX + 'px';
        particle.style.top = startY + 'px';
        
        container.appendChild(particle);
        
        // 动画
        particle.animate([
            { 
                transform: 'translate(0, 0)',
                opacity: 0.2
            },
            {
                transform: `translate(${(Math.random() - 0.5) * 200}px, ${(Math.random() - 0.5) * 200}px)`,
                opacity: 0.8
            },
            {
                transform: `translate(${(Math.random() - 0.5) * 400}px, ${(Math.random() - 0.5) * 400}px)`,
                opacity: 0.2
            }
        ], {
            duration: duration * 1000,
            delay: delay * 1000,
            iterations: Infinity,
            easing: 'ease-in-out'
        });
    }
}

// 添加键盘导航支持
document.addEventListener('keydown', function(e) {
    const navButtons = Array.from(document.querySelectorAll('.cyber-btn'));
    const activeIndex = navButtons.findIndex(btn => btn.classList.contains('active'));
    
    if (e.key === 'ArrowRight' && activeIndex < navButtons.length - 1) {
        navButtons[activeIndex + 1].click();
    } else if (e.key === 'ArrowLeft' && activeIndex > 0) {
        navButtons[activeIndex - 1].click();
    }
});

