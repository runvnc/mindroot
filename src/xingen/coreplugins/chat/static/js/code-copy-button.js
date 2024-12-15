// Initialize copy button functionality and expose process function
window.initializeCodeCopyButtons = (() => {
  // Style template that will be injected into both main document and shadow roots
  const styleTemplate = `
    pre > .code-copy-button {
      position: absolute;
      top: 4px;
      right: 4px;
      padding: 4px 8px;
      font-size: 12px;
      color: #fff;
      background-color: #2d2d2d;
      border: none;
      border-radius: 4px;
      opacity: 0;
      transition: all 0.2s ease;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      z-index: 1000;
    }

    pre > .code-copy-button:hover {
      background-color: #404040;
    }

    pre > .code-copy-button:active {
      transform: scale(0.95);
    }

    pre > .code-copy-button.success {
      background-color: #2ea043;
    }

    pre {
      position: relative;
    }

    pre:hover > .code-copy-button {
      opacity: 1;
    }
  `;

  // Add styles to a root (document or shadow)
  const addStylesToRoot = (root) => {
    // Check if styles already exist
    if (root.querySelector('style[data-copy-button-style]')) {
      return;
    }
    const style = document.createElement('style');
    style.setAttribute('data-copy-button-style', 'true');
    style.textContent = styleTemplate;
    if (root === document) {
      document.head.appendChild(style);
    } else {
      root.appendChild(style);
    }
  };

  // Add initial styles to main document
  addStylesToRoot(document);

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
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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

  // Process all code elements in a root (document or shadow)
  const processRoot = (root) => {
    // Add styles if this is a shadow root
    if (root instanceof ShadowRoot && !root.querySelector('style[data-copy-button-style]')) {
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

  // Process action components specifically
  const processActionComponents = () => {
    document.querySelectorAll('action-component').forEach(action => {
      if (action.shadowRoot) {
        // Add a small delay to ensure the write command content is rendered
        setTimeout(() => {
          processRoot(action.shadowRoot);
        }, 50);
      }
    });
  };

  // Main process function that will be exported
  const processCodeElements = () => {
    // Process regular elements
    processRoot(document);

    // Find all chat-message elements and process their shadow roots
    const chatMessages = document.querySelectorAll('chat-message');
    chatMessages.forEach(msg => {
      if (msg.shadowRoot) {
        processRoot(msg.shadowRoot);
      }
    });

    // Process action components specifically
    processActionComponents();

    // Process all custom elements with shadow roots
    document.querySelectorAll('*').forEach(processElement);

    // Add a small delay and process again to catch any late-initializing elements
    setTimeout(() => {
      processRoot(document);
      chatMessages.forEach(msg => {
        if (msg.shadowRoot) {
          processRoot(msg.shadowRoot);
        }
      });
      processActionComponents(); // Process action components again after delay
      document.querySelectorAll('*').forEach(processElement);
    }, 100);
  };

  // Return the process function for external use
  return processCodeElements;
})();
