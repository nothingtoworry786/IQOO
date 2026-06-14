import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, AppState, type AppStateStatus } from 'react-native';
import { WifiOff } from 'lucide-react-native';

// Standard Android connectivity probe endpoint — returns 204 with empty body
const PROBE_URL = 'https://connectivitycheck.gstatic.com/generate_204';
const PROBE_INTERVAL = 20_000;
const PROBE_TIMEOUT = 4_000;

async function checkOnline(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), PROBE_TIMEOUT);
    const res = await fetch(PROBE_URL, { method: 'HEAD', signal: controller.signal });
    clearTimeout(id);
    return res.status === 204 || res.ok;
  } catch {
    return false;
  }
}

export default function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function probe() {
      const online = await checkOnline();
      if (mounted) setIsOffline(!online);
    }

    probe();
    const timer = setInterval(probe, PROBE_INTERVAL);
    const sub = AppState.addEventListener('change', (s: AppStateStatus) => {
      if (s === 'active') probe();
    });

    return () => {
      mounted = false;
      clearInterval(timer);
      sub.remove();
    };
  }, []);

  if (!isOffline) return null;

  return (
    <View style={styles.banner}>
      <WifiOff size={12} color="#F8FAFC" />
      <Text style={styles.text}>You're offline — showing cached data</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#475569',
    paddingHorizontal: 16,
    paddingVertical: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  text: {
    fontSize: 12,
    fontWeight: '500',
    color: '#F8FAFC',
    flex: 1,
  },
});
