// src/components/BottomNav.js
import React, { useMemo } from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

export default function BottomNav({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);
  const items = [
    { name: 'Explore', icon: 'map' },
    { name: 'Saved', icon: 'heart' },
    { name: 'Suggest', icon: 'chatbox' },
    { name: 'Profile', icon: 'person' },
  ];

  return (
    <View style={styles.container}>
      {items.map((item) => (
        <TouchableOpacity
          key={item.name}
          onPress={() => navigation.navigate(item.name)}
          style={styles.tab}
        >
          <Ionicons name={item.icon} size={24} color={theme.colors.text} />
          <Text style={styles.text}>{item.name}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    container: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      backgroundColor: colors.card,
      paddingVertical: 10,
      borderTopWidth: StyleSheet.hairlineWidth,
      borderTopColor: colors.border,
    },
    tab: { alignItems: 'center' },
    text: { color: colors.text, fontSize: 12 },
  });
