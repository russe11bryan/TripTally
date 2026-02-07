
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import useThemedStyles from '../hooks/useThemedStyles';

export default function WelcomePage({ navigation }) {
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    container: { flex:1, padding:24, paddingTop: 150, backgroundColor:colors.background },
    hero: {alignItems:'center', marginBottom: 40},
    title: { fontSize: 28, fontWeight: '800', textAlign:'center', marginTop: 10, color: colors.text },
    subtitle: { color:colors.muted, textAlign:'center', marginTop:6 },
    ctaOutline: { borderColor:colors.accent, borderWidth:1.5, padding:14, borderRadius:12, alignItems:'center', justifyContent:'center', marginBottom: 8, backgroundColor: colors.card },
    ctaText: { fontWeight:'700', color: colors.text },
    footerText: { color: colors.text },
    footerLink: { color: colors.accent, fontWeight:'600' },
  }));

  return (
    <View style={styles.container}>
      <View style={styles.hero}>
        <Ionicons name="navigate-outline" size={72} color={theme.colors.accent} />
        <Text style={styles.title}>Welcome to{"\n"}TripTally</Text>
        <Text style={styles.subtitle}>Making travelling simpler…</Text>
      </View>
      <TouchableOpacity style={styles.ctaOutline} onPress={() => navigation.navigate('SignIn')}>
        <Text style={styles.ctaText}>
          <Ionicons name="logo-google" size={20} color={theme.colors.text} /> Continue with Google
        </Text>
      </TouchableOpacity>
      {/* <TouchableOpacity style={styles.ctaOutline} onPress={() => navigation.navigate('SignIn')}>
        <Text style={styles.ctaText}>
          <Ionicons name="logo-apple" size={20} color={theme.colors.text} /> Continue with Apple
        </Text>
      </TouchableOpacity> */}
      <TouchableOpacity style={styles.ctaOutline} onPress={() => navigation.navigate('SignIn')}>
        <Text style={styles.ctaText}>Continue with Email</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.navigate('SignIn')} style={{marginTop: 12}}>
        <Text style={styles.footerText}>Already have an account? <Text style={styles.footerLink}>Login</Text></Text>
      </TouchableOpacity>
    </View>
  );
}
