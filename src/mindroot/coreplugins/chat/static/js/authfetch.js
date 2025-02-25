

export async function authenticatedFetch(url, options = {}) {
    const token = window.access_token;
    
    if (!token || (token && token.length < 20)) {
      console.log("No valid auth token found, token is", token)
      return fetch(url, options);
   } else {
    console.log("Auth token found :), token is", token)
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    });
  }
}

window.authenticatedFetch = authenticatedFetch;

