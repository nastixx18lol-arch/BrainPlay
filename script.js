// Создаем плавающие яблоки на фоне
document.addEventListener('DOMContentLoaded', function() {
    const bg = document.querySelector('.background');
    if (!bg) return;

    for (let i = 0; i < 10; i++) {
        const apple = document.createElement('div');
        apple.classList.add('floating-apple');
        apple.textContent = '🍎';
        apple.style.left = Math.random() * 100 + '%';
        apple.style.top = Math.random() * 100 + '%';
        apple.style.animationDelay = Math.random() * 5 + 's';
        apple.style.fontSize = (Math.random() * 2 + 1) + 'rem';
        bg.appendChild(apple);
    }
});