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
    console.log('type of params is', typeof(params))
    console.log({funcName, params, result})
    if (typeof(params) == 'array') {
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

    let res = '';
    if (result != '()') {
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

    return html` 
    <div></div>
    <div style="position: relative; max-width: 800px;">
      <div class="av"></div>
      <div class="action" >
        ⚡  <span class="fn_name">${funcName}</span> ${paramshtml}
        result: ${res}
      </div>
    </div>
    `;
  }
}

customElements.define('action-component', ActionComponent);
