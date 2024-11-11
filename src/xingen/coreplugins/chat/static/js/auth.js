// This file will handle token storage, retrieval, and HTTP interceptor setup

// Store the access token in the browser's local storage and cookie
export function storeAccessToken(token) {
  localStorage.setItem('accessToken', token);
  document.cookie = `access_token=${token}; path=/; max-age=604800`; // Expires in 1 week
}

// Retrieve the access token from the browser's local storage or cookie
export function getAccessToken() {
  const tokenFromStorage = localStorage.getItem('accessToken');
  if (tokenFromStorage) {
    return tokenFromStorage;
  }

  const tokenFromCookie = getCookieValue('access_token');
  return tokenFromCookie;
}

// Helper function to get the value of a cookie by name
function getCookieValue(name) {
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith(`${name}=`)) {
      return cookie.substring(name.length + 1);
    }
  }
  return null;
}
