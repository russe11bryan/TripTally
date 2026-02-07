import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function MyAccountPage({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);
  const { user } = useAuth();
  const displayName = user?.display_name ?? 'TripTally Explorer';
  const username = user?.username ?? 'guest';
  const email = user?.email ?? 'guest@triptally.app';

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} noLeftMargin />
      <Text style={styles.title}>My Account</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Name</Text>
        <Text style={styles.value}>{displayName}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Username</Text>
        <Text style={styles.value}>@{username}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Email</Text>
        <Text style={styles.value}>{email}</Text>
      </View>

      <Text style={styles.helper}>
        Reach out to support@triptally.app if you need to update more details.
      </Text>
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
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
    label: {
      color: colors.muted,
      fontSize: 12,
      fontWeight: '600',
      textTransform: 'uppercase',
      marginBottom: 4,
    },
    value: {
      color: colors.text,
      fontSize: 16,
      fontWeight: '700',
    },
    helper: {
      marginTop: 16,
      color: colors.muted,
      fontSize: 13,
    },
  });
