import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '../context/ThemeContext';

export default function Card({ children, style }) {
  const { theme } = useTheme();
  const baseStyle = useMemo(
    () =>
      StyleSheet.create({
        card: {
          backgroundColor: theme.colors.card,
          borderRadius: 16,
          padding: 12,
          borderWidth: StyleSheet.hairlineWidth,
          borderColor: theme.colors.border,
          shadowColor: '#000',
          shadowOpacity: theme.mode === 'dark' ? 0.35 : 0.1,
          shadowRadius: 10,
          elevation: 3,
        },
      }),
    [theme],
  );

  return <View style={[baseStyle.card, style]}>{children}</View>;
}
