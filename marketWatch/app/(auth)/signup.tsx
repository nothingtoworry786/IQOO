import { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react-native';
import Button from '../../src/components/ui/Button';
import InputField from '../../src/components/ui/InputField';
import { useAuth } from '../../contexts/AuthContext';

// ─────────────────────────────────────────────────────────────────────────────
// Validation
// ─────────────────────────────────────────────────────────────────────────────

function validateEmail(e: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
}

// ─────────────────────────────────────────────────────────────────────────────
// Sign Up Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function SignUpScreen() {
  const { signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  // Per-field errors (shown only after blur)
  const [emailBlurred, setEmailBlurred] = useState(false);
  const [passwordBlurred, setPasswordBlurred] = useState(false);
  const [confirmBlurred, setConfirmBlurred] = useState(false);
  const [apiError, setApiError] = useState('');

  const emailError =
    emailBlurred && email.trim() && !validateEmail(email)
      ? 'Enter a valid email address.'
      : '';
  const passwordError =
    passwordBlurred && password.length > 0 && password.length < 8
      ? 'Password must be at least 8 characters.'
      : '';
  const confirmError =
    confirmBlurred && confirm.length > 0 && confirm !== password
      ? 'Passwords do not match.'
      : '';

  const canSubmit =
    validateEmail(email) &&
    password.length >= 8 &&
    confirm === password &&
    !loading;

  const iconColor = '#64748B';

  async function handleSignUp() {
    if (!canSubmit) {
      setEmailBlurred(true);
      setPasswordBlurred(true);
      setConfirmBlurred(true);
      return;
    }
    setApiError('');
    setLoading(true);
    try {
      await signup(email.trim().toLowerCase(), password);
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e?.status === 409 || e?.status === 400) {
        setApiError('An account with this email already exists.');
      } else if (e?.status === 0) {
        setApiError('Cannot reach server. Check your connection.');
      } else {
        setApiError(e?.message ?? 'Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        style={styles.kav}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Logo */}
          <View style={styles.logoSection}>
            <View style={styles.logoInner}>
              <Shield size={26} color="#22D3EE" />
            </View>
            <Text style={styles.appName}>MarketWatch</Text>
            <Text style={styles.tagline}>Create your command centre</Text>
          </View>

          {/* Card */}
          <View style={styles.card}>
            <Text style={styles.headline}>Create account</Text>
            <Text style={styles.subheadline}>
              Join thousands of founders tracking competitors
            </Text>

            <View style={styles.fields}>
              <View>
                <InputField
                  label="Email"
                  icon={<Mail size={16} color={iconColor} />}
                  value={email}
                  onChangeText={(t) => { setEmail(t); setApiError(''); }}
                  placeholder="you@company.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoComplete="email"
                  returnKeyType="next"
                  onBlur={() => setEmailBlurred(true)}
                />
                {emailError !== '' && (
                  <Text style={styles.fieldError}>{emailError}</Text>
                )}
              </View>

              <View>
                <View style={styles.passwordWrap}>
                  <InputField
                    label="Password"
                    icon={<Lock size={16} color={iconColor} />}
                    value={password}
                    onChangeText={(t) => { setPassword(t); setApiError(''); }}
                    placeholder="Min 8 characters"
                    secureTextEntry={!showPassword}
                    returnKeyType="next"
                    onBlur={() => setPasswordBlurred(true)}
                  />
                  <Pressable
                    style={styles.eyeToggle}
                    onPress={() => setShowPassword((p) => !p)}
                    accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <EyeOff size={16} color="#64748B" />
                    ) : (
                      <Eye size={16} color="#64748B" />
                    )}
                  </Pressable>
                </View>
                {passwordError !== '' && (
                  <Text style={styles.fieldError}>{passwordError}</Text>
                )}
              </View>

              <View>
                <View style={styles.passwordWrap}>
                  <InputField
                    label="Confirm Password"
                    icon={<Lock size={16} color={iconColor} />}
                    value={confirm}
                    onChangeText={(t) => { setConfirm(t); setApiError(''); }}
                    placeholder="Re-enter password"
                    secureTextEntry={!showConfirm}
                    returnKeyType="done"
                    onBlur={() => setConfirmBlurred(true)}
                    onSubmitEditing={handleSignUp}
                  />
                  <Pressable
                    style={styles.eyeToggle}
                    onPress={() => setShowConfirm((p) => !p)}
                    accessibilityLabel={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirm ? (
                      <EyeOff size={16} color="#64748B" />
                    ) : (
                      <Eye size={16} color="#64748B" />
                    )}
                  </Pressable>
                </View>
                {confirmError !== '' && (
                  <Text style={styles.fieldError}>{confirmError}</Text>
                )}
              </View>
            </View>

            {apiError !== '' && (
              <Text style={styles.apiError}>{apiError}</Text>
            )}

            <Button
              text={loading ? 'Creating account…' : 'Create Account'}
              onPress={handleSignUp}
              variant="primary"
              disabled={loading}
              style={styles.btn}
            />

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR</Text>
              <View style={styles.dividerLine} />
            </View>

            <View style={styles.loginRow}>
              <Text style={styles.loginLabel}>Already have an account?</Text>
              <Pressable onPress={() => router.back()}>
                <Text style={styles.loginLink}> Sign In</Text>
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#0B1121',
  },
  kav: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 40,
    alignItems: 'center',
  },
  logoSection: {
    alignItems: 'center',
    paddingTop: 16,
    marginBottom: 32,
  },
  logoInner: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: '#164E63',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#22D3EE',
    marginBottom: 16,
  },
  appName: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F8FAFC',
    letterSpacing: 0.5,
  },
  tagline: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
    letterSpacing: 0.3,
  },
  card: {
    width: '100%',
    backgroundColor: '#0F172A',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#1E293B',
    padding: 24,
  },
  headline: {
    fontSize: 22,
    fontWeight: '800',
    color: '#F8FAFC',
    marginBottom: 4,
  },
  subheadline: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 28,
  },
  fields: {
    gap: 16,
    marginBottom: 8,
  },
  passwordWrap: {
    position: 'relative',
  },
  eyeToggle: {
    position: 'absolute',
    right: 14,
    top: 38,
    padding: 4,
  },
  fieldError: {
    fontSize: 12,
    color: '#F87171',
    marginTop: 5,
    marginLeft: 4,
  },
  apiError: {
    fontSize: 13,
    color: '#F87171',
    marginBottom: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  btn: {
    marginTop: 4,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
    gap: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#1E293B',
  },
  dividerText: {
    fontSize: 11,
    color: '#475569',
    fontWeight: '700',
    letterSpacing: 1,
  },
  loginRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginLabel: {
    fontSize: 14,
    color: '#94A3B8',
  },
  loginLink: {
    fontSize: 14,
    color: '#22D3EE',
    fontWeight: '700',
  },
});
