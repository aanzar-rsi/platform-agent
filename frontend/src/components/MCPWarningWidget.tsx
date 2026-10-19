import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertCircle, Loader2 } from "lucide-react";

interface MCPWarningWidgetProps {
  onConnectAll: () => Promise<void>;
  onIgnore: () => void;
  isConnecting?: boolean;
}

export default function MCPWarningWidget({ onConnectAll, onIgnore, isConnecting }: MCPWarningWidgetProps) {
  return (
    <Card className="p-4 bg-yellow-500/10 border-yellow-500/50 border-2">
      <div className="flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-yellow-500 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-yellow-400 mb-1">No MCP Servers Connected</h3>
          <p className="text-xs text-neutral-400 mb-3">
            The agent doesn't have access to any MCP servers. Some features may be limited.
          </p>
          <div className="flex gap-2">
            <Button
              onClick={onConnectAll}
              disabled={isConnecting}
              size="sm"
              className="bg-yellow-500 hover:bg-yellow-600 text-black border-0 h-8 text-xs"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                  Connecting...
                </>
              ) : (
                "Connect All"
              )}
            </Button>
            <Button
              onClick={onIgnore}
              disabled={isConnecting}
              variant="outline"
              size="sm"
              className="border-neutral-600 text-neutral-300 hover:bg-neutral-800 h-8 text-xs"
            >
              Ignore
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
