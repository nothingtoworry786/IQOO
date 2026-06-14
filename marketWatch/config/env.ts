import Constants from 'expo-constants';
import { Platform } from 'react-native';

// ─────────────────────────────────────────────────────────────────────────────
// HOW TO CONNECT IN DEV
//
// Android emulator (AVD):   10.0.2.2 is the host loopback alias — works as-is.
// Physical Android device:  Change DEV_PHYSICAL_IP to your machine's Wi-Fi IP.
//                           Run: ipconfig  →  look for Wi-Fi IPv4 address.
// iOS simulator:            localhost works as-is.
// ─────────────────────────────────────────────────────────────────────────────

const DEV_EMULATOR_URL = 'http://localhost:8000';        // Android emulator (via adb reverse)
const DEV_PHYSICAL_URL = 'http://192.168.9.233:8000';  // Physical device — Wi-Fi IP
const DEV_IOS_URL      = 'http://localhost:8000';       // iOS simulator

function devUrl(): string {
  if (Platform.OS === 'ios') return DEV_IOS_URL;
  return DEV_PHYSICAL_URL;
}

const ENVIRONMENTS = {
  development: {
    apiBaseUrl: devUrl(),
  },
  staging: {
    apiBaseUrl: 'https://staging-api.competitorgpt.com',
  },
  production: {
    apiBaseUrl: 'https://api.competitorgpt.com',
  },
} as const;

type EnvName = keyof typeof ENVIRONMENTS;

function getEnvironment(): EnvName {
  if (__DEV__) return 'development';
  const extra = Constants.expoConfig?.extra as { environment?: string } | undefined;
  const env = extra?.environment;
  if (env === 'staging') return 'staging';
  return 'production';
}

export const apiBaseUrl = ENVIRONMENTS[getEnvironment()].apiBaseUrl;
