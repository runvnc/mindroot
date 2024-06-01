import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';
import {BaseEl} from './base.js';
import {escapeJsonForHtml, unescapeHtmlForJson} from './property-escape.js'
import { marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';

class ActionComponent extends BaseEl {
  static properties = {
    funcName: { type: String },
    params: { type: String },
    result: { type: String }
  }

  static styles = [
    css`
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
    if (Array.isArray(params)) {
      for (let item of params) {
        paramshtml += `<span class="param_value">(${item}), </span> `;
      }
    } else if (typeof(params) == 'object') {
      for (var key in params) {
        paramshtml += `<span class="param_name">${key}:</span> `;
        paramshtml += `<span class="param_value">${params[key]}</span>  `;
      }
    } else {
      paramshtml += `<span class="param_value">[${params}]</span> `;
    }
    if (paramshtml.length > 50) {
      paramshtml = paramshtml.slice(0, 50) + '...'
    }
    let res = '';
    if (result != '()' && result != '' && result != undefined) {
      let lines = result.split("\n");
      if (lines.length == 1) {
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
      const [filename, content] = params;
      console.log("Displaying file")
      if (filename.endsWith('.md')) {
        console.log("Displaying markdown")
        console.log(marked(content))
        res = html`<div class="markdown-content">${unsafeHTML(marked(content, {breaks: true}))}</div>`;
      } else {
        console.log("Displaying code")
        res = html`<pre><code class="hljs">${unsafeHTML(hljs.highlightAuto(content).value)}</code></pre>`;
      }
    }

    return html` 
    <div></div>
    <div style="position: relative; max-width: 800px;">
      <div class="av"></div>
      <div class="action" >
        ⚡  <span class="fn_name">${funcName}</span> ${unsafeHTML(paramshtml)}
        ${res}
      </div>
    </div>
    `;
  }
}

customElements.define('action-component', ActionComponent);
