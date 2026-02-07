import React, { createContext, useContext, useMemo, useState } from 'react';
import { DarkTheme, DefaultTheme } from '@react-navigation/native';

const lightTheme = {
  mode: 'light',
  colors: {
    background: '#f2f5f9',
    card: '#ffffff',
    text: '#0f2434',
    muted: '#6b7280',
    accent: '#2f7cf6',
    border: '#e5e7eb',
    pill: '#e0e7f8',
    pillAlt: '#f4f6fb',
    danger: '#ff6b6b',
  },
  navigation: {
    ...DefaultTheme,
    colors: {
      ...DefaultTheme.colors,
      background: '#f2f5f9',
      card: '#ffffff',
      text: '#0f2434',
      border: '#e5e7eb',
      primary: '#2f7cf6',
    },
  },
};

const darkTheme = {
  mode: 'dark',
  colors: {
    background: '#07121f',
    card: '#132237',
    text: '#f8fafc',
    muted: '#94a3b8',
    accent: '#60a5fa',
    border: '#1f3b53',
    pill: '#12233b',
    pillAlt: '#0d192a',
    danger: '#f87171',
  },
  navigation: {
    ...DarkTheme,
    colors: {
      ...DarkTheme.colors,
      background: '#07121f',
      card: '#132237',
      text: '#f8fafc',
      border: '#1f3b53',
      primary: '#60a5fa',
    },
  },
};

const ThemeContext = createContext({
  theme: lightTheme,
  toggleTheme: () => {},
  setMode: () => {},
});

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(lightTheme);

  const value = useMemo(
    () => ({
      theme,
      toggleTheme: () =>
        setTheme((prev) => (prev.mode === 'light' ? darkTheme : lightTheme)),
      setMode: (mode) => setTheme(mode === 'dark' ? darkTheme : lightTheme),
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
