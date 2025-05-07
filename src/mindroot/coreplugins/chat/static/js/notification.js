/**
 * Toast notification system
 * Supports different notification types: success, error, warning, info
 * Error notifications remain on screen until manually dismissed
 */

export default async function showNotification(type, message) {
  // Create toast container if it doesn't exist
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.position = 'fixed';
    toastContainer.style.top = '20px';
    toastContainer.style.right = '20px';
    toastContainer.style.zIndex = '9999';
    document.body.appendChild(toastContainer);
    
    // Add CSS for toast container
    const style = document.createElement('style');
    style.textContent = `
      #toast-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .toast {
        min-width: 250px;
        margin-left: auto;
        padding: 15px 35px 15px 15px;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        color: white;
        font-family: sans-serif;
        animation: toast-in 0.3s ease-in-out, toast-out 0.3s ease-in-out 2.7s;
        position: relative;
        overflow: hidden;
      }
      .toast.error {
        animation: toast-in 0.3s ease-in-out;
        border-left: 4px solid #B71C1C;
      }
      .toast .close-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        cursor: pointer;
        font-size: 16px;
        opacity: 0.7;
      }
      .toast .close-btn:hover {
        opacity: 1;
      }
      .toast.success { background-color: #4CAF50; }
      .toast.error { background-color: #F44336; }
      .toast.warning { background-color: #FF9800; }
      .toast.warning { border-left: 4px solid #E65100; }
      .toast.info { background-color: #2196F3; }
      .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        background-color: rgba(255, 255, 255, 0.7);
        width: 100%;
      }
      .toast:not(.error) .toast-progress {
        /* Only animate progress bar for non-error toasts */
        animation: toast-progress 3s linear;
      }
      @keyframes toast-in {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes toast-out {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
      }
      @keyframes toast-progress {
        from { width: 100%; }
        to { width: 0%; }
      }
    `;
    document.head.appendChild(style);
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast ${type || 'info'}`;
  
  // Add aria attributes for accessibility
  toast.setAttribute('role', 'alert');
  
  // Create message span
  const messageSpan = document.createElement('span');
  messageSpan.textContent = message;
  toast.appendChild(messageSpan);
  
  // Create close button
  const closeBtn = document.createElement('span');
  closeBtn.className = 'close-btn';
  closeBtn.innerHTML = '&times;';
  closeBtn.setAttribute('aria-label', 'Close notification');
  closeBtn.addEventListener('click', () => toast.remove());
  toast.appendChild(closeBtn);
  
  // Add progress bar
  const progressBar = document.createElement('div');
  progressBar.className = 'toast-progress';
  toast.appendChild(progressBar);

  // For non-error notifications, set timeout to remove
  if (type !== 'error') {
    // Apply exit animation before removing
    setTimeout(() => {
      toast.style.animation = 'toast-out 0.3s ease-in-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
  
  // Add to container
  toastContainer.appendChild(toast);
}
