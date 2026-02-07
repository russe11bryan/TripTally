// src/components/DrivingCard.js
import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Card from './Card';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

export default function DrivingCard({ mode, time, distance, cost, notes }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);
  const icons = {
    Driving: 'car',
    'Public Transport': 'bus',
    Walking: 'walk',
    Cycling: 'bicycle',
  };
  const iconName = icons[mode] ?? icons.Driving;

  return (
    <Card style={styles.container}>
      <View style={styles.header}>
        <Ionicons name={iconName} size={22} color={theme.colors.accent} />
        <Text style={styles.mode}>{mode ?? 'Mode'}</Text>
      </View>
      <Text style={styles.text}>Time: {time}</Text>
      <Text style={styles.text}>Distance: {distance}</Text>
      <Text style={styles.text}>Cost: {cost}</Text>
      {notes && <Text style={styles.text}>Notes: {notes}</Text>}
    </Card>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    container: { marginBottom: 10 },
    header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
    mode: { fontWeight: '700', fontSize: 16, color: colors.text },
    text: { fontSize: 14, color: colors.muted },
  });
