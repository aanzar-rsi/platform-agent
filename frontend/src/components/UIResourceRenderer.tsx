/**
 * UIResourceRenderer Component
 * 
 * Renders MCP UI Resources using the @mcp-ui/client library.
 * Supports rendering HTML content and external URLs in sandboxed iframes.
 * 
 * Based on MCP-UI specification: https://mcpui.dev/guide/introduction
 */

import { UIResourceRenderer as MCPUIRenderer } from '@mcp-ui/client';
import { useCallback, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, ExternalLink, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface UIResource {
  uri: string;
  mimeType: 'text/html' | 'text/uri-list' | 'application/vnd.mcp-ui.remote-dom';
  text?: string;
  blob?: string;
}

export interface UIResourceRendererProps {
  resource: UIResource;
  className?: string;
  maxHeight?: string;
  onAction?: (action: any) => void;
}

export default function UIResourceRenderer({ 
  resource, 
  className = '',
  maxHeight = '600px',
  onAction 
}: UIResourceRendererProps) {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const handleUIAction = useCallback((actionResult: any) => {
    console.log('UI Action received:', actionResult);
    if (onAction) {
      onAction(actionResult);
    }
    return { status: 'handled' };
  }, [onAction]);

  const handleLoad = useCallback(() => {
    setIsLoading(false);
  }, []);

  const handleError = useCallback((err: any) => {
    console.error('UI Resource rendering error:', err);
    setError(err.message || 'Failed to render UI resource');
    setIsLoading(false);
  }, []);

  // For URL resources, provide option to open in new tab
  const isUrlResource = resource.mimeType === 'text/uri-list';
  const resourceUrl = isUrlResource ? (resource.text || resource.blob) : null;

  if (error) {
    return (
      <Alert className="bg-red-900/20 border-red-600/50">
        <AlertCircle className="h-4 w-4 text-red-500" />
        <AlertDescription className="text-red-300">
          <p className="font-medium mb-1">Failed to render UI resource</p>
          <p className="text-sm">{error}</p>
          {resourceUrl && (
            <Button
              variant="outline"
              size="sm"
              className="mt-2 border-red-600/50 text-red-300 hover:bg-red-900/30"
              onClick={() => window.open(resourceUrl, '_blank')}
            >
              <ExternalLink className="h-3 w-3 mr-2" />
              Open in new tab
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card 
      className={`relative overflow-hidden bg-neutral-800/50 border-neutral-700 ${className}`}
      style={{ maxHeight }}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900/50 backdrop-blur-sm z-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
        </div>
      )}
      
      {resourceUrl && (
        <div className="absolute top-2 right-2 z-20">
          <Button
            variant="outline"
            size="sm"
            className="bg-neutral-800/90 border-neutral-700 text-neutral-300 hover:bg-neutral-700"
            onClick={() => window.open(resourceUrl, '_blank')}
          >
            <ExternalLink className="h-3 w-3 mr-2" />
            Open
          </Button>
        </div>
      )}

      <div className="w-full h-full min-h-50">
        <MCPUIRenderer
          resource={resource}
          onUIAction={handleUIAction}
          onLoad={handleLoad}
          onError={handleError}
        />
      </div>
    </Card>
  );
}

/**
 * Multiple UIResource Renderer
 * Renders multiple UI resources in a grid or stacked layout
 */
export interface MultiUIResourceRendererProps {
  resources: UIResource[];
  layout?: 'grid' | 'stack';
  className?: string;
  onAction?: (action: any) => void;
}

export function MultiUIResourceRenderer({ 
  resources, 
  layout = 'stack',
  className = '',
  onAction 
}: MultiUIResourceRendererProps) {
  if (!resources || resources.length === 0) {
    return null;
  }

  const layoutClass = layout === 'grid' 
    ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
    : 'space-y-4';

  return (
    <div className={`${layoutClass} ${className}`}>
      {resources.map((resource, index) => (
        <UIResourceRenderer
          key={resource.uri || `resource-${index}`}
          resource={resource}
          onAction={onAction}
        />
      ))}
    </div>
  );
}

