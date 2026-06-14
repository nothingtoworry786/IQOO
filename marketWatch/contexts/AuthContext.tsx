import React, {
  createContext,
  useContext,
  useCallback,
  type ReactNode,
} from 'react';
import { router } from 'expo-router';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: string | null;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const login = useCallback(async (_email: string, _password: string) => {
    router.replace('/(app)' as never);
  }, []);

  const signup = useCallback(async (_email: string, _password: string) => {
    router.replace('/(onboarding)' as never);
  }, []);

  const logout = useCallback(async () => {
    router.replace('/(app)' as never);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: true,
        isLoading: false,
        userId: 'local-user',
        userEmail: null,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
