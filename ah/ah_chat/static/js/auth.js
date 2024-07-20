// This file will handle token storage, retrieval, and HTTP header setup

// Store the access token in the browser's local storage
export function storeAccessToken(token) {
  localStorage.setItem('accessToken', token);
}

// Retrieve the access token from the browser's local storage
export function getAccessToken() {
  return localStorage.getItem('accessToken');
}

// Create a custom HTTP header setter that adds the access token
export function setupAuthHeader(request) {
  const token = getAccessToken();
  if (token) {
    request.headers.set('Authorization', `Bearer ${token}`);
  }
  return request;
}
