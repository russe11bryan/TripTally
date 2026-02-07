import { useMemo } from 'react';
import { StyleSheet as RNStyleSheet } from 'react-native';
import { useTheme } from '../context/ThemeContext';

export default function useThemedStyles(factory) {
  const { theme } = useTheme();
  const styles = useMemo(() => RNStyleSheet.create(factory(theme)), [theme]);
  return { styles, theme };
}
