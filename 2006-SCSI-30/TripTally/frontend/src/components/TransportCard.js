import React, { useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';

export default function TransportCard({ 
  icon, 
  title, 
  time, 
  distance, 
  cost, 
  co2, 
  additionalInfo,
  onPress 
}) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  const renderIcon = () => {
    switch (icon) {
      case 'car':
        return <Ionicons name="car" size={36} color={theme.colors.accent} />;
      case 'train':
        return <Ionicons name="train" size={36} color={theme.colors.accent} />;
      case 'walk':
        return <Ionicons name="walk" size={36} color={theme.colors.accent} />;
      case 'bicycle':
        return <MaterialCommunityIcons name="bike" size={36} color={theme.colors.accent} />;
      default:
        return null;
    }
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.85}
      disabled={!onPress}
    >
      {renderIcon()}
      <Text style={styles.cardTitle}>{title}</Text>

      <View style={styles.detailRow}>
        <Text style={styles.label}>Time:</Text>
        <Text style={styles.value}>{time}</Text>
      </View>
      <View style={styles.detailRow}>
        <Text style={styles.label}>Distance:</Text>
        <Text style={styles.value}>{distance}</Text>
      </View>
      <View style={styles.detailRow}>
        <Text style={styles.label}>Cost:</Text>
        <Text style={styles.value}>{cost}</Text>
      </View>
      <View style={styles.detailRow}>
        <Text style={styles.label}>CO₂:</Text>
        <Text style={styles.value}>{co2}</Text>
      </View>
      {additionalInfo?.map((info, index) => (
        <View key={`${info.label}-${index}`} style={styles.detailRow}>
          <Text style={styles.label}>{info.label}:</Text>
          <Text style={styles.value}>{info.value}</Text>
        </View>
      ))}
    </TouchableOpacity>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    card: {
      width: '48%',
      backgroundColor: colors.pillAlt,
      borderRadius: 12,
      paddingVertical: 16,
      paddingHorizontal: 8,
      alignItems: 'center',
      marginBottom: 16,
      shadowColor: '#000',
      shadowOpacity: colors.mode === 'dark' ? 0.25 : 0.08,
      shadowOffset: { width: 0, height: 2 },
      shadowRadius: 4,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
      minHeight: 200,  // Add minimum height to accommodate additional info
      justifyContent: 'space-between',  // Evenly space content
    },
    cardTitle: {
      fontSize: 15,
      fontWeight: '700',
      marginTop: 8,
      marginBottom: 8,
      color: colors.text,
    },
    detailRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      width: '70%',
      marginVertical: 2,
    },
    label: { color: colors.muted, fontSize: 13 },
    value: { color: colors.text, fontWeight: '600', fontSize: 13 },
  });
