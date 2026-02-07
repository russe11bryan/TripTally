import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { BASE_URL } from '../config/keys';

// Automatically detect the backend URL based on the Expo manifest
// This will use the same IP as your Expo dev server, so it updates automatically
function getDefaultApiUrl() {
  // For iOS simulator, use localhost
  if (Platform.OS === 'ios' && !Constants.isDevice) {
    return BASE_URL;
  }
  
  // For Android emulator, use the special Android emulator IP
  if (Platform.OS === 'android' && !Constants.isDevice) {
    return 'http://10.0.2.2:8000';
  }
  
  // For physical devices, automatically detect the host IP from Expo
  // This is the same IP that Expo Metro bundler is using
  const expoHostUrl = Constants.expoConfig?.hostUri;
  if (expoHostUrl) {
    // Extract just the IP/hostname part (remove port)
    const host = expoHostUrl.split(':')[0];
    return `http://${host}:8000`;
  }
  
  // Fallback to a hardcoded IP (you can update this as needed)
  return BASE_URL;
}

// Default API URLs for different environments:
// - iOS Simulator: http://localhost:8000
// - Android Emulator: http://10.0.2.2:8000
// - Physical Device: Auto-detected from Expo dev server IP
const DEFAULT_API_URL = getDefaultApiUrl();

// Log the detected API URL for debugging
console.log('🌐 API Base URL:', DEFAULT_API_URL);

// Prefer explicit BASE_URL from config/keys if set (keeps all callers consistent)
// Wrap the nullish-coalescing chain in parentheses so mixing with || doesn't cause a parse error
export const API_BASE_URL =
  BASE_URL ||
  (Constants?.expoConfig?.extra?.apiUrl ?? process.env.EXPO_PUBLIC_API_URL ?? DEFAULT_API_URL);

async function request(path, { method = 'GET', body, token, timeout = 10000 } = {}) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Create an AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      try {
        const errorBody = await response.json();
        if (errorBody?.detail) {
          message = Array.isArray(errorBody.detail)
            ? errorBody.detail.map((d) => d.msg ?? d).join(', ')
            : errorBody.detail;
        }
      } catch {
        // ignore parse errors
      }
      throw new Error(message);
    }

    if (response.status === 204) {
      return null;
    }
    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    // Handle timeout and network errors with better messages
    if (error.name === 'AbortError') {
      throw new Error('Request timeout. Please check your internet connection and try again.');
    }
    if (error.message === 'Network request failed' || error.message.includes('Failed to fetch')) {
      throw new Error(`Cannot connect to server at ${API_BASE_URL}. Please ensure the backend is running.`);
    }
    throw error;
  }
}

export function apiGet(path, options) {
  return request(path, { ...options, method: 'GET' });
}

export function apiPost(path, body, options) {
  return request(path, { ...options, method: 'POST', body });
}

export function apiPut(path, body, options) {
  return request(path, { ...options, method: 'PUT', body });
}

export function apiPatch(path, body, options) {
  return request(path, { ...options, method: 'PATCH', body });
}

export function apiDelete(path, options) {
  return request(path, { ...options, method: 'DELETE' });
}
