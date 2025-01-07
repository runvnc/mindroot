export function isMobile() {
    // Primary check
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        return true;
    }

    // Secondary checks
    const checks = [
        // Touch events
        () => 'ontouchstart' in window,
        // Touch points
        () => navigator.maxTouchPoints > 0,
        // matchMedia if available
        () => window.matchMedia?.("(max-width: 768px)").matches
    ];

    return checks.some(check => {
        try {
            return check();
        } catch {
            return false;
        }
    });
}

