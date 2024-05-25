import sharedStyles from '../css/main.css';

const sharedStyleSheet = new CSSStyleSheet();
sharedStyleSheet.replaceSync(sharedStyles);

export { sharedStyleSheet };

