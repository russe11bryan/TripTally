// src/components/RouteCard.js
import React, { useMemo } from 'react';
import { Text, TouchableOpacity, StyleSheet } from 'react-native';
import Card from './Card';
import { useTheme } from '../context/ThemeContext';

export default function RouteCard({ name, desc, onPress }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  return (
    <TouchableOpacity onPress={onPress}>
      <Card style={styles.card}>
        <Text style={styles.name}>{name}</Text>
        {desc && <Text style={styles.desc}>{desc}</Text>}
      </Card>
    </TouchableOpacity>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    card: { marginBottom: 10 },
    name: { fontWeight: '700', fontSize: 16, color: colors.text },
    desc: { color: colors.muted, marginTop: 4 },
  });
