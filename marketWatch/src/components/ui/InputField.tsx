import React, { useState, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Pressable,
  type TextInputProps,
  type StyleProp,
  type ViewStyle,
} from "react-native";

interface InputFieldProps extends TextInputProps {
  label: string;
  icon?: React.ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
  multiline?: boolean;
  isFocused?: boolean;
}

export default function InputField({
  label,
  icon,
  containerStyle,
  multiline = false,
  isFocused: isFocusedProp,
  ...props
}: InputFieldProps) {
  const [isFocusedLocal, setIsFocusedLocal] = useState(false);
  const isFocused = isFocusedProp !== undefined ? isFocusedProp : isFocusedLocal;
  const inputRef = useRef<TextInput>(null);

  const handlePress = () => {
    inputRef.current?.focus();
  };

  return (
    <View style={[styles.inputGroup, containerStyle]}>
      <Text style={styles.inputLabel}>{label}</Text>
      <Pressable
        onPress={handlePress}
        style={[
          styles.inputWrap, 
          multiline && styles.inputWrapMultiline,
          isFocused && styles.inputWrapFocused
        ]}
      >
        {icon && (
          <View style={[
            styles.iconContainer, 
            multiline && styles.iconContainerMultiline,
            { opacity: isFocused ? 1 : 0.5 }
          ]}>
            {icon}
          </View>
        )}
        <TextInput
          ref={inputRef}
          style={[styles.input, multiline && styles.inputMultiline]}
          multiline={multiline}
          placeholderTextColor="#475569"
          {...props}
          onFocus={(e) => {
            setIsFocusedLocal(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocusedLocal(false);
            props.onBlur?.(e);
          }}
        />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#94A3B8",
    marginLeft: 2,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  inputWrapFocused: {
    borderColor: "#22D3EE",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
  },
  inputWrapMultiline: {
    alignItems: "flex-start",
  },
  iconContainer: {
    marginLeft: 14,
    justifyContent: "center",
    alignItems: "center",
  },
  iconContainerMultiline: {
    marginTop: 15,
  },
  input: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 14,
    fontSize: 14,
    color: "#F1F5F9",
  },
  inputMultiline: {
    height: 100,
    textAlignVertical: "top",
  },
});

