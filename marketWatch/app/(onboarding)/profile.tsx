import React, { useState } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { router } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Building2, Globe, FileText, ArrowRight } from "lucide-react-native";
import InputField from "../../src/components/ui/InputField";
import Button from "../../src/components/ui/Button";

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [companyDescription, setCompanyDescription] = useState("");
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const isValidUrl = (url: string) => {
    const trimmed = url.trim();
    return trimmed.length >= 4 && trimmed.includes(".");
  };

  const isProfileDisabled = !companyName.trim() || !isValidUrl(websiteUrl);

  const handleNext = () => {
    if (isProfileDisabled) return;
    router.replace({
      pathname: "/(onboarding)/processing",
      params: {
        companyName: companyName.trim(),
        websiteUrl: websiteUrl.trim(),
        companyDescription: companyDescription.trim(),
      },
    });
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.container}>
        <StatusBar style="light" />

        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 20) + 12 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.formSection}>
            <Text style={styles.formTitle}>Tell us about your Business</Text>
            <Text style={styles.formDesc}>
              These parameters help set up our scanning lens for your company website and business profile.
            </Text>

            {/* Name Input */}
            <InputField
              label="Company Name"
              icon={<Building2 size={16} color={focusedField === "name" ? "#22D3EE" : "#64748B"} />}
              placeholder="e.g. Zepto, Stripe, Vercel"
              value={companyName}
              onChangeText={setCompanyName}
              autoCapitalize="words"
              autoCorrect={false}
              isFocused={focusedField === "name"}
              onFocus={() => setFocusedField("name")}
              onBlur={() => setFocusedField(null)}
            />

            {/* Website Input */}
            <InputField
              label="Website URL"
              icon={<Globe size={16} color={focusedField === "website" ? "#22D3EE" : "#64748B"} />}
              placeholder="https://yourcompany.com"
              value={websiteUrl}
              onChangeText={setWebsiteUrl}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              isFocused={focusedField === "website"}
              onFocus={() => setFocusedField("website")}
              onBlur={() => setFocusedField(null)}
            />

            {/* Business Description Input */}
            <InputField
              label="Business Description"
              icon={<FileText size={16} color={focusedField === "description" ? "#22D3EE" : "#64748B"} />}
              placeholder="e.g. Hyperlocal 10-minute grocery delivery platform using a network of dark stores."
              value={companyDescription}
              onChangeText={setCompanyDescription}
              multiline
              numberOfLines={4}
              autoCapitalize="sentences"
              autoCorrect={true}
              isFocused={focusedField === "description"}
              onFocus={() => setFocusedField("description")}
              onBlur={() => setFocusedField(null)}
            />

            {/* Action buttons */}
            <View style={styles.btnRow}>
              <Button
                style={{ flex: 1 }}
                text="Begin Setup"
                onPress={handleNext}
                disabled={isProfileDisabled}
                icon={<ArrowRight size={18} color={isProfileDisabled ? "#475569" : "#0F172A"} />}
                iconPosition="right"
              />
            </View>
          </View>
          <View style={{ height: 40 }} />
        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0B1121",
  },
  content: {
    paddingBottom: 40,
  },
  formSection: {
    paddingHorizontal: 24,
    gap: 18,
    paddingTop: 12,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: "#F8FAFC",
    letterSpacing: -0.5,
  },
  formDesc: {
    fontSize: 13,
    color: "#64748B",
    lineHeight: 20,
    marginBottom: 6,
  },
  btnRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
});
