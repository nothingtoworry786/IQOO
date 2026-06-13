import { Text, View, StyleSheet } from "react-native";

export default function ProfileScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile</Text>
      <Text style={styles.subtitle}>
        Account settings and alert preferences
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0F172A",
  },
  title: {
    fontSize: 18,
    fontWeight: "600",
    color: "#F1F5F9",
  },
  subtitle: {
    marginTop: 8,
    fontSize: 14,
    color: "#94A3B8",
  },
});
