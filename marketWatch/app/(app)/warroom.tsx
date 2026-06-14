import { useState, useEffect, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  RefreshControl,
} from "react-native";
import { Swords, AlertTriangle, RefreshCw } from "lucide-react-native";
import { api, type WarRoomReport, type Signal } from "../../services/apiClient";

// ─────────────────────────────────────────────────────────────────────────────
// War Room Report Card
// ─────────────────────────────────────────────────────────────────────────────

function WarRoomCard({ report }: { report: WarRoomReport }) {
  const impactColor =
    report.impact_score >= 8
      ? "#F87171"
      : report.impact_score >= 6
      ? "#FB923C"
      : "#FBBF24";

  const actions = report.recommended_actions
    ? report.recommended_actions.split("\n").filter(Boolean)
    : [];

  return (
    <View style={[wrc.container, { borderLeftColor: impactColor }]}>
      {/* Impact score */}
      <View style={wrc.headerRow}>
        <View>
          <Text style={wrc.competitorId}>
            {report.competitor_id.replace("disc-", "").replace("comp-", "").toUpperCase()}
          </Text>
          <Text style={wrc.dateText}>
            {new Date(report.created_at).toLocaleDateString("en-IN", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
          </Text>
        </View>
        <View style={[wrc.impactBadge, { borderColor: impactColor }]}>
          <Text style={[wrc.impactLabel, { color: impactColor }]}>IMPACT</Text>
          <Text style={[wrc.impactValue, { color: impactColor }]}>
            {report.impact_score.toFixed(1)}
          </Text>
        </View>
      </View>

      {/* Threat summary */}
      <Text style={wrc.summary}>{report.threat_summary}</Text>

      {/* Recommended actions */}
      {actions.length > 0 && (
        <View style={wrc.actionsBox}>
          <Text style={wrc.actionsLabel}>RECOMMENDED ACTIONS</Text>
          {actions.map((action, i) => (
            <View key={i} style={wrc.actionRow}>
              <View style={[wrc.actionDot, { backgroundColor: impactColor }]} />
              <Text style={wrc.actionText}>{action.replace(/^\d+\.\s*/, "")}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const wrc = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    borderLeftWidth: 4,
    padding: 16,
    marginBottom: 14,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  competitorId: {
    fontSize: 14,
    fontWeight: "800",
    color: "#F1F5F9",
    letterSpacing: 1,
  },
  dateText: {
    fontSize: 12,
    color: "#475569",
    marginTop: 2,
  },
  impactBadge: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignItems: "center",
    backgroundColor: "#0F172A",
  },
  impactLabel: {
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  impactValue: {
    fontSize: 22,
    fontWeight: "800",
    marginTop: 2,
  },
  summary: {
    fontSize: 14,
    color: "#E2E8F0",
    lineHeight: 22,
    marginBottom: 14,
  },
  actionsBox: {
    backgroundColor: "#0F172A",
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  actionsLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 1.2,
    marginBottom: 10,
    textTransform: "uppercase",
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    marginBottom: 8,
  },
  actionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    flexShrink: 0,
  },
  actionText: {
    flex: 1,
    fontSize: 13,
    color: "#94A3B8",
    lineHeight: 20,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// War Room Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function WarRoomScreen() {
  const [reports, setReports] = useState<WarRoomReport[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [reportsData, signalsData] = await Promise.all([
        api.warroom.list(),
        api.signals.list({ sort_by: "impact", limit: 50 }),
      ]);
      setReports(reportsData);
      setSignals(signalsData);
    } catch (err: any) {
      setError(err?.message ?? "Failed to load War Room data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalImpact =
    reports.length > 0
      ? (reports.reduce((s, r) => s + r.impact_score, 0) / reports.length).toFixed(1)
      : "—";
  const criticalCount = reports.filter((r) => r.impact_score >= 8).length;

  if (loading) {
    return (
      <View style={screen.centered}>
        <ActivityIndicator size="large" color="#22D3EE" />
        <Text style={screen.loadingText}>Loading War Room…</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={screen.centered}>
        <AlertTriangle size={32} color="#F87171" />
        <Text style={screen.errorText}>{error}</Text>
        <Pressable style={screen.retryBtn} onPress={() => fetchData()}>
          <Text style={screen.retryBtnText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView
      style={screen.container}
      contentContainerStyle={screen.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => fetchData(true)}
          tintColor="#22D3EE"
        />
      }
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <View style={screen.header}>
        <View style={screen.titleRow}>
          <Swords size={20} color="#F87171" />
          <View>
            <Text style={screen.title}>War Room</Text>
            <Text style={screen.subtitle}>Critical threat response</Text>
          </View>
        </View>

        {/* Alert strip */}
        {reports.length > 0 && (
          <View style={screen.alertStrip}>
            <View style={screen.alertStat}>
              <Text style={[screen.alertValue, { color: "#F87171" }]}>
                {criticalCount}
              </Text>
              <Text style={screen.alertLabel}>CRITICAL</Text>
            </View>
            <View style={[screen.alertStat, { borderLeftWidth: 1, borderColor: "#334155" }]}>
              <Text style={[screen.alertValue, { color: "#FB923C" }]}>{totalImpact}</Text>
              <Text style={screen.alertLabel}>AVG IMPACT</Text>
            </View>
            <View style={[screen.alertStat, { borderLeftWidth: 1, borderColor: "#334155" }]}>
              <Text style={screen.alertValue}>{reports.length}</Text>
              <Text style={screen.alertLabel}>REPORTS</Text>
            </View>
          </View>
        )}
      </View>

      <View style={screen.body}>
        {/* ── War Room Reports ─────────────────────────────────────── */}
        <Text style={screen.sectionLabel}>
          THREAT BRIEFINGS ({reports.length})
        </Text>

        {reports.length === 0 ? (
          <View style={screen.emptyState}>
            <Swords size={32} color="#334155" />
            <Text style={screen.emptyText}>
              No threat briefings yet.{"\n"}Initialise your War Room from the Dashboard.
            </Text>
          </View>
        ) : (
          reports
            .sort((a, b) => b.impact_score - a.impact_score)
            .map((report) => <WarRoomCard key={report.id} report={report} />)
        )}
      </View>
    </ScrollView>
  );
}

const screen = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F1F5F9",
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  alertStrip: {
    flexDirection: "row",
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    overflow: "hidden",
  },
  alertStat: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
  },
  alertValue: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F1F5F9",
  },
  alertLabel: {
    fontSize: 9,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 0.8,
    marginTop: 2,
    textTransform: "uppercase",
  },
  body: {
    padding: 16,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.5,
    color: "#475569",
    marginBottom: 12,
    textTransform: "uppercase",
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
    backgroundColor: "#0F172A",
  },
  loadingText: {
    fontSize: 14,
    color: "#64748B",
  },
  errorText: {
    fontSize: 14,
    color: "#F87171",
    textAlign: "center",
    lineHeight: 22,
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 32,
    gap: 12,
  },
  emptyText: {
    fontSize: 14,
    color: "#475569",
    textAlign: "center",
    lineHeight: 22,
  },
  retryBtn: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  retryBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#22D3EE",
  },
});
