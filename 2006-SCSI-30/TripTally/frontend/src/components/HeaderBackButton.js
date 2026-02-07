import React, { useMemo } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useTheme } from '../context/ThemeContext';

export default function HeaderBackButton({
  onPress,
  label = '< Back',
  style,
  textStyle,
  noLeftMargin = false,
}) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors, noLeftMargin), [theme, noLeftMargin]);

  return (
    <TouchableOpacity onPress={onPress} style={[styles.container, style]} activeOpacity={0.6}>
      <Text style={[styles.label, textStyle]}>{label}</Text>
    </TouchableOpacity>
  );
}

const createStyles = (colors, noLeftMargin) =>
  StyleSheet.create({
    container: {
      alignSelf: 'flex-start',
      marginTop: 8,
      marginLeft: noLeftMargin ? 0 : 16,
      marginBottom: 8,
    },
    label: {
      color: colors.accent,
      fontSize: 18,
      fontWeight: '600',
      paddingVertical: 4,
      paddingHorizontal: 8,
    },
  });
