// src/components/NearestCarparkButton.js
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

export default function NearestCarparkButton({ 
  origin, 
  destination, 
  destText, 
  onPress, 
  style,
  buttonStyle,
  textStyle 
}) {
  if (!destination) return null;

  return (
    <View style={[{ marginBottom: 12 }, style]}>
      <TouchableOpacity
        style={[styles.carparkButton, buttonStyle]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Ionicons name="car-sport" size={16} color="#FFFFFF" />
        <Text style={[styles.carparkButtonText, textStyle]}>Find Nearest Carpark</Text>
        <Ionicons name="chevron-forward" size={14} color="#FFFFFF" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  carparkButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: "#4C8BF5",
    gap: 6,
  },
  carparkButtonText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
