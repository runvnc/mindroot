import { Marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';

class MarkdownRenderer {
    constructor() {
        this.marked = new Marked();

        // Configure marked with custom renderer
        const renderer = {
            code: (code, language) => {
                let text = code.text
                try {                    
                    console.log('Highlighting code:', code);
                    const lang = code.lang
                    if (!lang) {
                      const result = hljs.highlightAuto(text)
                      return `<pre><code class="hljs">${result.value}</code></pre>`;
                    } else if (lang == 'math') {
                      text = katex.renderToString(text), { throwOnError: true, displayMode: false }
                      return `<p>${text}</p>`;
                    } else {
                      const result = hljs.highlight(lang, text);
                      return `<pre><code class="hljs">${result.value}</code></pre>`;
                    }
                } catch (e) {
                    console.warn('Highlighting failed:', e);
                    return ''// `<p>${text}</p>`;
                }
            }
        };

        this.marked.use({ renderer });
    }

    parse(markdown) {
        if (typeof markdown !== 'string') {
            console.warn('Received non-string markdown:', markdown);
            markdown = String(markdown);
        }
        try {
            return this.marked.parse(markdown, { async: false });
        } catch (e) {
            console.error('Markdown parsing failed:', e);
            return `<pre><code>${markdown}</code></pre>`;
        }
    }
}

// Create and export singleton instance
export const markdownRenderer = new MarkdownRenderer();
