export function throttle(func, wait) {
    let lastCall = 0;
    let timeout;

    return function executedFunction(...args) {
        const now = Date.now();

        if (now - lastCall >= wait) {
            func(...args);
            lastCall = now;
        } else {
            // Optional: ensure the last call still happens
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func(...args);
                lastCall = Date.now();
            }, wait - (now - lastCall));
        }
    };
}


