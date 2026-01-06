export function removeCmdPrefix(msgText) {
  try {
    let i = 0;
    let depth = 0;
    let inString = false;
    let escaped = false;
    
    // Scan for complete JSON object at start
    for (; i < msgText.length; i++) {
      const char = msgText[i];
      
      if (!inString) {
        if (char === '{') depth++;
        if (char === '}') {
          depth--; 
          if (depth === 0) {
            // Found potential end of JSON
            const possibleJson = msgText.substring(0, i + 1);
            try {
              JSON.parse(possibleJson); // Validate it's valid JSON
              return msgText.substring(i + 1);
            } catch {
              continue; // Wasn't valid JSON, keep scanning
            }
          }
        }
      }

      if (char === '"' && !escaped) inString = !inString;
      escaped = char === '\\' && !escaped;
    }
    
    return msgText; // No valid JSON prefix found
  } catch (e) {
    console.warn('Error removing command prefix:', e);
    return msgText;
  }
}
