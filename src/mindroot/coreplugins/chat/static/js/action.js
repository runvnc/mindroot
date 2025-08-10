import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from './lit-html/directives/unsafe-html.js';
import {BaseEl} from './base.js';
import {escapeJsonForHtml, unescapeHtmlForJson} from './property-escape.js'
import { Marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';
import { markdownRenderer } from './markdown-renderer.js';

import {markedHighlight} from 'https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm'

function tryParse(markdown) {
    //return renderMarkdown(markdown)
      return markdownRenderer.parse(markdown);
}


console.log('markedHighlight', markedHighlight)

const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang, info) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    }
  })
)

 const format_ = (x) => {
      // if it is a string then split, otherwise return the object
      if (typeof(x) == 'string') {
        return x.split('\n')[0].slice(0, 160)
      } else {
        // if it is an object then stringify it
        if (typeof (x) == 'object' || x+"" == "[object Object]") {
          return "<pre><code>"+JSON.stringify(x,undefined, 4)+ "</code></pre>"
        } else {
          return x
        }
      }
    }


class ActionComponent extends BaseEl {
  static properties = {
    funcName: { type: String },
    params: { type: String },
    result: { type: String },
    isExpanded: { type: Boolean },
    isRunning: { type: Boolean }
  }

  static styles = [
    css`
:host {
  display: block;
  width: 100%;
}

.action-container {
  width: 100%;
  border: 1px solid #333;
  border-radius: 8px;
  margin: 4px 0;
  background-color: transparent;
}

.action-container.running {
  border-color: #4a5eff;
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0%, 100% {
    border-color: #4a5eff;
    box-shadow: 0 0 5px rgba(74, 94, 255, 0.3);
  }
  50% {
    border-color: #6a7eff;
    box-shadow: 0 0 10px rgba(74, 94, 255, 0.5);
  }
}

.action-summary {
  padding: 8px 12px;
  cursor: pointer;
  background: rgba(200, 200, 255, 0.1);
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box;
  display: block;
  color: #f0f0f0;
  user-select: none;
}

.action-summary:hover {
  background: #444;
}

.action-content {
  padding: 8px 12px;
  border-top: 1px solid #333;
  color: #f0f0f0;
  display: none;
}

.action-content.expanded {
  display: block;
}

.param-preview {
  color: #ddd;
  font-style: italic;
  margin-left: 8px;
}

.fn_name {
  color: #f0f0f0;
  font-weight: normal;
}

@keyframes flash {
  0% { opacity: 0; }
  50% { opacity: 0.5; }
  100% { opacity: 0; }
}
    `
  ];

  constructor() {
    super();
    this.funcName = '';
    this.result = '';
    this.isExpanded = true;
    this.isRunning = false;
  }

  connectedCallback() {
    super.connectedCallback();
    this.checkRunningState();
  }

  checkRunningState() {
    const chatMessages = document.querySelectorAll('chat-message');
    const lastMessage = chatMessages[chatMessages.length - 1];
    if (lastMessage && lastMessage.getAttribute('spinning') === 'yes') {
      this.isRunning = true;
      setTimeout(() => {
        this.isRunning = false;
        this.requestUpdate();
      }, 1000);
    }
  }

  _toggleExpanded() {
    this.isExpanded = !this.isExpanded;
  }
 
  _paramsHTML(params) {
    let paramshtml = '';
    if (Array.isArray(params)) {
      for (let item of params) {
        paramshtml += `<span class="param_value">(${format_(item)}), </span> `;
      }
    } else if (typeof(params) == 'object') {
      console.log('in action.js params is:',params)
      for (var key in params) {
        paramshtml += `<span class="param_name">${key}:</span> `;
        paramshtml += `<span class="param_value">${format_(params[key])}</span>  `;
      }
    } else {
      paramshtml += `<span class="param_value">[${format_(params)}]</span> `;
    }
    return paramshtml;
  } 

  _getFirstParamPreview(params) {
    if (!params) return '';
    
    let firstValue = '';
    if (Array.isArray(params) && params.length > 0) {
      firstValue = params[0];
    } else if (typeof(params) == 'object') {
      const keys = Object.keys(params);
      if (keys.length > 0) {
        firstValue = params[keys[0]];
      }
    } else {
      firstValue = params;
    }

    if (typeof(firstValue) === 'string') {
      return firstValue.length > 100 ? firstValue.substring(0, 100) + '...' : firstValue;
    } else if (typeof(firstValue) === 'object') {
      const str = JSON.stringify(firstValue);
      return str.length > 100 ? str.substring(0, 100) + '...' : str;
    } else {
      const str = String(firstValue);
      return str.length > 100 ? str.substring(0, 100) + '...' : str;
    }
  }

  _render() {
    let {funcName, params, result} = this;
    params = unescapeHtmlForJson(params)
    try {
      params = JSON.parse(params)
    } catch (e) {
       console.log('error parsing params', e)
    }

    let paramshtml = '';
    console.log('type of params is', typeof(params))
    console.log({funcName, params, result})
    if (params.val) {
      params = params.val
    }

    const paramPreview = this._getFirstParamPreview(params);
    paramshtml = this._paramsHTML(params)

    console.log('paramshtml', paramshtml)
    let res = '';
    if (result != '()' && result != '' && result != undefined) {
      let lines = result.split("\n");
      if (false && lines.length == 1) {
        res = html`<div class="one_line_result">${result}</div>`;
      } else {
        res = html`
        <details class="block fn_result">
          <summary>${lines[0]} ...</summary>
          <div>${result}</div>
        </details>`;
      }
    }
    if (funcName === 'overwrite' || funcName === 'write' || funcName == 'think') {
      let {fname, text} = params;
      if (params.extensive_chain_of_thoughts) {
        text = params.extensive_chain_of_thoughts
      }

      console.log("Displaying file")
      if (fname?.endsWith('.md') || funcName == 'think') {
        console.log("Displaying markdown")
        if (true || Date.now() - window.lastParsed > 300) {
           res = html`<div class="markdown-content">${unsafeHTML(tryParse(text, {breaks: true}))}</div>`;
        }
      } else {
        console.log("Displaying code")
        const hih = hljs.highlightAuto(text).value;
        console.log(hih)
        res = html`<pre><code>${unsafeHTML(hih)}</code></pre>`;
      }
    } else {
      if (typeof(params) === "string") {
          try {
            if (true || Date.now() - window.lastParsed > 300) {
              res = html`<div class="markdown-content">${unsafeHTML(tryParse(params))}</div>`;
            }
          } catch (e) {
            res = html`<pre><code>${params}</code></pre>`;
          }
      } else {
        const todel = []
        for (var key in params) {
          if (typeof(params[key]) === 'string' && params[key].split('\n').length > 2) {
            console.log('rendering markdown', params[key])
            try { 
              if (true || Date.now() - window.lastParsed > 300) {
                res = html`<div class="markdown-content">${unsafeHTML(tryParse(params[key]+" "))}</div>`;
              }
            } catch (e) {
              res = html`<pre><code>${params[key]}</code></pre>`;
            }
            todel.push(key)
            break
          }
        }
        for (let key of todel) {
          delete params[key]
        }
      }
      paramshtml = this._paramsHTML(params)
    }

    return html`
    <div class="action-container ${this.isRunning ? 'running' : ''}">
      <div class="action-summary" @click="${this._toggleExpanded}">
        <span class="fn_name">${funcName}</span>
        ${paramPreview ? html`<span class="param-preview">${paramPreview}</span>` : ''}
      </div>
      <div class="action-content ${this.isExpanded ? 'expanded' : ''}">
        <div class="action">
          <span class="fn_name"> ${unsafeHTML(paramshtml)}</span>
          ${res}
        </div>
      </div>
    </div>
    `;
  }
}

customElements.define('action-component', ActionComponent);
