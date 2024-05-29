import { LitElement, html, css } from '/static/js/lit-core.min.js';
import {BaseEl} from './base.js';

class ActionComponent extends BaseEl {
  static properties = {
    funcName: { type: String },
    params: { type: Object },
    result: { type: String }
  }

  static styles = [
    css`
      .param_name { font-weight: bold; }
      .param_value { color: blue; }
      .fn_result { margin-top: 10px; }
      .action { border: 2px solid blue; padding: 10px; margin: 10px; border-radius: 5px; background-color: gray; }
    `
  ];

  constructor() {
    super();
    this.funcName = '';
    this.params = {};
    this.result = '';
  }

  _render() {
    const {funcName, params, result} = this;
    let paramshtml = '';
    for (var key in params) {
      paramshtml += `<span class="param_name">${key}</span> `;
      paramshtml += `<span class="param_value">${params[key]}</span>  `;
    }

    let res = '';
    if (result != '()') {
      let lines = result.split("\n");
      if (lines.length == 1) {
        res = `<div class="fn_result"><pre><code class="font-mono whitespace-pre-wrap" >${result}</code></pre></div>`;
      } else {
        res = `
        <details class="block fn_result">
          <summary>${lines[0]} ...</summary>
          <pre><code class="font-mono whitespace-pre-wrap" >${result}</code></pre>
        </details>`;
      }
    }

    let html = ` 
    <div></div>
    <div>
      <div class="av"></div>
      <div class="action block border-2 border-blue-500 p-4 m-2 rounded-lg bg-gray-800" >
        ⚡  <span class="fn_name">${funcName}</span> ${paramshtml}
        ${res}
      </div>
    </div>
    `;
    return html;
  }
}

customElements.define('action-component', ActionComponent);
