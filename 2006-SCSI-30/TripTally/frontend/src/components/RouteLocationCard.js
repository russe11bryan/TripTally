import React, { useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import Entypo from '@expo/vector-icons/Entypo';
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import { useTheme } from '../context/ThemeContext';

export default function RouteLocationCard({
  origin = 'Your Location',
  destination = 'Lee Wee Nam Library',
  onSwap,
  onOptions,
}) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  return (
    <View style={styles.overlayContainer}>
      <View style={styles.card}>
        {/* Top Row */}
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <Ionicons name="radio-button-on" size={18} color={theme.colors.accent} style={{ marginRight: 6 }} />
            <Text style={[styles.text, { color: theme.colors.accent }]}>{origin}</Text>
          </View>
          <TouchableOpacity onPress={onOptions}>
            <Entypo name="dots-three-horizontal" size={16} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        {/* Divider line */}
        <View style={styles.line} />

        {/* Bottom Row */}
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <Ionicons name="location-sharp" size={18} color={theme.colors.danger} style={{ marginRight: 6 }} />
            <Text style={[styles.text, { color: theme.colors.text }]}>{destination}</Text>
          </View>
          <TouchableOpacity onPress={onSwap}>
            <MaterialCommunityIcons name="swap-vertical" size={18} color={theme.colors.text} />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    overlayContainer: {
      position: 'absolute',
      top: 65,
      left: 0,
      right: 0,
      alignItems: 'center',
      zIndex: 999,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 12,
      paddingVertical: 10,
      paddingHorizontal: 14,
      width: '90%',
      alignSelf: 'center',
      shadowColor: '#000',
      shadowOpacity: 0.15,
      shadowRadius: 4,
      shadowOffset: { width: 0, height: 2 },
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    rowLeft: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    text: {
      fontSize: 14,
      fontWeight: '600',
    },
    line: {
      height: 1,
      backgroundColor: colors.border,
      marginVertical: 8,
      marginLeft: 22,
    },
  });
