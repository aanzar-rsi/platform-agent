export type ConnectionLog = { timestamp: string; level: string; message: string };

export function defaultMcpLoginUrl(serverUrl: string): string {
  try {
    const url = new URL(serverUrl);
    url.pathname = `${url.pathname.replace(/\/$/, '')}/auth/login`;
    url.search = '';
    url.hash = '';
    return url.toString().replace(/\/$/, '');
  } catch {
    return '';
  }
}

export function mcpErrorMessage(error: any): string {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const location = Array.isArray(item?.loc) ? item.loc.filter((part: unknown) => part !== 'body').join('.') : '';
      return `${location ? `${location}: ` : ''}${item?.msg || JSON.stringify(item)}`;
    }).join('; ');
  }
  if (typeof detail?.message === 'string') return detail.message;
  return error?.message || 'Unknown MCP connection error';
}

export function mcpErrorLogs(error: any): ConnectionLog[] {
  const logs = error?.response?.data?.detail?.logs;
  return Array.isArray(logs) && logs.length
    ? logs
    : [{ timestamp: new Date().toISOString(), level: 'ERROR', message: mcpErrorMessage(error) }];
}
