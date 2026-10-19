// Mock data for development and testing

export const mockUser = {
  user_id: "ahad.anzar",
  name: "Ahad Anzar",
  email: "ahad.anzar@chryselys.com"
};

export const mockSessions = [
  {
    _id: "mock-session-1",
    userId: "ahad.anzar",
    title: "Welcome to PlatformAgent",
    _creationTime: Date.now() - 86400000, // 1 day ago
    lastMessageAt: Date.now() - 3600000, // 1 hour ago
    messageCount: 15
  },
  {
    _id: "mock-session-2",
    userId: "ahad.anzar",
    title: "MCP Server Configuration",
    _creationTime: Date.now() - 172800000, // 2 days ago
    lastMessageAt: Date.now() - 7200000, // 2 hours ago
    messageCount: 8
  },
  {
    _id: "mock-session-3",
    userId: "ahad.anzar",
    title: "Getting Started Guide",
    _creationTime: Date.now() - 259200000, // 3 days ago
    lastMessageAt: Date.now() - 21600000, // 6 hours ago
    messageCount: 12
  }
];

export const mockMemory = [
  {
    key: "name",
    value: "Ahad Anzar",
    category: "user_data"
  },
  {
    key: "email",
    value: "ahad.anzar@chryselys.com",
    category: "user_data"
  },
  {
    key: "location",
    value: "Bangalore, India",
    category: "user_data"
  },
  {
    key: "preferred_language",
    value: "English",
    category: "user_preferences"
  },
  {
    key: "timezone",
    value: "IST (UTC+5:30)",
    category: "user_preferences"
  }
];

export const mockMessages = [
  {
    id: "msg-1",
    type: "human",
    content: "Hello! Can you help me understand how to configure MCP servers?",
    timestamp: Date.now() - 3600000
  },
  {
    id: "msg-2",
    type: "ai",
    content: "Of course! I'd be happy to help you configure MCP servers. The Model Context Protocol (MCP) allows the agent to connect to external services and tools.\n\nHere's a quick overview:\n\n1. **Add a Server**: Open MCP Config in the chat workspace and add a server\n2. **Configure**: Provide the server URL (e.g., http://localhost:8000) or stdio command\n3. **Connect**: The server will auto-connect on startup if enabled\n4. **Use Tools**: Once connected, you can access server tools in your conversations\n\nWould you like me to walk you through setting up a specific server?",
    timestamp: Date.now() - 3540000
  }
];
