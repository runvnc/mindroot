export function throttle(func, wait) {
    let lastCall = 0;
    let timeout;

    return function executedFunction(...args) {
        const now = Date.now();

        if (now - lastCall >= wait) {
            const res = func(...args);
            lastCall = now;
            return res
        } else {
            // Optional: ensure the last call still happens
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const res2 = func(...args);
                lastCall = Date.now();
                return res2
            }, wait - (now - lastCall));
        }
    };
}


