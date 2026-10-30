// Real backend authentication (JWT / client2.0)
import { useState, useEffect, useCallback, useRef } from 'react';
import { authAPI, healthAPI, setAccessToken, getAccessToken, clearAuthStorage } from '@/lib/api';
import { User } from '@/types/backend';
import { toast } from 'sonner';

const USER_KEY = 'agent_user';
const AUTH_SESSION_KEY = 'agent_session_id';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  currentSessionId: string | null;
  backendAvailable: boolean;
  backendWarning: string | null;
}

type SignInResult = { success: boolean; message: string };

function toUser(u: {
  uid: string;
  user_name?: string;
  email?: string;
  name?: string;
  role?: string;
  created_at?: string;
  last_login?: string;
}): User {
  return {
    uid: u.uid,
    user_id: u.uid,
    user_name: u.user_name,
    name: u.name || u.user_name || 'User',
    email: u.email,
    role: u.role,
    created_at: u.created_at,
    last_login: u.last_login,
  };
}

function extractError(error: any): string {
  if (!error?.response) {
    return 'Backend unavailable. Start the API and check PostgreSQL connectivity.';
  }
  const data = error?.response?.data;
  if (!data) return error?.message || 'Request failed';
  if (typeof data === 'string') return data;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  if (data.message) return data.message;
  return 'Request failed';
}

export function useBackendAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    currentSessionId: null,
    backendAvailable: true,
    backendWarning: null,
  });
  const bootstrapRunRef = useRef(0);
  const signInFlightRef = useRef<Promise<SignInResult> | null>(null);

  useEffect(() => {
    let cancelled = false;
    healthAPI.live()
      .then((live) => {
        if (cancelled) return;
        const available = Boolean(live?.dependencies?.postgres);
        const warning = available ? null : 'PostgreSQL is unavailable; backend is running in degraded mode.';
        setState((prev) => ({ ...prev, backendAvailable: available, backendWarning: warning }));
      })
      .catch(() => {
        if (cancelled) return;
        setState((prev) => ({
          ...prev,
          backendAvailable: false,
          backendWarning: 'Backend is unreachable. Start backend service and verify dependencies.',
        }));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const run = ++bootstrapRunRef.current;
    const token = getAccessToken();
    if (!token) {
      setState((prev) => ({ ...prev, user: null, isLoading: false, isAuthenticated: false, currentSessionId: null }));
      return;
    }

    authAPI.me()
      .then((response) => {
        if (bootstrapRunRef.current !== run) return;
        const user = toUser(response);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        setState((prev) => ({
          ...prev,
          user,
          isLoading: false,
          isAuthenticated: true,
          currentSessionId: localStorage.getItem(AUTH_SESSION_KEY),
        }));
      })
      .catch((error: unknown) => {
        if (bootstrapRunRef.current !== run) return;
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 401 || status === 403) clearAuthStorage();
        setState((prev) => ({
          ...prev,
          user: null,
          isLoading: false,
          isAuthenticated: false,
          currentSessionId: null,
          backendAvailable: Boolean(status),
          backendWarning: status ? prev.backendWarning : 'Backend is unreachable. Start backend service and verify dependencies.',
        }));
      });
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      bootstrapRunRef.current += 1;
      setState((prev) => ({ ...prev, user: null, isLoading: false, isAuthenticated: false, currentSessionId: null }));
    };

    window.addEventListener('eva:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('eva:unauthorized', handleUnauthorized);
  }, []);

  const signIn = useCallback(
    async (
      userIdOrMethod?: string,
      passwordOrData?: string | FormData
    ): Promise<SignInResult> => {
      if (signInFlightRef.current) {
        return signInFlightRef.current;
      }

      const attempt = (async (): Promise<SignInResult> => {
        bootstrapRunRef.current += 1;

        try {
          if (userIdOrMethod === 'anonymous' || userIdOrMethod === 'email-otp') {
            toast.error('This sign-in method is not available');
            return { success: false, message: 'Method not available' };
          }

          const identifier = (userIdOrMethod || '').trim();
          const password = typeof passwordOrData === 'string' ? passwordOrData : '';

          if (!identifier || !password) {
            toast.error('Username and password required');
            return { success: false, message: 'Username and password required' };
          }

          const response = await authAPI.login({ identifier, password });
          setAccessToken(response.access_token);
          const user = toUser(response.user);
          localStorage.setItem(USER_KEY, JSON.stringify(user));
          if (response.session_id) {
            localStorage.setItem(AUTH_SESSION_KEY, response.session_id);
          }

          setState((prev) => ({
            ...prev,
            user,
            isLoading: false,
            isAuthenticated: true,
            currentSessionId: response.session_id || null,
            backendAvailable: true,
            backendWarning: null,
          }));

          toast.success('Signed in successfully');
          return { success: true, message: 'logged in' };
        } catch (error: any) {
          console.error('Sign in error:', error);
          const errorMessage = extractError(error);
          toast.error(errorMessage);
          setState((prev) => ({
            ...prev,
            backendAvailable: Boolean(error?.response),
            backendWarning: error?.response ? prev.backendWarning : 'Backend is unreachable. Start backend service and verify dependencies.',
          }));
          return { success: false, message: errorMessage };
        }
      })();

      signInFlightRef.current = attempt;
      try {
        return await attempt;
      } finally {
        if (signInFlightRef.current === attempt) {
          signInFlightRef.current = null;
        }
      }
    },
    []
  );

  const signOut = useCallback(async () => {
    bootstrapRunRef.current += 1;
    signInFlightRef.current = null;
    try {
      if (getAccessToken()) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error('Sign out error:', error);
    } finally {
      clearAuthStorage();
      setState((prev) => ({
        ...prev,
        user: null,
        isLoading: false,
        isAuthenticated: false,
        currentSessionId: null,
      }));
      toast.success('Signed out successfully');
    }
  }, []);

  const setCurrentSessionId = useCallback((sessionId: string | null) => {
    setState((prev) => ({ ...prev, currentSessionId: sessionId }));
    if (sessionId) localStorage.setItem(AUTH_SESSION_KEY, sessionId);
    else localStorage.removeItem(AUTH_SESSION_KEY);
  }, []);

  return {
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    currentSessionId: state.currentSessionId,
    backendAvailable: state.backendAvailable,
    backendWarning: state.backendWarning,
    signIn,
    signOut,
    setCurrentSessionId,
  };
}
