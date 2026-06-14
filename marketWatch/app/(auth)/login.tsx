import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  Animated,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react-native';
import Button from '../../src/components/ui/Button';
import InputField from '../../src/components/ui/InputField';
import { useAuth } from '../../contexts/AuthContext';

// ─────────────────────────────────────────────────────────────────────────────
// Logo mark — matches the onboarding welcome screen visual language
// ─────────────────────────────────────────────────────────────────────────────

function LogoMark() {
  const pulse = useRef(new Animated.Value(1)).current;
  const pulseOpacity = useRef(new Animated.Value(0.35)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(pulse, { toValue: 1.45, duration: 1600, useNativeDriver: true }),
          Animated.timing(pulseOpacity, { toValue: 0, duration: 1600, useNativeDriver: true }),
        ]),
        Animated.timing(pulse, { toValue: 1, duration: 0, useNativeDriver: true }),
        Animated.timing(pulseOpacity, { toValue: 0.35, duration: 0, useNativeDriver: true }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, [pulse, pulseOpacity]);

  return (
    <View style={logo.wrap}>
      <Animated.View
        style={[logo.ring, { opacity: pulseOpacity, transform: [{ scale: pulse }] }]}
      />
      <View style={logo.inner}>
        <Shield size={26} color="#22D3EE" />
      </View>
    </View>
  );
}

const logo = StyleSheet.create({
  wrap: {
    width: 72,
    height: 72,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  ring: {
    position: 'absolute',
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 2,
    borderColor: '#22D3EE',
  },
  inner: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: '#164E63',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#22D3EE',
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Login Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const iconColor = '#64748B';

  async function handleLogin() {
    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail || !password) {
      setError('Please enter your email and password.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(trimmedEmail, password);
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e?.status === 401 || e?.status === 400) {
        setError('Invalid email or password. Please try again.');
      } else if (e?.status === 0) {
        setError('Cannot reach server. Check your connection.');
      } else {
        setError(e?.message ?? 'Something went wrong. Please try again.');
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
            <LogoMark />
            <Text style={styles.appName}>MarketWatch</Text>
            <Text style={styles.tagline}>AI Competitive War Room</Text>
          </View>

          {/* Card */}
          <View style={styles.card}>
            <Text style={styles.headline}>Welcome back</Text>
            <Text style={styles.subheadline}>Sign in to your command centre</Text>

            <View style={styles.fields}>
              <InputField
                label="Email"
                icon={<Mail size={16} color={iconColor} />}
                value={email}
                onChangeText={(t) => { setEmail(t); setError(''); }}
                placeholder="you@company.com"
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                returnKeyType="next"
              />

              <View style={styles.passwordWrap}>
                <InputField
                  label="Password"
                  icon={<Lock size={16} color={iconColor} />}
                  value={password}
                  onChangeText={(t) => { setPassword(t); setError(''); }}
                  placeholder="Your password"
                  secureTextEntry={!showPassword}
                  autoComplete="password"
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
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

              <Pressable style={styles.forgotWrap} accessibilityLabel="Forgot password">
                <Text style={styles.forgotText}>Forgot password?</Text>
              </Pressable>
            </View>

            {error !== '' && <Text style={styles.errorText}>{error}</Text>}

            <Button
              text={loading ? 'Signing in…' : 'Sign In'}
              onPress={handleLogin}
              variant="primary"
              disabled={loading}
              style={styles.btn}
            />

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR</Text>
              <View style={styles.dividerLine} />
            </View>

            <View style={styles.signupRow}>
              <Text style={styles.signupLabel}>Don't have an account?</Text>
              <Pressable onPress={() => router.push('/(auth)/signup' as never)}>
                <Text style={styles.signupLink}> Sign Up</Text>
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
  forgotWrap: {
    alignSelf: 'flex-end',
  },
  forgotText: {
    fontSize: 13,
    color: '#22D3EE',
    fontWeight: '600',
  },
  errorText: {
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
  signupRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  signupLabel: {
    fontSize: 14,
    color: '#94A3B8',
  },
  signupLink: {
    fontSize: 14,
    color: '#22D3EE',
    fontWeight: '700',
  },
});
