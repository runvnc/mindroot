import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from './lit-html/directives/unsafe-html.js';
import {BaseEl} from './base.js';
import {escapeJsonForHtml, unescapeHtmlForJson} from './property-escape.js'
import { Marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';

import {markedHighlight} from 'https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm'


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


class ActionComponent extends BaseEl {
  static properties = {
    funcName: { type: String },
    params: { type: String },
    result: { type: String }
  }

  static styles = [
    css`
    * {
      display: contents;
    }

@keyframes flash {
  0% { opacity: 0; }
  50% { opacity: 0.5; }
  100% { opacity: 0; }
}

.animated-element::before {
  content: '';
  display: inline-block;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(200,200,200,0.5);
  animation: flash 0.2s;
  pointer-events: none;
}

.animated-element {
  /* position: relative; */
}
    `
  ];

  constructor() {
    super();
    this.funcName = '';
    //this.params = {};
    this.result = '';
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
    let dontTruncate = false;
    let format_;
    if (funcName != 'write') {
      format_ = (str) => {
        return str
      }
    } else {
      format_ = (str) => {
        return str.split('\n')[0].slice(0, 160)
      }
    }
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

    if (funcName === 'write') {
      const {fname, text} = params;
      console.log("Displaying file")
      if (fname.endsWith('.md')) {
        console.log("Displaying markdown")
        console.log(marked.parse(text))
        res = html`<div class="markdown-content">${unsafeHTML(marked.parse(text, {breaks: true}))}</div>`;
      } else {
        console.log("Displaying code")
        const hih = hljs.highlightAuto(text).value;
        console.log(hih)
        res = html`<pre><code>${unsafeHTML(hih)}</code></pre>`;
      }
    }

    return html`
    <details class="animated-element-x" style="position: relative; max-width: 800px;" open >
      <!-- we need to make sure it's open by default so we will set property to true -->
      <summary class="fn_name" style="display:contents"  >⚡ ${funcName}</summary>
      <div class="av-x"></div>
      <div class="action" style="display: contents;" >
        ⚡  <span class="fn_name"> ${unsafeHTML(paramshtml)}
        <div style="height: 15px; display: block">&nbsp;</div>
        ${res}
      </div> 
    </details>
    `;
  }
}

customElements.define('action-component', ActionComponent);
