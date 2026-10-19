import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Get name initials generator
export function getInitials(name: string): string {
  if (!name) return "";

  const parts = name.trim().split(/\s+/);

  if (parts.length === 1) {
    const value = parts[0].substring(0, 2);
    return value ? value.toUpperCase() : "";
  }

  const firstTwo = (parts[0][0] + parts[1][0]).toUpperCase().trim();
  return firstTwo || "";
}