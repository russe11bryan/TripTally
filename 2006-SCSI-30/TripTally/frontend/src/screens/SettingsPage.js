import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Switch } from 'react-native';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';

export default function SettingsPage({ navigation }) {
  const { theme, toggleTheme } = useTheme();
  const [notifications, setNotifications] = useState(true);
  const [routeSharing, setRouteSharing] = useState(false);
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} noLeftMargin />
      <Text style={styles.title}>Settings</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Personalisation</Text>
        {/* <View style={styles.row}>
          <View style={styles.rowText}>
            <Text style={styles.rowLabel}>Trip notifications</Text>
            <Text style={styles.rowDescription}>Get reminders for upcoming journeys.</Text>
          </View>
          <Switch value={notifications} onValueChange={setNotifications} />
        </View> */}
        <View style={styles.row}>
          <View style={styles.rowText}>
            <Text style={styles.rowLabel}>Dark mode</Text>
            <Text style={styles.rowDescription}>Reduce glare for night-time travel.</Text>
          </View>
          <Switch value={theme.mode === 'dark'} onValueChange={toggleTheme} />
        </View>
      </View>

      {/* <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sharing</Text>
        <View style={styles.row}>
          <View style={styles.rowText}>
            <Text style={styles.rowLabel}>Share new routes automatically</Text>
            <Text style={styles.rowDescription}>
              Publish your custom routes to the community once approved.
            </Text>
          </View>
          <Switch value={routeSharing} onValueChange={setRouteSharing} />
        </View>
      </View> */}

      <Text style={styles.footer}>
        TripTally saves your preferences to the device and syncs to your account when you go online.
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
    section: {
      backgroundColor: colors.card,
      borderRadius: 18,
      padding: 16,
      marginBottom: 16,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    sectionTitle: {
      fontWeight: '700',
      color: colors.text,
      fontSize: 16,
      marginBottom: 12,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 10,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: colors.border,
    },
    rowText: {
      flex: 1,
      marginRight: 16,
    },
    rowLabel: {
      fontWeight: '600',
      color: colors.text,
      marginBottom: 4,
    },
    rowDescription: {
      color: colors.muted,
      fontSize: 13,
    },
    footer: {
      marginTop: 12,
      color: colors.muted,
      fontSize: 13,
    },
  });
