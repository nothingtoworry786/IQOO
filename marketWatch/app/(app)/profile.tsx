import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  Pressable,
  Alert,
  TextInput,
  RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  UserCircle,
  Building2,
  Users,
  Bell,
  BellOff,
  ChevronRight,
  LogOut,
  Trash2,
  Info,
  Shield,
  Pencil,
  Check,
} from 'lucide-react-native';
import { router } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import { getItem, setItem } from '../../services/storage';
import { api } from '../../services/apiClient';
import OfflineBanner from '../../src/components/OfflineBanner';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface NotificationPrefs {
  war_room_alerts: boolean;
  daily_briefing: boolean;
}

const DEFAULT_NOTIF: NotificationPrefs = {
  war_room_alerts: true,
  daily_briefing: false,
};

// ─────────────────────────────────────────────────────────────────────────────
// Helper components
// ─────────────────────────────────────────────────────────────────────────────

function SectionHeader({ title }: { title: string }) {
  return <Text style={styles.sectionHeader}>{title}</Text>;
}

function Card({ children }: { children: React.ReactNode }) {
  return <View style={styles.card}>{children}</View>;
}

function RowDivider() {
  return <View style={styles.rowDivider} />;
}

function SettingsRow({
  icon,
  label,
  value,
  onPress,
  showChevron = false,
  rightElement,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string;
  onPress?: () => void;
  showChevron?: boolean;
  rightElement?: React.ReactNode;
}) {
  return (
    <Pressable
      style={styles.settingsRow}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.rowLeft}>
        <View style={styles.rowIcon}>{icon}</View>
        <Text style={styles.rowLabel}>{label}</Text>
      </View>
      <View style={styles.rowRight}>
        {value !== undefined && (
          <Text style={styles.rowValue} numberOfLines={1}>
            {value}
          </Text>
        )}
        {rightElement}
        {showChevron && <ChevronRight size={16} color="#475569" />}
      </View>
    </Pressable>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Profile Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { userId, userEmail, logout } = useAuth();

  const [companyName, setCompanyNameState] = useState('');
  const [competitorCount, setCompetitorCount] = useState(0);
  const [role, setRole] = useState('');
  const [editingRole, setEditingRole] = useState(false);
  const [roleInput, setRoleInput] = useState('');
  const [notifPrefs, setNotifPrefs] = useState<NotificationPrefs>(DEFAULT_NOTIF);
  const [refreshing, setRefreshing] = useState(false);

  // Derive initials from email
  const initials = userEmail
    ? userEmail.split('@')[0].slice(0, 2).toUpperCase()
    : 'MW';

  const displayEmail = userEmail ?? userId ?? '—';

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    const [savedName, savedRole, savedNotif, competitors] = await Promise.all([
      getItem<string>('cache_company_name'),
      getItem<string>('user_role'),
      getItem<NotificationPrefs>('notification_prefs'),
      api.competitors.list(50).catch(() => []),
    ]);
    if (savedName) setCompanyNameState(savedName);
    if (savedRole) setRole(savedRole);
    if (savedNotif) setNotifPrefs(savedNotif);
    setCompetitorCount(competitors.length);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const saveRole = useCallback(async () => {
    const trimmed = roleInput.trim();
    setRole(trimmed);
    setEditingRole(false);
    await setItem('user_role', trimmed);
  }, [roleInput]);

  const toggleNotif = useCallback(
    async (key: keyof NotificationPrefs) => {
      const updated = { ...notifPrefs, [key]: !notifPrefs[key] };
      setNotifPrefs(updated);
      await setItem('notification_prefs', updated);
    },
    [notifPrefs]
  );

  const handleLogout = useCallback(() => {
    Alert.alert(
      'Log Out',
      'Are you sure you want to log out of MarketWatch?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
          },
        },
      ]
    );
  }, [logout]);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <OfflineBanner />

      {/* Header */}
      <View style={styles.header}>
        <Shield size={18} color="#22D3EE" />
        <Text style={styles.headerTitle}>Profile</Text>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadData(true)}
            tintColor="#22D3EE"
            colors={["#22D3EE"]}
          />
        }
      >
        {/* ── USER INFO ─────────────────────────────────────────────────── */}
        <SectionHeader title="ACCOUNT" />
        <Card>
          {/* Avatar + name row */}
          <View style={styles.avatarRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{initials}</Text>
            </View>
            <View style={styles.avatarInfo}>
              <Text style={styles.emailText} numberOfLines={1}>
                {displayEmail}
              </Text>
              {companyName !== '' && (
                <Text style={styles.companyText} numberOfLines={1}>
                  {companyName}
                </Text>
              )}
              <View style={styles.statBadge}>
                <Users size={11} color="#22D3EE" />
                <Text style={styles.statBadgeText}>
                  {competitorCount} {competitorCount === 1 ? 'competitor' : 'competitors'} tracked
                </Text>
              </View>
            </View>
          </View>

          <RowDivider />

          {/* Role */}
          <View style={styles.settingsRow}>
            <View style={styles.rowLeft}>
              <View style={styles.rowIcon}>
                <UserCircle size={16} color="#94A3B8" />
              </View>
              <Text style={styles.rowLabel}>Role</Text>
            </View>
            <View style={styles.rowRight}>
              {editingRole ? (
                <View style={styles.roleEditRow}>
                  <TextInput
                    style={styles.roleInput}
                    value={roleInput}
                    onChangeText={setRoleInput}
                    placeholder="e.g. CEO, CMO"
                    placeholderTextColor="#475569"
                    autoFocus
                    returnKeyType="done"
                    onSubmitEditing={saveRole}
                    onBlur={saveRole}
                    maxLength={40}
                  />
                  <Pressable onPress={saveRole} style={styles.checkBtn}>
                    <Check size={14} color="#22D3EE" />
                  </Pressable>
                </View>
              ) : (
                <Pressable
                  style={styles.roleValueRow}
                  onPress={() => { setRoleInput(role); setEditingRole(true); }}
                >
                  <Text style={styles.rowValue}>
                    {role !== '' ? role : 'Tap to set'}
                  </Text>
                  <Pencil size={13} color="#475569" style={{ marginLeft: 6 }} />
                </Pressable>
              )}
            </View>
          </View>
        </Card>

        {/* ── COMPANY PROFILE ──────────────────────────────────────────── */}
        <SectionHeader title="COMPANY" />
        <Card>
          <SettingsRow
            icon={<Building2 size={16} color="#94A3B8" />}
            label="Company"
            value={companyName !== '' ? companyName : 'Not set'}
          />
          <RowDivider />
          <SettingsRow
            icon={<Pencil size={16} color="#94A3B8" />}
            label="Edit Company Details"
            onPress={() => router.push('/(onboarding)/profile' as never)}
            showChevron
          />
        </Card>

        {/* ── NOTIFICATIONS ─────────────────────────────────────────────── */}
        <SectionHeader title="NOTIFICATIONS" />
        <Card>
          <SettingsRow
            icon={<Bell size={16} color="#94A3B8" />}
            label="War Room Alerts"
            rightElement={
              <Switch
                value={notifPrefs.war_room_alerts}
                onValueChange={() => toggleNotif('war_room_alerts')}
                trackColor={{ false: '#334155', true: '#0E7490' }}
                thumbColor={notifPrefs.war_room_alerts ? '#22D3EE' : '#64748B'}
              />
            }
          />
          <RowDivider />
          <SettingsRow
            icon={<BellOff size={16} color="#94A3B8" />}
            label="Daily Briefing"
            rightElement={
              <Switch
                value={notifPrefs.daily_briefing}
                onValueChange={() => toggleNotif('daily_briefing')}
                trackColor={{ false: '#334155', true: '#0E7490' }}
                thumbColor={notifPrefs.daily_briefing ? '#22D3EE' : '#64748B'}
              />
            }
          />
        </Card>

        {/* ── APP INFO ──────────────────────────────────────────────────── */}
        <SectionHeader title="APP" />
        <Card>
          <SettingsRow
            icon={<Info size={16} color="#94A3B8" />}
            label="Version"
            value="1.0.0"
          />
          <RowDivider />
          <SettingsRow
            icon={<Shield size={16} color="#94A3B8" />}
            label="Privacy Policy"
            showChevron
          />
          <RowDivider />
          <SettingsRow
            icon={<Shield size={16} color="#94A3B8" />}
            label="Terms of Service"
            showChevron
          />
        </Card>

        {/* ── DANGER ZONE ───────────────────────────────────────────────── */}
        <SectionHeader title="DANGER ZONE" />
        <Card>
          <Pressable style={styles.logoutBtn} onPress={handleLogout}>
            <LogOut size={16} color="#F87171" />
            <Text style={styles.logoutText}>Log Out</Text>
          </Pressable>
          <RowDivider />
          <View style={styles.deleteRow}>
            <Trash2 size={16} color="#475569" />
            <Text style={styles.deleteText}>Delete Account</Text>
            <View style={styles.soonBadge}>
              <Text style={styles.soonText}>Soon</Text>
            </View>
          </View>
        </Card>

        <View style={{ height: 32 }} />
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
    letterSpacing: 1.2,
    marginBottom: 8,
    marginTop: 20,
    marginLeft: 4,
    textTransform: 'uppercase',
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#334155',
    overflow: 'hidden',
  },
  rowDivider: {
    height: 1,
    backgroundColor: '#334155',
    marginHorizontal: 16,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    padding: 16,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#164E63',
    borderWidth: 2,
    borderColor: '#22D3EE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#22D3EE',
  },
  avatarInfo: {
    flex: 1,
    gap: 3,
  },
  emailText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  companyText: {
    fontSize: 13,
    color: '#94A3B8',
  },
  statBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  statBadgeText: {
    fontSize: 12,
    color: '#22D3EE',
    fontWeight: '600',
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    minHeight: 52,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  rowIcon: {
    width: 22,
    alignItems: 'center',
  },
  rowLabel: {
    fontSize: 14,
    color: '#E2E8F0',
    fontWeight: '500',
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    maxWidth: '55%',
  },
  rowValue: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'right',
  },
  roleEditRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  roleInput: {
    backgroundColor: '#0F172A',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#22D3EE',
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 13,
    color: '#F1F5F9',
    minWidth: 100,
    maxWidth: 140,
  },
  checkBtn: {
    padding: 4,
  },
  roleValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  logoutText: {
    fontSize: 14,
    color: '#F87171',
    fontWeight: '600',
  },
  deleteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    opacity: 0.5,
  },
  deleteText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
    flex: 1,
  },
  soonBadge: {
    backgroundColor: '#1E293B',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  soonText: {
    fontSize: 10,
    color: '#475569',
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
