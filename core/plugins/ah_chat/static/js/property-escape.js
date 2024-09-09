export function escapeJsonForHtml(json) {
  return json.replace(/"/g, '&quot;')
  //const div = document.createElement('div');
  //div.appendChild(document.createTextNode(json));
  //return div.innerHTML;
}

export function unescapeHtmlForJson(escapedHtml) {
  return escapedHtml.replace(/&quot;/g, '"')
  //const div = document.createElement('div');
  //div.innerHTML = escapedHtml;
  //return div.textContent || div.innerText;
}


