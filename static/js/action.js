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
      if (false && lines.length == 1) {
        res = html`<div class="fn_result">${result}</div>`;
      } else {
        res = html`
        <details class="block fn_result">
          <summary>${lines[0]} ...</summary>
          <pre><code>${result}</code></pre>
        </details>`;
      }
    }

    return html` 
    <div></div>
    <div>
      <div class="av"></div>
      <div class="action" >
        ⚡  <span class="fn_name">${funcName}</span> ${paramshtml}
        ${res}
      </div>
    </div>
    `;
  }
}

customElements.define('action-component', ActionComponent);
