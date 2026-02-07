import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import * as AuthSession from 'expo-auth-session';
import { apiGet, apiPost } from '../services/api';

WebBrowser.maybeCompleteAuthSession();

const AuthContext = createContext(null);

const STORAGE_KEY = 'triptally.token';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Configure Google Sign-In for Expo
  // Note: Google Sign-In has limitations in Expo Go due to redirect URI handling
  // For production, you'll need a development build or standalone app
  const [request, response, promptAsync] = Google.useAuthRequest({
    expoClientId: '766584183679-lo5r8ing0dk7knmfgr84q9vvl51vrsjp.apps.googleusercontent.com',
    iosClientId: '766584183679-f996180ulcutjme5kq6gnr67d9f8mv1a.apps.googleusercontent.com',
    androidClientId: 'YOUR_ANDROID_CLIENT_ID_HERE',
    webClientId: '766584183679-lo5r8ing0dk7knmfgr84q9vvl51vrsjp.apps.googleusercontent.com',
  });

  // Debug: Log the request details
  useEffect(() => {
    console.log('=== Google Auth Request Details ===');
    console.log('Request:', request);
    if (request) {
      console.log('Redirect URI:', request.redirectUri);
      console.log('Code Challenge Method:', request.codeChallengeMethod);
    }
    console.log('===================================');
  }, [request]);

  const hydrateUser = useCallback(async (accessToken) => {
    try {
      const me = await apiGet('/auth/me', { token: accessToken });
      setToken(accessToken);
      setUser(me);
      await AsyncStorage.setItem(STORAGE_KEY, accessToken);
    } catch (error) {
      await AsyncStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      throw error;
    }
  }, []);

  // Handle Google Sign-In response
  useEffect(() => {
    console.log('Google response:', response);
    if (response?.type === 'success') {
      console.log('Google Sign-In successful!');
      console.log('Response params:', response.params);
      const { id_token, authentication } = response.params;
      const token = id_token || authentication?.idToken;
      
      if (token) {
        console.log('Got ID token, sending to backend...');
        (async () => {
          try {
            const { access_token: accessToken } = await apiPost('/auth/google', {
              id_token: token,
            }, { timeout: 30000 }); // Increase timeout to 30 seconds for Google login
            console.log('Backend responded with access token');
            await hydrateUser(accessToken);
          } catch (error) {
            console.error('Google sign-in backend error:', error);
            console.error('Error details:', JSON.stringify(error, null, 2));
            setAuthError(error);
          }
        })();
      } else {
        console.error('No ID token found in response');
      }
    } else if (response?.type === 'error') {
      console.error('Google Sign-In error:', response.error);
      setAuthError(new Error(response.error?.message || 'Google Sign-In failed'));
    } else if (response?.type === 'cancel') {
      console.log('User cancelled Google Sign-In');
    }
  }, [response, hydrateUser]);

  useEffect(() => {
    (async () => {
      try {
        const storedToken = await AsyncStorage.getItem(STORAGE_KEY);
        if (storedToken) {
          await hydrateUser(storedToken);
        }
      } catch (error) {
        console.warn('Failed to restore session', error);
      } finally {
        setLoading(false);
      }
    })();
  }, [hydrateUser]);

  const signIn = useCallback(async (identifier, password) => {
    setAuthError(null);
    try {
      const { access_token: accessToken } = await apiPost('/auth/login', {
        identifier,
        password,
      }, { timeout: 30000 }); // Increase timeout to 30 seconds for login
      await hydrateUser(accessToken);
    } catch (error) {
      setAuthError(error);
      throw error;
    }
  }, [hydrateUser]);

  const signUp = useCallback(async ({ email, username, password, displayName }) => {
    setAuthError(null);
    await apiPost('/users', {
      email,
      username,
      password,
      display_name: displayName,
    });
    await signIn(email, password);
  }, [signIn]);

  const signInWithGoogle = useCallback(async () => {
    setAuthError(null);
    try {
      console.log('Starting Google Sign-In...');
      console.log('Request ready:', !!request);
      // Try forcing useProxy to route through Expo's auth proxy
      const result = await promptAsync({ useProxy: true });
      console.log('Google Sign-In result:', JSON.stringify(result, null, 2));
      console.log('Result type:', result.type);
      return result;
    } catch (error) {
      console.error('Google Sign-In error:', error);
      setAuthError(error);
      throw error;
    }
  }, [promptAsync, request]);

  const signOut = useCallback(async () => {
    setToken(null);
    setUser(null);
    setAuthError(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const me = await apiGet('/auth/me', { token });
      setUser(me);
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  }, [token]);

  const clearError = useCallback(() => setAuthError(null), []);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      authError,
      isAuthenticated: Boolean(token && user),
      signIn,
      signUp,
      signInWithGoogle,
      signOut,
      refreshUser,
      clearError,
    }),
    [authError, clearError, loading, signIn, signInWithGoogle, signOut, signUp, token, user, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
