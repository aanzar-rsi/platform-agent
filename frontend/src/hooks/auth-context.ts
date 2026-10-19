import { createContext } from "react";
import type { useBackendAuth } from "./use-backend-auth";

export type AuthContextValue = ReturnType<typeof useBackendAuth>;

export const AuthContext = createContext<AuthContextValue | null>(null);
