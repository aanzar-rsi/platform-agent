import type { ReactNode } from "react";
import { AuthContext } from "./auth-context";
import { useBackendAuth } from "./use-backend-auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useBackendAuth();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}
