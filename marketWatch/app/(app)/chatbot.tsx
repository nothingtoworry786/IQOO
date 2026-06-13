import { useState, useRef, useEffect, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  TextInput,
  Pressable,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { MessageCircle, Send, Bot, User } from "lucide-react-native";
import { api } from "../../services/apiClient";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
}

// ─────────────────────────────────────────────────────────────────────────────
// Suggested Questions
// ─────────────────────────────────────────────────────────────────────────────

const SUGGESTED_QUESTIONS = [
  "What are the latest competitor funding rounds?",
  "What hiring signals should I watch for?",
  "Any pricing changes I should know about?",
  "Which competitors are expanding to new cities?",
];

// ─────────────────────────────────────────────────────────────────────────────
// Bubble Component
// ─────────────────────────────────────────────────────────────────────────────

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

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
          isUser ? bubble.userBubble : bubble.assistantBubble,
        ]}
      >
        <Text style={isUser ? bubble.userText : bubble.assistantText}>
          {message.text}
        </Text>
        <Text style={bubble.time}>
          {message.timestamp.toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
          })}
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
  userRow: {
    justifyContent: "flex-end",
  },
  assistantRow: {
    justifyContent: "flex-start",
  },
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
    maxWidth: "78%",
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
  userText: {
    fontSize: 14,
    color: "#E2E8F0",
    lineHeight: 20,
  },
  assistantText: {
    fontSize: 14,
    color: "#E2E8F0",
    lineHeight: 20,
  },
  time: {
    fontSize: 10,
    color: "#475569",
    marginTop: 6,
    textAlign: "right",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Main Chatbot Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function ChatbotScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text:
        "👋 Welcome to MarketWatch AI!\n\n" +
        "I can answer questions about your tracked competitors — funding, hiring, pricing, expansions, and more.\n\n" +
        "Try asking one of the suggested questions below or type your own!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  const sendMessage = useCallback(async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    if (!overrideText) setInput("");
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await api.chat.send(text);
      const assistantMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        text: response.reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        text: `⚠️ Error: ${err?.message ?? "Could not reach the AI backend. Is the server running?"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    setTimeout(() => {
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  return (
    <KeyboardAvoidingView
      style={screen.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      {/* Header */}
      <View style={screen.header}>
        <View style={screen.titleRow}>
          <MessageCircle size={20} color="#A78BFA" />
          <View>
            <Text style={screen.title}>MarketWatch AI</Text>
            <Text style={screen.subtitle}>
              Ask anything about your competitors
            </Text>
          </View>
        </View>
      </View>

      {/* Messages */}
      <ScrollView
        ref={scrollRef}
        style={screen.chatArea}
        contentContainerStyle={screen.chatContent}
        keyboardShouldPersistTaps="handled"
      >
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* Loading indicator */}
        {loading && (
          <View style={[bubble.row, bubble.assistantRow]}>
            <View style={bubble.avatarBot}>
              <Bot size={16} color="#A78BFA" />
            </View>
            <View style={[bubble.bubble, bubble.assistantBubble]}>
              <ActivityIndicator size="small" color="#A78BFA" />
            </View>
          </View>
        )}

        {/* Suggested questions (shown only at the start) */}
        {messages.length === 1 && (
          <View style={screen.suggestionsBox}>
            <Text style={screen.suggestionsLabel}>SUGGESTED QUESTIONS</Text>
            <View style={screen.suggestionsGrid}>
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <Pressable
                  key={i}
                  style={screen.suggestionChip}
                  onPress={() => sendMessage(q)}
                >
                  <Text style={screen.suggestionText}>{q}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Input bar */}
      <View style={screen.inputBar}>
        <TextInput
          style={screen.input}
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
          style={[
            screen.sendBtn,
            (!input.trim() || loading) && screen.sendBtnDisabled,
          ]}
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

const screen = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
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
  },
  title: {
    fontSize: 18,
    fontWeight: "800",
    color: "#F1F5F9",
  },
  subtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  chatArea: {
    flex: 1,
  },
  chatContent: {
    paddingTop: 16,
    paddingBottom: 8,
  },
  suggestionsBox: {
    paddingHorizontal: 16,
    marginTop: 8,
    marginBottom: 16,
  },
  suggestionsLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 1.2,
    marginBottom: 10,
    textTransform: "uppercase",
  },
  suggestionsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  suggestionChip: {
    backgroundColor: "#1E293B",
    borderRadius: 99,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  suggestionText: {
    fontSize: 12,
    color: "#94A3B8",
    fontWeight: "500",
  },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 10,
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
  sendBtnDisabled: {
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
  },
});
