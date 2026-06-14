import { useState, useRef, useEffect, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  TextInput,
  Pressable,
  Animated,
  KeyboardAvoidingView,
  Platform,
  useWindowDimensions,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  MessageCircle,
  Send,
  Bot,
  User,
  PenSquare,
  RotateCcw,
  ShieldCheck,
} from "lucide-react-native";
import { api } from "../../services/apiClient";
import { getItem, setItem, removeItem } from "../../services/storage";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  isError?: boolean;
  retryText?: string;
}

const STORAGE_KEY = "cache_chat_history";

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  text:
    "👋 Welcome to MarketWatch AI!\n\n" +
    "I can answer questions about your tracked competitors — funding, hiring, pricing, expansions, and more.\n\n" +
    "Try asking one of the suggested questions below or type your own!",
  timestamp: new Date().toISOString(),
};

const SUGGESTED_QUESTIONS = [
  "What are the latest competitor funding rounds?",
  "What hiring signals should I watch for?",
  "Any pricing changes I should know about?",
  "Which competitors are expanding to new cities?",
];

// ─────────────────────────────────────────────────────────────────────────────
// Typing indicator
// ─────────────────────────────────────────────────────────────────────────────

function TypingIndicator() {
  const d1 = useRef(new Animated.Value(0)).current;
  const d2 = useRef(new Animated.Value(0)).current;
  const d3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const bounce = (val: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(val, { toValue: -5, duration: 280, useNativeDriver: true }),
          Animated.timing(val, { toValue: 0, duration: 280, useNativeDriver: true }),
          Animated.delay(420),
        ])
      );
    const a1 = bounce(d1, 0);
    const a2 = bounce(d2, 140);
    const a3 = bounce(d3, 280);
    Animated.parallel([a1, a2, a3]).start();
    return () => { a1.stop(); a2.stop(); a3.stop(); };
  }, [d1, d2, d3]);

  return (
    <View style={[bubble.row, bubble.assistantRow]}>
      <View style={bubble.avatarBot}>
        <Bot size={16} color="#A78BFA" />
      </View>
      <View style={[bubble.bubble, bubble.assistantBubble, typing.wrap]}>
        {[d1, d2, d3].map((d, i) => (
          <Animated.View key={i} style={[typing.dot, { transform: [{ translateY: d }] }]} />
        ))}
      </View>
    </View>
  );
}

const typing = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: "#A78BFA" },
});

// ─────────────────────────────────────────────────────────────────────────────
// Chat bubble
// ─────────────────────────────────────────────────────────────────────────────

function ChatBubble({
  message,
  maxBubbleWidth,
  onRetry,
}: {
  message: ChatMessage;
  maxBubbleWidth: number;
  onRetry: (text: string) => void;
}) {
  const isUser = message.role === "user";
  const ts = new Date(message.timestamp);

  return (
    <View style={[bubble.row, isUser ? bubble.userRow : bubble.assistantRow]}>
      {!isUser && (
        <View style={bubble.avatarBot}>
          <Bot size={16} color="#A78BFA" />
        </View>
      )}
      <View
        style={[
          bubble.bubble,
          { maxWidth: maxBubbleWidth },
          isUser ? bubble.userBubble : bubble.assistantBubble,
          message.isError && bubble.errorBubble,
        ]}
      >
        <Text style={isUser ? bubble.userText : bubble.assistantText}>
          {message.text}
        </Text>
        {message.isError && message.retryText && (
          <Pressable style={bubble.retryBtn} onPress={() => onRetry(message.retryText!)}>
            <RotateCcw size={12} color="#22D3EE" />
            <Text style={bubble.retryTxt}>Retry</Text>
          </Pressable>
        )}
        <Text style={bubble.time}>
          {ts.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
        </Text>
      </View>
      {isUser && (
        <View style={bubble.avatarUser}>
          <User size={16} color="#22D3EE" />
        </View>
      )}
    </View>
  );
}

const bubble = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  userRow: { justifyContent: "flex-end" },
  assistantRow: { justifyContent: "flex-start" },
  avatarBot: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#2D1B4E",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#4C1D95",
    alignSelf: "flex-end",
  },
  avatarUser: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#22D3EE",
    alignSelf: "flex-end",
  },
  bubble: {
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: "#164E63",
    borderBottomRightRadius: 4,
    borderWidth: 1,
    borderColor: "#155E75",
  },
  assistantBubble: {
    backgroundColor: "#1E293B",
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: "#334155",
  },
  errorBubble: {
    borderColor: "#7F1D1D",
    backgroundColor: "#1C0A0A",
  },
  userText: { fontSize: 14, color: "#E2E8F0", lineHeight: 20 },
  assistantText: { fontSize: 14, color: "#E2E8F0", lineHeight: 20 },
  time: { fontSize: 10, color: "#475569", marginTop: 6, textAlign: "right" },
  retryBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 8,
    backgroundColor: "#0F172A",
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: "#22D3EE",
  },
  retryTxt: { fontSize: 12, color: "#22D3EE", fontWeight: "600" },
});

// ─────────────────────────────────────────────────────────────────────────────
// Main screen
// ─────────────────────────────────────────────────────────────────────────────

export default function ChatbotScreen() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();

  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastModel, setLastModel] = useState<string | null>(null);
  const [lastSources, setLastSources] = useState<number>(0);
  const scrollRef = useRef<ScrollView>(null);

  // Responsive bubble width: 75% of screen, capped at 320
  const maxBubbleWidth = Math.min(width * 0.75, 320);

  // Load persisted chat history
  useEffect(() => {
    getItem<ChatMessage[]>(STORAGE_KEY).then((saved) => {
      if (saved && saved.length > 1) setMessages(saved);
    });
  }, []);

  // Persist on every change
  useEffect(() => {
    if (messages.length > 1) setItem(STORAGE_KEY, messages);
  }, [messages]);

  // Auto-scroll to bottom
  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
  }, [messages, loading]);

  const clearChat = useCallback(async () => {
    await removeItem(STORAGE_KEY);
    setMessages([{ ...WELCOME_MESSAGE, timestamp: new Date().toISOString() }]);
  }, []);

  const sendMessage = useCallback(
    async (overrideText?: string) => {
      const text = (overrideText ?? input).trim();
      if (!text || loading) return;
      if (!overrideText) setInput("");

      setMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, role: "user", text, timestamp: new Date().toISOString() },
      ]);
      setLoading(true);

      try {
        const response = await api.chat.send(text);
        if (response.model_used) setLastModel(response.model_used);
        setLastSources(response.sources_used ?? 0);
        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: "assistant",
            text: response.reply,
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch (err: unknown) {
        const e = err as { message?: string };
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            text: `Could not reach the AI backend. Is the server running?\n${e?.message ?? ""}`.trim(),
            timestamp: new Date().toISOString(),
            isError: true,
            retryText: text,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading]
  );

  return (
    <KeyboardAvoidingView
      style={[styles.root, { paddingTop: insets.top }]}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <MessageCircle size={20} color="#A78BFA" />
          <View style={styles.titleBlock}>
            <Text style={styles.title}>MarketWatch AI</Text>
            {lastModel ? (
              <View style={styles.localBadge}>
                <ShieldCheck size={11} color="#22C55E" />
                <View style={styles.localDot} />
                <Text style={styles.localBadgeText}>
                  LOCAL AI • {lastModel}
                  {lastSources > 0 ? ` • ${lastSources} sources` : ""}
                </Text>
              </View>
            ) : (
              <Text style={styles.subtitle}>Ask anything about your competitors</Text>
            )}
          </View>
        </View>
        <Pressable
          style={styles.newChatBtn}
          onPress={clearChat}
          accessibilityLabel="New chat"
        >
          <PenSquare size={15} color="#64748B" />
          <Text style={styles.newChatText}>New</Text>
        </Pressable>
      </View>

      {/* ── Messages ────────────────────────────────────────────────────────── */}
      <ScrollView
        ref={scrollRef}
        style={styles.chatArea}
        contentContainerStyle={styles.chatContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {messages.map((msg) => (
          <ChatBubble
            key={msg.id}
            message={msg}
            maxBubbleWidth={maxBubbleWidth}
            onRetry={sendMessage}
          />
        ))}

        {loading && <TypingIndicator />}

        {messages.length === 1 && (
          <View style={styles.suggestionsBox}>
            <Text style={styles.suggestionsLabel}>SUGGESTED QUESTIONS</Text>
            <View style={styles.suggestionsGrid}>
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <Pressable
                  key={i}
                  style={styles.chip}
                  onPress={() => sendMessage(q)}
                >
                  <Text style={styles.chipText}>{q}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* ── Input bar ───────────────────────────────────────────────────────── */}
      <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
        <TextInput
          style={styles.input}
          placeholder="Ask about competitors..."
          placeholderTextColor="#475569"
          value={input}
          onChangeText={setInput}
          multiline
          maxLength={2000}
          returnKeyType="send"
          onSubmitEditing={() => sendMessage()}
          blurOnSubmit
          accessibilityLabel="Chat input"
        />
        <Pressable
          style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnOff]}
          onPress={() => sendMessage()}
          disabled={!input.trim() || loading}
          accessibilityLabel="Send message"
        >
          <Send size={18} color={!input.trim() || loading ? "#334155" : "#0F172A"} />
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#0F172A",
  },

  // Header
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
    gap: 10,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    flex: 1,
  },
  titleBlock: { flex: 1 },
  title: { fontSize: 17, fontWeight: "800", color: "#F1F5F9" },
  subtitle: { fontSize: 12, color: "#64748B", marginTop: 2 },

  // Local AI badge
  localBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 3,
  },
  localDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#22C55E",
  },
  localBadgeText: {
    fontSize: 11,
    color: "#22C55E",
    fontWeight: "700",
    letterSpacing: 0.4,
  },

  // New chat button
  newChatBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "#1E293B",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: "#334155",
  },
  newChatText: { fontSize: 12, color: "#64748B", fontWeight: "600" },

  // Messages area
  chatArea: { flex: 1 },
  chatContent: { paddingTop: 16, paddingBottom: 12 },

  // Suggested questions
  suggestionsBox: { paddingHorizontal: 16, marginTop: 8, marginBottom: 16 },
  suggestionsLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  suggestionsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    backgroundColor: "#1E293B",
    borderRadius: 99,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  chipText: { fontSize: 12, color: "#94A3B8", fontWeight: "500" },

  // Input bar
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#1E293B",
    backgroundColor: "#0F172A",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    color: "#F1F5F9",
    maxHeight: 100,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#22D3EE",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  sendBtnOff: {
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
  },
});
