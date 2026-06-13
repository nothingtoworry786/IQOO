import { Text, View, ScrollView, StyleSheet } from "react-native";
import { ShieldAlert } from "lucide-react-native";
import Card from "@/components/ui/Card";

/**
 * Dashboard — the primary screen users see after authentication.
 * Displays a summary of competitive intelligence signals and momentum scores.
 */
export default function DashboardScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>War Room</Text>
        <Text style={styles.subtitle}>
          Real-time competitive intelligence feed
        </Text>
      </View>

      {/* Example priority card */}
      <Card
        title="Blinkit Ops Hiring Surge"
        subtitle="23 operations & logistics roles posted in Pune over 48 hours"
        priority="high"
        icon={<ShieldAlert size={18} color="#FB923C" />}
        action={{ label: "View Brief", onPress: () => {} }}
      >
        <View style={styles.cardBody}>
          <View style={styles.signalRow}>
            <View style={[styles.dot, { backgroundColor: "#FB923C" }]} />
            <Text style={styles.signalText}>Expansion risk detected</Text>
          </View>
          <View style={[styles.signalRow, styles.signalRowSpaced]}>
            <View style={[styles.dot, { backgroundColor: "#22D3EE" }]} />
            <Text style={styles.signalText}>
              Confidence: 74% — matches historical pattern
            </Text>
          </View>
        </View>
      </Card>

      {/* Standard card example */}
      <View style={styles.cardSpacing}>
        <Card
          title="Market Snapshot"
          subtitle="Competitor momentum scores this week"
          variant="elevated"
        >
          <View style={styles.competitorList}>
            <View style={styles.competitorRow}>
              <Text style={styles.competitorName}>Blinkit</Text>
              <View style={styles.scoreRow}>
                <Text style={[styles.scoreValue, { color: "#22D3EE" }]}>8.4</Text>
                <Text style={[styles.scoreDelta, { color: "#4ADE80" }]}>↑ +1.2</Text>
              </View>
            </View>
            <View style={styles.competitorRow}>
              <Text style={styles.competitorName}>Swiggy Instamart</Text>
              <View style={styles.scoreRow}>
                <Text style={[styles.scoreValue, { color: "#94A3B8" }]}>5.1</Text>
                <Text style={[styles.scoreDelta, { color: "#94A3B8" }]}>→ +0.1</Text>
              </View>
            </View>
            <View style={styles.competitorRow}>
              <Text style={styles.competitorName}>Zepto (You)</Text>
              <View style={styles.scoreRow}>
                <Text style={[styles.scoreValue, { color: "#4ADE80" }]}>6.8</Text>
                <Text style={[styles.scoreDelta, { color: "#4ADE80" }]}>↑ +0.9</Text>
              </View>
            </View>
          </View>
        </Card>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
    marginTop: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    letterSpacing: -0.5,
    color: "#F1F5F9",
  },
  subtitle: {
    marginTop: 4,
    fontSize: 14,
    color: "#94A3B8",
  },
  cardBody: {
    marginTop: 4,
  },
  signalRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  signalRowSpaced: {
    marginTop: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  signalText: {
    fontSize: 14,
    color: "#94A3B8",
  },
  cardSpacing: {
    marginTop: 16,
  },
  competitorList: {
    marginTop: 8,
    gap: 12,
  },
  competitorRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  competitorName: {
    fontSize: 14,
    color: "#94A3B8",
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: "600",
  },
  scoreDelta: {
    fontSize: 12,
  },
});
