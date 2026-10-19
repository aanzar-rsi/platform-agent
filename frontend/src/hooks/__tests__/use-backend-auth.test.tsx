import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

const loginMock = vi.fn();
const logoutMock = vi.fn();
const meMock = vi.fn();
const setAccessTokenMock = vi.fn();
const getAccessTokenMock = vi.fn();
const clearAuthStorageMock = vi.fn();

vi.mock("@/lib/api", () => ({
  authAPI: {
    login: (...args: any[]) => loginMock(...args),
    logout: (...args: any[]) => logoutMock(...args),
    me: (...args: any[]) => meMock(...args),
  },
  setAccessToken: (...args: any[]) => setAccessTokenMock(...args),
  getAccessToken: (...args: any[]) => getAccessTokenMock(...args),
  clearAuthStorage: (...args: any[]) => clearAuthStorageMock(...args),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

describe("useBackendAuth", () => {
  beforeEach(() => {
    localStorage.clear();
    loginMock.mockReset();
    logoutMock.mockReset();
    meMock.mockReset();
    setAccessTokenMock.mockReset();
    getAccessTokenMock.mockReset();
    clearAuthStorageMock.mockReset();
    getAccessTokenMock.mockReturnValue(null);
  });

  it("boots unauthenticated when no token", async () => {
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("restores a stored login after validating the token", async () => {
    getAccessTokenMock.mockReturnValue("jwt");
    meMock.mockResolvedValue({ uid: "u1", user_name: "jane_doe", name: "Jane" });
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
    expect(result.current.user?.uid).toBe("u1");
    expect(meMock).toHaveBeenCalledOnce();
    expect(clearAuthStorageMock).not.toHaveBeenCalled();
  });

  it("clears an expired stored login", async () => {
    getAccessTokenMock.mockReturnValue("expired");
    meMock.mockRejectedValue({ response: { status: 401 } });
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isAuthenticated).toBe(false);
    expect(clearAuthStorageMock).toHaveBeenCalledOnce();
  });

  it("signIn stores token and user", async () => {
    loginMock.mockResolvedValue({
      access_token: "jwt2",
      session_id: "sid",
      user: { uid: "u2", user_name: "jane_doe", name: "Jane" },
    });
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let out: { success: boolean; message: string } | undefined;
    await act(async () => {
      out = await result.current.signIn("jane_doe", "password123");
    });
    expect(out?.success).toBe(true);
    expect(setAccessTokenMock).toHaveBeenCalledWith("jwt2");
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.user_id).toBe("u2");
  });

  it("deduplicates concurrent signIn calls", async () => {
    let resolveLogin: (value: unknown) => void = () => {};
    loginMock.mockReturnValue(
      new Promise((resolve) => {
        resolveLogin = resolve;
      })
    );
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let first: Promise<{ success: boolean; message: string }> | undefined;
    let second: Promise<{ success: boolean; message: string }> | undefined;
    await act(async () => {
      first = result.current.signIn("jane_doe", "password123");
      second = result.current.signIn("jane_doe", "password123");
    });

    resolveLogin({
      access_token: "jwt3",
      session_id: "sid2",
      user: { uid: "u3", user_name: "jane_doe", name: "Jane" },
    });

    const [a, b] = await act(async () => Promise.all([first!, second!]));
    expect(a.success).toBe(true);
    expect(b.success).toBe(true);
    expect(loginMock).toHaveBeenCalledTimes(1);
  });

  it("rejects empty credentials and unsupported methods", async () => {
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      const empty = await result.current.signIn("", "");
      expect(empty.success).toBe(false);
      const anon = await result.current.signIn("anonymous");
      expect(anon.success).toBe(false);
    });
    expect(loginMock).not.toHaveBeenCalled();
  });

  it("signOut calls logout and clears storage", async () => {
    loginMock.mockResolvedValue({
      access_token: "jwt",
      session_id: "sid",
      user: { uid: "u1", name: "A" },
    });
    logoutMock.mockResolvedValue({ success: true });
    const { useBackendAuth } = await import("@/hooks/use-backend-auth");
    const { result } = renderHook(() => useBackendAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      await result.current.signIn("user", "password");
    });
    getAccessTokenMock.mockReturnValue("jwt");
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    await act(async () => {
      await result.current.signOut();
    });
    expect(logoutMock).toHaveBeenCalled();
    expect(clearAuthStorageMock).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
