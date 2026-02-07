// components/TransportDetailsCard.js
import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../context/ThemeContext';

export default function TransportDetailsCard({ details }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  return (
    <View style={styles.card}>
      {Object.entries(details).map(([label, value], index) => (
        <View
          key={`${label}-${index}`}
          style={[
            styles.row,
            index !== Object.entries(details).length - 1 && styles.rowBorder,
          ]}
        >
          <Text style={styles.label}>{label}:</Text>
          <Text style={styles.value}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    card: {
      backgroundColor: colors.card,
      borderRadius: 10,
      paddingHorizontal: 16,
      paddingVertical: 10,
      borderWidth: 0.6,
      borderColor: colors.border,
    },
    row: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 6,
    },
    rowBorder: {
      borderBottomWidth: 0.3,
      borderColor: colors.border,
    },
    label: {
      fontSize: 14,
      fontWeight: '500',
      color: colors.muted,
    },
    value: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
  });
