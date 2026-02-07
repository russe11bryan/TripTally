
import React, { useState } from 'react';
import { ActivityIndicator, View, Text, TextInput, TouchableOpacity } from 'react-native';
import useThemedStyles from '../hooks/useThemedStyles';
import { useAuth } from '../context/AuthContext';

export default function SignIn({ navigation }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    container:{ flex:1, padding:24, paddingTop:80, backgroundColor:colors.background },
    heading:{ fontSize:28, fontWeight:'800', marginBottom:20, color: colors.text },
    appLabel:{ fontSize:14, color: colors.muted },
    input:{ backgroundColor:colors.card, borderRadius:10, padding:14, borderWidth:1, borderColor:colors.border, color: colors.text },
    login:{ marginTop:18, backgroundColor:colors.accent, padding:14, borderRadius:12, alignItems:'center' },
    loginText:{ color:'white', fontWeight:'700' },
    googleButton:{ marginTop:12, backgroundColor:'white', padding:14, borderRadius:12, alignItems:'center', borderWidth:1, borderColor:colors.border, flexDirection:'row', justifyContent:'center', gap:10 },
    googleButtonText:{ color:'#000', fontWeight:'600' },
    divider:{ flexDirection:'row', alignItems:'center', marginVertical:20 },
    dividerLine:{ flex:1, height:1, backgroundColor:colors.border },
    dividerText:{ paddingHorizontal:12, color:colors.muted, fontSize:12 },
    error:{ color: colors.danger, marginTop:12, fontWeight:'600' },
    footer:{ marginTop:14, color: colors.text },
    footerLink:{ color: colors.accent, fontWeight:'600' },
  }));
  const { signIn, signInWithGoogle, authError, clearError } = useAuth();

  const handleSubmit = async () => {
    if (!identifier.trim() || !password) {
      setLocalError('Please provide both username/email and password.');
      return;
    }
    setSubmitting(true);
    setLocalError('');
    clearError();
    try {
      await signIn(identifier.trim(), password);
    } catch (error) {
      setLocalError(error.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleIdentifierChange = (value) => {
    setIdentifier(value);
    if (localError) setLocalError('');
    if (authError) clearError();
  };

  const handlePasswordChange = (value) => {
    setPassword(value);
    if (localError) setLocalError('');
    if (authError) clearError();
  };

  const handleGoogleSignIn = async () => {
    setSubmitting(true);
    setLocalError('');
    clearError();
    try {
      await signInWithGoogle();
    } catch (error) {
      if (error.code !== 'SIGN_IN_CANCELLED') {
        setLocalError(error.message || 'Google Sign-In failed');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Sign In{"\n"}<Text style={styles.appLabel}>TRIPTALLY</Text></Text>
      <View style={{gap:12}}>
        <TextInput style={styles.input} placeholder="Email or username" placeholderTextColor={theme.colors.muted} value={identifier} autoCapitalize="none" onChangeText={handleIdentifierChange} />
        <TextInput style={styles.input} placeholder="password" placeholderTextColor={theme.colors.muted} secureTextEntry value={password} onChangeText={handlePasswordChange} />
      </View>
      {(authError || localError) && <Text style={styles.error}>{(authError?.message) || localError}</Text>}
      <TouchableOpacity style={styles.login} onPress={handleSubmit} disabled={submitting}>
        {submitting ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.loginText}>Log in</Text>
        )}
      </TouchableOpacity>
      
      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>OR</Text>
        <View style={styles.dividerLine} />
      </View>
      
      <TouchableOpacity style={styles.googleButton} onPress={handleGoogleSignIn} disabled={submitting}>
        <Text style={styles.googleButtonText}>🔵 Continue with Google</Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        onPress={() => {
          if (authError) clearError();
          if (localError) setLocalError('');
          navigation.navigate('CreateAccount');
        }}
        style={{marginTop:14}}
      >
        <Text style={styles.footer}>Don't have account? <Text style={styles.footerLink}>Sign up</Text></Text>
      </TouchableOpacity>
    </View>
  );
}
