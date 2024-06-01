export function escapeJsonForHtml(json) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(json));
  return div.innerHTML;
}

export function unescapeHtmlForJson(escapedHtml) {
  const div = document.createElement('div');
  div.innerHTML = escapedHtml;
  return div.textContent || div.innerText;
}


