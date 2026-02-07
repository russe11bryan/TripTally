import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);
  const { signOut, user } = useAuth();
  const profile = {
    name: user?.display_name ?? 'TripTally Explorer',
    email: user?.email ?? 'guest@triptally.app',
    username: user?.username ?? 'guest',
  };
  const membership = user
    ? `Signed in as @${profile.username}`
    : 'Browsing as guest';
  const initials = (profile.name || profile.username)
    .split(' ')
    .map((part) => part.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const menuGroups = [
    {
      title: 'Account',
      items: [
        {
          label: 'My Account',
          icon: 'person-circle-outline',
          onPress: () => navigation?.navigate('MyAccount'),
        },
        {
          label: 'Privacy',
          icon: 'shield-checkmark-outline',
          onPress: () => navigation?.navigate('Privacy'),
        },
        {
          label: 'Security',
          icon: 'lock-closed-outline',
          onPress: () => navigation?.navigate('Security'),
        },
        {
          label: 'Settings',
          icon: 'settings-outline',
          onPress: () => navigation?.navigate('Settings'),
        },
      ],
    },
    {
      title: 'Support',
      items: [
        {
          label: 'Help Us',
          icon: 'megaphone-outline',
          onPress: () => navigation?.navigate('IncidentReportPage'),
        },
        {
          label: 'User Suggested Routes',
          icon: 'map-outline',
          onPress: () => navigation?.navigate('UserSuggestedRoutePage'),
        },
      ],
    },
  ];

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarInitials}>{initials || 'TT'}</Text>
        </View>
        <View>
          <Text style={styles.name}>{profile.name}</Text>
          <Text style={styles.email}>{profile.email}</Text>
          <Text style={styles.membership}>{membership}</Text>
        </View>
      </View>

      {/* <View style={styles.card}>
        <Text style={styles.sectionTitle}>Quick Access</Text>
        <View style={styles.quickRow}>
          {quickActions.map((item) => (
            <TouchableOpacity
              key={item.key}
              onPress={item.onPress}
              style={styles.quickCard}
              activeOpacity={0.7}
            >
              <View style={styles.quickIcon}>
                <Ionicons name={item.icon} size={20} color={theme.colors.text} />
              </View>
              <Text style={styles.quickLabel}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View> */}

      {menuGroups.map((group) => (
        <View key={group.title} style={styles.card}>
          <Text style={styles.sectionTitle}>{group.title}</Text>
          {group.items.map((item) => (
            <TouchableOpacity
              key={item.label}
              onPress={item.onPress}
              style={styles.menuRow}
              activeOpacity={0.7}
            >
              <View style={styles.menuLeft}>
                <View style={styles.menuIcon}>
                  <Ionicons name={item.icon} size={18} color={theme.colors.accent} />
                </View>
                <Text style={styles.menuLabel}>{item.label}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={theme.colors.muted} />
            </TouchableOpacity>
          ))}
        </View>
      ))}

      <TouchableOpacity
        onPress={signOut}
        style={styles.logoutButton}
        activeOpacity={0.75}
      >
        <Ionicons name="log-out-outline" size={20} color="#fff" />
        <Text style={styles.logoutText}>Log out</Text>
      </TouchableOpacity>
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: colors.background,
      paddingTop: 60,
      paddingHorizontal: 20,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 16,
      marginBottom: 24,
    },
    avatar: {
      width: 64,
      height: 64,
      borderRadius: 32,
      backgroundColor: colors.pill,
      alignItems: 'center',
      justifyContent: 'center',
    },
    avatarInitials: {
      color: colors.text,
      fontSize: 22,
      fontWeight: '700',
    },
    name: {
      color: colors.text,
      fontSize: 20,
      fontWeight: '800',
    },
    email: {
      color: colors.muted,
      marginTop: 4,
    },
    membership: {
      color: colors.muted,
      marginTop: 2,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 18,
      padding: 18,
      marginBottom: 16,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    sectionTitle: {
      fontWeight: '700',
      fontSize: 16,
      marginBottom: 12,
      color: colors.text,
    },
    menuRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 14,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: colors.border,
    },
    menuLeft: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
    },
    menuIcon: {
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: colors.pillAlt,
      alignItems: 'center',
      justifyContent: 'center',
    },
    menuLabel: {
      fontSize: 15,
      color: colors.text,
      fontWeight: '600',
    },
    logoutButton: {
      marginTop: 'auto',
      marginBottom: 28,
      backgroundColor: colors.danger,
      borderRadius: 16,
      paddingVertical: 16,
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      gap: 10,
    },
    logoutText: {
      color: '#fff',
      fontWeight: '700',
      fontSize: 16,
    },
  });
