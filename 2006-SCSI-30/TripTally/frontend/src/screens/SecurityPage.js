import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';

const tips = [
  {
    title: 'Password Strength',
    detail: 'Use a mix of at least 12 characters, numbers, and symbols for your TripTally password.',
  },
  {
    title: 'Device Verification',
    detail: 'We notify you whenever a new device signs in. Review activity regularly in Settings.',
  },
  {
    title: 'Route Sharing',
    detail: 'Only share custom routes with users you trust. You can revoke access at any time.',
  },
];

export default function SecurityPage({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} noLeftMargin />
      <Text style={styles.title}>Security</Text>

      {tips.map((tip) => (
        <View key={tip.title} style={styles.card}>
          <Text style={styles.cardTitle}>{tip.title}</Text>
          <Text style={styles.cardDetail}>{tip.detail}</Text>
        </View>
      ))}

      <View style={styles.alert}>
        <Text style={styles.alertTitle}>Suspicious activity?</Text>
        <Text style={styles.alertDesc}>
          Reset your password immediately and email security@triptally.app for help.
        </Text>
      </View>
    </View>
  );
}

const createStyles = (theme) => {
  const { colors } = theme;
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: colors.background,
      paddingTop: 48,
      paddingHorizontal: 16,
    },
    title: {
      fontSize: 24,
      fontWeight: '800',
      marginBottom: 24,
      color: colors.text,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 16,
      padding: 16,
      marginBottom: 12,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    cardTitle: {
      fontWeight: '700',
      color: colors.text,
      marginBottom: 6,
      fontSize: 16,
    },
    cardDetail: {
      color: colors.muted,
      lineHeight: 20,
    },
    alert: {
      marginTop: 20,
      padding: 16,
      borderRadius: 16,
      backgroundColor: theme.mode === 'dark' ? '#2f1e21' : '#fff5f5',
      borderWidth: 1,
      borderColor: theme.mode === 'dark' ? '#b91c1c' : '#fecaca',
    },
    alertTitle: {
      fontWeight: '700',
      color: '#b91c1c',
      marginBottom: 4,
    },
    alertDesc: {
      color: '#b91c1c',
      lineHeight: 20,
    },
  });
};
