import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { Shield, Sparkles } from "lucide-react-native";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface AnimatedSplashScreenProps {
  onFinish: () => void;
}

const BOOT_LOGS = [
  "INITIALISING STRATEGY AGENTS...",
  "CONNECTING MARKET DATABASE...",
  "SCANNING GROWTH POTENTIALS...",
  "LAUNCHING STRATEGY COMMAND...",
];

export default function AnimatedSplashScreen({ onFinish }: AnimatedSplashScreenProps) {
  const [logText, setLogText] = useState(BOOT_LOGS[0]);
  
  // Animation values
  const logoScale = useRef(new Animated.Value(0.3)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  
  const pulseScale = useRef(new Animated.Value(1)).current;
  const pulseOpacity = useRef(new Animated.Value(0.4)).current;
  
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const titleTranslateY = useRef(new Animated.Value(15)).current;
  
  const subtitleOpacity = useRef(new Animated.Value(0)).current;
  const subtitleTranslateY = useRef(new Animated.Value(10)).current;
  
  const logOpacity = useRef(new Animated.Value(0)).current;
  
  const progressWidth = useRef(new Animated.Value(0)).current;
  
  const screenFade = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // 1. Logo entry (Spring Scale + Fade)
    Animated.parallel([
      Animated.spring(logoScale, {
        toValue: 1,
        tension: 40,
        friction: 6,
        useNativeDriver: true,
      }),
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // 2. Continuous Pulse loop
    Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(pulseScale, {
            toValue: 1.8,
            duration: 1800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseOpacity, {
            toValue: 0,
            duration: 1800,
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(pulseScale, {
            toValue: 1,
            duration: 0,
            useNativeDriver: true,
          }),
          Animated.timing(pulseOpacity, {
            toValue: 0.4,
            duration: 0,
            useNativeDriver: true,
          }),
        ]),
      ])
    ).start();

    // 3. Title Entry (delayed by 400ms)
    Animated.sequence([
      Animated.delay(400),
      Animated.parallel([
        Animated.timing(titleOpacity, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(titleTranslateY, {
          toValue: 0,
          duration: 600,
          useNativeDriver: true,
        }),
      ]),
    ]).start();

    // 4. Subtitle Entry (delayed by 800ms)
    Animated.sequence([
      Animated.delay(800),
      Animated.parallel([
        Animated.timing(subtitleOpacity, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(subtitleTranslateY, {
          toValue: 0,
          duration: 600,
          useNativeDriver: true,
        }),
      ]),
    ]).start();

    // 5. Terminal Logs and Progress Bar
    Animated.sequence([
      Animated.delay(1000),
      Animated.timing(logOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start();

    // Fill Progress Bar over 3 seconds
    Animated.timing(progressWidth, {
      toValue: 1,
      duration: 3000,
      useNativeDriver: false, // width requires layout driver
    }).start();

    // Cycle through boot logs
    const logInterval = setInterval(() => {
      setLogText((prev) => {
        const idx = BOOT_LOGS.indexOf(prev);
        if (idx < BOOT_LOGS.length - 1) {
          return BOOT_LOGS[idx + 1];
        }
        return prev;
      });
    }, 700);

    // 6. Complete and Fade Screen Out
    const exitTimeout = setTimeout(() => {
      Animated.timing(screenFade, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }).start(() => {
        onFinish();
      });
    }, 3200);

    return () => {
      clearInterval(logInterval);
      clearTimeout(exitTimeout);
    };
  }, []);

  const progressPercent = progressWidth.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  return (
    <Animated.View style={[styles.container, { opacity: screenFade }]}>
      <StatusBar style="light" />

      {/* Decorative Cybernetic Background Lines */}
      <View style={styles.gridOverlay} />

      <View style={styles.contentWrap}>
        {/* Animated Logo Container */}
        <View style={styles.logoOuter}>
          {/* Looping pulse circle */}
          <Animated.View
            style={[
              styles.pulseCircle,
              {
                transform: [{ scale: pulseScale }],
                opacity: pulseOpacity,
              },
            ]}
          />
          {/* Main Logo Sphere */}
          <Animated.View
            style={[
              styles.logoInner,
              {
                transform: [{ scale: logoScale }],
                opacity: logoOpacity,
              },
            ]}
          >
            <Shield size={32} color="#22D3EE" />
            <View style={styles.sparkleDot}>
              <Sparkles size={12} color="#22D3EE" />
            </View>
          </Animated.View>
        </View>

        {/* Brand Text */}
        <View style={styles.brandContainer}>
          <Animated.Text
            style={[
              styles.title,
              {
                opacity: titleOpacity,
                transform: [{ translateY: titleTranslateY }],
              },
            ]}
          >
            MarketWatch
          </Animated.Text>
          <Animated.Text
            style={[
              styles.subtitle,
              {
                opacity: subtitleOpacity,
                transform: [{ translateY: subtitleTranslateY }],
              },
            ]}
          >
            AI COMPETITIVE WAR ROOM
          </Animated.Text>
        </View>
      </View>

      {/* Boot Logs & Progress at the bottom */}
      <Animated.View style={[styles.footer, { opacity: logOpacity }]}>
        <Text style={styles.logText}>{logText}</Text>
        <View style={styles.progressTrack}>
          <Animated.View style={[styles.progressFill, { width: progressPercent }]} />
        </View>
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#0B1121",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 60,
    zIndex: 9999,
  },
  gridOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    opacity: 0.05,
    borderWidth: 1,
    borderColor: "#22D3EE",
    margin: 20,
    borderRadius: 20,
  },
  contentWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 32,
  },
  logoOuter: {
    width: 120,
    height: 120,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  logoInner: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#22D3EE",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 15,
    elevation: 10,
    position: "relative",
  },
  pulseCircle: {
    position: "absolute",
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 2,
    borderColor: "#22D3EE",
  },
  sparkleDot: {
    position: "absolute",
    top: -4,
    right: -4,
    backgroundColor: "#062E16",
    borderColor: "#22D3EE",
    borderWidth: 1,
    borderRadius: 6,
    padding: 2,
  },
  brandContainer: {
    alignItems: "center",
    gap: 8,
  },
  title: {
    fontSize: 34,
    fontWeight: "900",
    color: "#F8FAFC",
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: 11,
    fontWeight: "700",
    color: "#22D3EE",
    letterSpacing: 2.5,
    textTransform: "uppercase",
  },
  footer: {
    width: SCREEN_WIDTH - 64,
    alignItems: "center",
    gap: 12,
  },
  logText: {
    fontSize: 10,
    fontFamily: "Courier New",
    fontWeight: "600",
    color: "#64748B",
    letterSpacing: 1.5,
    textAlign: "center",
  },
  progressTrack: {
    width: "100%",
    height: 3,
    backgroundColor: "#1E293B",
    borderRadius: 2,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#22D3EE",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
});
