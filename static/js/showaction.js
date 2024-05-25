function showFunctionCall(funcName, params, result) {
  let paramshtml = ''
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
      </details>`
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
  `
  return html
}
