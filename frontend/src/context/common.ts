// @/lib/common.ts (or @/constants/common.ts)

import type { LucideIcon } from "lucide-react";
import { Bot, Brain, Database, MessageSquare, Sparkles, Zap } from "lucide-react";

// ===========================
// Liquid Ether Configurations
// ===========================
export const LIQUID_ETHER_CONFIGS = {
  default: {
    colors: ['#010101', '#fbe232', '#ffffff'] as string[],
    mouseForce: 20,
    cursorSize: 100,
    resolution: 0.5,
    autoDemo: true,
    autoSpeed: 0.5,
    autoIntensity: 2.2,
  }
} as const;


// ===========================
// Feature Cards Data
// ===========================
export interface Feature {
    icon: LucideIcon;
    title: string;
    description: string;
}

export const FEATURES: readonly Feature[] = [
    {
        icon: MessageSquare,
        title: "Intelligent Chat",
        description: "Context-aware conversations",
    },
    {
        icon: Brain,
        title: "Long-Term Memory",
        description: "Learns from every interaction",
    },
    {
        icon: Zap,
        title: "MCP Tools",
        description: "Powerful tool integration",
    },
    {
        icon: Database,
        title: "Data Sources",
        description: "Connect multiple sources",
    },
    {
        icon: Bot,
        title: "Agentic Behavior",
        description: "Autonomous task execution",
    },
    {
        icon: Sparkles,
        title: "Adaptive Learning",
        description: "Evolves with your needs",
    },
] as const;


export type LiquidEtherConfig = typeof LIQUID_ETHER_CONFIGS[keyof typeof LIQUID_ETHER_CONFIGS];
