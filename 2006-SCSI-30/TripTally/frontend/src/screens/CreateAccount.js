import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { FontAwesome } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import useThemedStyles from '../hooks/useThemedStyles';
import { useAuth } from '../context/AuthContext';

// Validation helper functions
const validatePassword = (password) => {
  const errors = [];
  
  if (password.length < 8) {
    errors.push('At least 8 characters');
  }
  
  if (!/\d/.test(password)) {
    errors.push('At least one number');
  }
  
  if (!/[a-zA-Z]/.test(password)) {
    errors.push('At least one letter');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]/.test(password)) {
    errors.push('At least one special character');
  }
  
  if (/\s/.test(password)) {
    errors.push('No whitespace allowed');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

const validateEmail = (email) => {
  const emailPattern = /^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailPattern.test(email);
};

export default function CreateAccount({ navigation }) {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');
  const [passwordErrors, setPasswordErrors] = useState([]);
  const [emailError, setEmailError] = useState('');
  const [touched, setTouched] = useState({
    email: false,
    password: false,
  });
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    scroll: {
      padding: 20,
      justifyContent: 'center',
    },
    title: {
      fontSize: 26,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 4,
    },
    subtitle: {
      fontSize: 15,
      color: colors.muted,
      marginBottom: 24,
    },
    input: {
      backgroundColor: colors.card,
      borderRadius: 10,
      paddingHorizontal: 14,
      paddingVertical: 12,
      fontSize: 16,
      marginBottom: 16,
      borderWidth: 1,
      borderColor: colors.border,
      color: colors.text,
    },
    passwordContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    eyeIcon: {
      position: 'absolute',
      right: 14,
      top: '50%',
      transform: [{ translateY: -10 }],
    },
    createButton: {
      backgroundColor: colors.accent,
      paddingVertical: 14,
      borderRadius: 10,
      marginTop: 8,
      alignItems: 'center',
    },
    createButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
    },
    dividerContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginVertical: 20,
    },
    line: {
      flex: 1,
      height: 1,
      backgroundColor: colors.border,
    },
    orText: {
      marginHorizontal: 8,
      color: colors.muted,
    },
    oauthContainer: {
      gap: 12,
    },
    oauthButton: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      borderWidth: 1,
      borderColor: colors.border,
      paddingVertical: 12,
      borderRadius: 10,
      backgroundColor: colors.card,
    },
    oauthText: {
      marginLeft: 8,
      fontWeight: '500',
      color: colors.text,
    },
    loginLink: {
      alignItems: 'center',
      marginTop: 20,
    },
    loginText: {
      color: colors.text,
    },
    loginTextHighlight: {
      color: colors.accent,
      fontWeight: '700',
    },
    errorText: {
      color: colors.danger,
      fontSize: 12,
      marginTop: 4,
      marginBottom: 8,
    },
    passwordRequirements: {
      marginTop: 4,
      marginBottom: 8,
    },
    requirementItem: {
      flexDirection: 'row',
      alignItems: 'center',
      marginVertical: 2,
    },
    requirementText: {
      fontSize: 11,
      marginLeft: 6,
    },
    requirementMet: {
      color: '#10B981',
    },
    requirementNotMet: {
      color: colors.muted,
    },
    inputError: {
      borderColor: colors.danger,
      borderWidth: 1.5,
    },
  }));
  const { signUp, authError, clearError } = useAuth();

  const goToSignIn = () => {
    if (authError) clearError();
    if (localError) setLocalError('');
    navigation?.navigate('SignIn');
  };

  const handleEmailChange = (value) => {
    setEmail(value);
    if (localError) setLocalError('');
    clearError();
    
    if (touched.email) {
      if (!value.trim()) {
        setEmailError('');
      } else if (!validateEmail(value.trim())) {
        setEmailError('Invalid email format (e.g., user@domain.com)');
      } else {
        setEmailError('');
      }
    }
  };

  const handlePasswordChange = (value) => {
    setPassword(value);
    if (localError) setLocalError('');
    clearError();
    
    if (touched.password) {
      const validation = validatePassword(value);
      setPasswordErrors(validation.errors);
    }
  };

  const handleCreateAccount = async () => {
    // Mark all fields as touched
    setTouched({ email: true, password: true });

    // Validate all fields
    if (!name.trim() || !username.trim() || !email.trim() || !password) {
      setLocalError('All fields are required.');
      return;
    }

    // Validate email format
    if (!validateEmail(email.trim())) {
      setEmailError('Invalid email format (e.g., user@domain.com)');
      setLocalError('Please fix the errors above.');
      return;
    }

    // Validate password
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      setPasswordErrors(passwordValidation.errors);
      setLocalError('Password does not meet requirements.');
      return;
    }

    setSubmitting(true);
    setLocalError('');
    clearError();
    try {
      await signUp({
        email: email.trim(),
        username: username.trim(),
        password,
        displayName: name.trim(),
      });
    } catch (error) {
      setLocalError(error.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Sign up to get started</Text>

        <TextInput
          style={styles.input}
          placeholder="Name"
          placeholderTextColor={theme.colors.muted}
          value={name}
          onChangeText={(value) => {
            setName(value);
            if (localError) setLocalError('');
            clearError();
          }}
        />

        <TextInput
          style={styles.input}
          placeholder="Username"
          placeholderTextColor={theme.colors.muted}
          autoCapitalize="none"
          value={username}
          onChangeText={(value) => {
            setUsername(value);
            if (localError) setLocalError('');
            clearError();
          }}
        />

        <TextInput
          style={[styles.input, emailError && touched.email && styles.inputError]}
          placeholder="Email Address"
          placeholderTextColor={theme.colors.muted}
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={handleEmailChange}
          onBlur={() => setTouched(prev => ({ ...prev, email: true }))}
        />
        {emailError && touched.email && (
          <Text style={styles.errorText}>{emailError}</Text>
        )}

        <View style={styles.passwordContainer}>
          <TextInput
            style={[styles.input, { flex: 1, marginBottom: 0 }, passwordErrors.length > 0 && touched.password && styles.inputError]}
            placeholder="Password"
            placeholderTextColor={theme.colors.muted}
            secureTextEntry={!showPassword}
            value={password}
            onChangeText={handlePasswordChange}
            onBlur={() => setTouched(prev => ({ ...prev, password: true }))}
          />
          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={styles.eyeIcon}
          >
            <Ionicons
              name={showPassword ? 'eye-off' : 'eye'}
              size={20}
              color={theme.colors.muted}
            />
          </TouchableOpacity>
        </View>

        {/* Password requirements - show when password field is touched */}
        {touched.password && password.length > 0 && (
          <View style={styles.passwordRequirements}>
            <Text style={[styles.requirementText, { color: theme.colors.muted, marginBottom: 4, fontWeight: '600' }]}>
              Password must contain:
            </Text>
            {[
              { label: 'At least 8 characters', met: password.length >= 8 },
              { label: 'At least one number', met: /\d/.test(password) },
              { label: 'At least one letter', met: /[a-zA-Z]/.test(password) },
              { label: 'At least one special character', met: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]/.test(password) },
              { label: 'No whitespace', met: !/\s/.test(password) },
            ].map((req, index) => (
              <View key={index} style={styles.requirementItem}>
                <Ionicons
                  name={req.met ? 'checkmark-circle' : 'ellipse-outline'}
                  size={14}
                  color={req.met ? '#10B981' : theme.colors.muted}
                />
                <Text style={[styles.requirementText, req.met ? styles.requirementMet : styles.requirementNotMet]}>
                  {req.label}
                </Text>
              </View>
            ))}
          </View>
        )}

        {(authError || localError) && (
          <Text style={{ color: theme.colors.danger, fontWeight: '600', marginBottom: 12 }}>
            {(authError?.message) || localError}
          </Text>
        )}

        <TouchableOpacity
          style={styles.createButton}
          onPress={handleCreateAccount}
          disabled={submitting}
        >
          {submitting ? (
            <Text style={styles.createButtonText}>Creating...</Text>
          ) : (
            <Text style={styles.createButtonText}>Create Account</Text>
          )}
        </TouchableOpacity>

        <View style={styles.dividerContainer}>
          <View style={styles.line} />
          <Text style={styles.orText}>OR</Text>
          <View style={styles.line} />
        </View>

        <View style={styles.oauthContainer}>
          <TouchableOpacity style={styles.oauthButton} onPress={goToSignIn}>
            <FontAwesome name="google" size={20} color="#DB4437" />
            <Text style={styles.oauthText}>Continue with Google</Text>
          </TouchableOpacity>

          {/* <TouchableOpacity style={styles.oauthButton} onPress={goToSignIn}>
            <FontAwesome name="apple" size={20} color={theme.colors.text} />
            <Text style={styles.oauthText}>Continue with Apple</Text>
          </TouchableOpacity> */}
        </View>

        <TouchableOpacity
          onPress={goToSignIn}
          style={styles.loginLink}
        >
          <Text style={styles.loginText}>
            Already have an account? <Text style={styles.loginTextHighlight}>Login</Text>
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}
