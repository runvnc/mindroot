// load-styles.js
export async function loadStyles(url) {
  const response = await fetch(url);
  const cssText = await response.text();
  const styleSheet = new CSSStyleSheet();
  styleSheet.replaceSync(cssText);
  return styleSheet;
}

