(() => {
  // Style template that will be injected into both main document and shadow roots
  const styleTemplate = `
    .code-copy-button {
      position: absolute;
      top: 8px;
      right: 8px;
      padding: 8px 12px;
      font-size: 13px;
      color: #fff;
      background-color: #2d2d2d;
      border: none;
      border-radius: 4px;
      opacity: 0;
      transition: all 0.2s ease;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .code-copy-button:hover {
      background-color: #404040;
    }

    .code-copy-button:active {
      transform: scale(0.95);
    }

    .code-copy-button.success {
      background-color: #2ea043;
    }

    pre {
      position: relative;
    }

    pre:hover .code-copy-button {
      opacity: 1;
    }
  `;

  // Add styles to a root (document or shadow)
  const addStylesToRoot = (root) => {
    const style = document.createElement('style');
    style.textContent = styleTemplate;
    root.appendChild(style);
  };

  // Add initial styles to main document
  addStylesToRoot(document.head);

  // Helper function to check if element already has a copy button
  const hasCopyButton = (element) => {
    const parent = element.closest('pre');
    if (!parent) return false;
    return parent.querySelector('.code-copy-button') !== null;
  };

  // Create copy button element
  const createCopyButton = () => {
    const button = document.createElement('button');
    button.className = 'code-copy-button';
    button.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      Copy
    `;
    return button;
  };

  // Copy functionality
  const copyCode = async (codeElement) => {
    try {
      const text = codeElement.textContent;
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error('Failed to copy code:', err);
      return false;
    }
  };

  // Add copy button to code element
  const addCopyButton = (codeElement) => {
    // Skip if already has copy button
    if (hasCopyButton(codeElement)) return;

    // Only add to code elements within pre
    const pre = codeElement.closest('pre');
    if (!pre) return;

    const copyButton = createCopyButton();
    
    copyButton.addEventListener('click', async () => {
      const success = await copyCode(codeElement);
      
      if (success) {
        copyButton.classList.add('success');
        copyButton.textContent = 'Copied!';
        
        setTimeout(() => {
          copyButton.classList.remove('success');
          copyButton.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Copy
          `;
        }, 2000);
      }
    });

    pre.appendChild(copyButton);
  };

  // Throttle function
  const throttle = (func, limit) => {
    let inThrottle;
    let lastFunc;
    let lastRan;

    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        lastRan = Date.now();
        inThrottle = true;
      } else {
        clearTimeout(lastFunc);
        lastFunc = setTimeout(() => {
          if (Date.now() - lastRan >= limit) {
            func.apply(this, args);
            lastRan = Date.now();
          }
        }, limit - (Date.now() - lastRan));
      }
    };
  };

  // Process all code elements in a root (document or shadow)
  const processRoot = (root) => {
    // Add styles if this is a shadow root
    if (root instanceof ShadowRoot && !root.querySelector('style')) {
      addStylesToRoot(root);
    }
    
    // Process all code elements in this root
    root.querySelectorAll('code').forEach(addCopyButton);
  };

  // Process an element and its shadow DOM recursively
  const processElement = (element) => {
    // Process the element's own shadow root if it has one
    if (element.shadowRoot) {
      processRoot(element.shadowRoot);
    }

    // Process any shadow roots in children
    element.querySelectorAll('*').forEach(child => {
      if (child.shadowRoot) {
        processRoot(child.shadowRoot);
      }
    });
  };

  // Main process function
  const processCodeElements = () => {
    // Process main document
    processRoot(document);

    // Process all existing custom elements with shadow roots
    document.querySelectorAll('*').forEach(processElement);
  };

  // Throttled version of process function
  const throttledProcessCodeElements = throttle(processCodeElements, 500);

  // Process all existing code elements initially
  processCodeElements();

  // Watch for dynamically added elements and shadow DOM changes
  const observer = new MutationObserver((mutations) => {
    let shouldProcess = false;
    
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        for (const node of mutation.addedNodes) {
          if (node.nodeType === 1) { // Element node
            if (node.matches('code') || 
                node.querySelector('code') || 
                node.shadowRoot || 
                node.querySelector('*[shadowroot]')) {
              shouldProcess = true;
              break;
            }
          }
        }
      }
      if (shouldProcess) break;
    }

    if (shouldProcess) {
      throttledProcessCodeElements();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
})();
