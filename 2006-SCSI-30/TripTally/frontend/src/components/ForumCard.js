// src/components/ForumCard.js
import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, Image, StyleSheet } from 'react-native';
import Card from './Card';
import { useTheme } from '../context/ThemeContext';

export default function ForumCard({ title, type, votes, image, onView, onMap }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  return (
    <Card style={{ marginBottom: 10 }}>
      {image && (
        <Image
          source={image}
          style={{ width: '100%', height: 150, borderRadius: 10, marginBottom: 8 }}
        />
      )}
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.type}>{type}</Text>
      <View style={styles.actions}>
        <TouchableOpacity onPress={onView}><Text style={styles.link}>View Details</Text></TouchableOpacity>
        <TouchableOpacity onPress={onMap}><Text style={styles.link}>Show on Map</Text></TouchableOpacity>
      </View>
      <Text style={styles.votes}>+{votes}</Text>
    </Card>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    title: { fontWeight: '700', fontSize: 16, color: colors.text },
    type: { color: colors.muted, fontSize: 13, marginBottom: 8 },
    actions: { flexDirection: 'row', justifyContent: 'space-between' },
    link: { color: colors.accent, fontWeight: '600' },
    votes: { position: 'absolute', right: 12, top: 12, fontWeight: '700', color: colors.accent },
  });
