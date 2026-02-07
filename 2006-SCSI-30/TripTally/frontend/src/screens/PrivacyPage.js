import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';

export default function PrivacyPage({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  const policies = [
    {
      title: 'Data Collection',
      description:
        'We only collect travel preferences and saved locations to personalise your TripTally experience.',
    },
    {
      title: 'Location Usage',
      description:
        'Live location is used temporarily for routing. It is never stored on our servers without your consent.',
    },
    {
      title: 'Sharing Preferences',
      description:
        'You control who sees your custom routes and shared reports. Adjust visibility in Settings at any time.',
    },
  ];

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} noLeftMargin />
      <Text style={styles.title}>Privacy</Text>

      {policies.map((item) => (
        <View key={item.title} style={styles.card}>
          <Text style={styles.cardTitle}>{item.title}</Text>
          <Text style={styles.cardDescription}>{item.description}</Text>
        </View>
      ))}

      <Text style={styles.footer}>
        Need more details? Read the full policy at triptally.app/privacy or contact privacy@triptally.app.
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
      padding: 18,
      marginBottom: 14,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    cardTitle: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 6,
    },
    cardDescription: {
      color: colors.muted,
      lineHeight: 20,
    },
    footer: {
      marginTop: 16,
      color: colors.muted,
      fontSize: 13,
    },
  });
