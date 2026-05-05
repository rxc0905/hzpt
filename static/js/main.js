// 自动关闭提示消息
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 500);
        }, 4000);
    });
});

// 确认操作
function confirmAction(msg) {
    return confirm(msg || '确认执行此操作？');
}
