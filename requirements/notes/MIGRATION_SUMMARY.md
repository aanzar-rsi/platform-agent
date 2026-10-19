# Frontend Migration Summary

## Overview
Updated frontend to work with the new client architecture that uses chat-based terminology and enhanced WebSocket streaming.

## Key Changes

### 1. WebSocket Protocol Updates (`src/lib/websocket.ts`)

#### Message Type Changes
- **Renamed**: `session.open` → `chat.open`
- **Renamed**: `session.updated` → `chat.updated`  
- **Added**: `agent.user_input_required` - for execution-time user input requests
- **Added**: `client.user_input` - for sending user input during execution

#### Connection Changes
- **Changed**: WebSocket URL from `/ws/{session_id}` to `/ws/{chat_id}?user_id={user_id}`
- **Updated**: Constructor to accept `chatId` and `userId` parameters
- **Updated**: All message envelopes use `chat_id` instead of `session_id`

#### New Methods
- `sendUserInput(input: string)` - Send user input during execution pause

#### Enhanced Handlers
- `onUserInputRequired` - Handle execution-time input requests
- `onChatOpen` - Handle chat connection events
- `onChatUpdated` - Handle chat metadata updates

### 2. API Endpoints (`src/lib/api.ts`)

#### Terminology Migration
- **Renamed**: `sessionAPI` → `chatAPI` (with backward compatibility alias)
- **Renamed**: `SessionCreateRequest` → `ChatCreateRequest`
- **Renamed**: `SessionSelectRequest` → `ChatSelectRequest`
- **Renamed**: `SessionInfo` → `ChatInfo`

#### New Endpoints
- `chatAPI.create()` - Create new chat (was `/sessions/create`, now `/chats/create`)
- `chatAPI.list()` - List user chats (was `/sessions/list`, now `/chats/list`)
- `chatAPI.load()` - Load chat (was `/sessions/load`, now `/chats/load`)
- `chatAPI.get(user_id, chat_id)` - Get chat with messages (new endpoint `/chats/get`)

### 3. Type Definitions (`src/types/backend.ts`)

#### New Types
- `Chat` interface (replaces `Session` with backward compatibility)
- `Session` type alias pointing to `Chat`

#### Updated Message Interface
- Added `chat_id` field (primary)
- Kept `session_id` field (backward compatibility)
- Added support for `execution_results` in metadata

### 4. EnhancedChatView Component (`src/components/EnhancedChatView.tsx`)

#### New Features
- **User Input Handling**: Added UI for `agent.user_input_required` messages
- **Execution Results**: Enhanced handling of `execution_results` in stream.done payload
- **Error Display**: Better error handling with payload.error support

#### State Management
- Added `userInputRequired` state for execution-time input prompts
- Added `userInputValue` state for user input field
- Enhanced `handleUserInputSubmit()` function

#### WebSocket Integration
- Updated connection to pass `userId` parameter
- Added `onUserInputRequired` handler
- Updated `onChatOpen` handler (was `onSessionOpen`)
- Enhanced `onStreamDone` to handle execution_results

#### API Migration
- Changed from `sessionAPI` to `chatAPI`
- Updated all message objects to use `chat_id`
- Updated chat history loading to use new `/chats/get` endpoint

### 5. ChatSidebar Component (`src/components/ChatSidebar.tsx`)

#### Terminology Changes
- Renamed `sessions` → `chats`
- Renamed `loadSessions()` → `loadChats()`
- Renamed `handleDeleteSession()` → `handleDeleteChat()`

#### API Updates
- Changed from `sessionAPI` to `chatAPI`
- Updated to handle both `chat_id` and `session_id` (backward compatibility)
- Updated chat creation to use `chat_name` parameter

## WebSocket Message Flow

### Query Execution Flow
```
Client → Server: client.query
Server → Client: chat.open (on connection)
Server → Client: agent.exec.start
Server → Client: agent.event (decision, planning, executing, etc.)
Server → Client: agent.event.plan (plan streaming)
Server → Client: agent.event.subroutine (step execution updates)
Server → Client: agent.stream.token (response streaming)
Server → Client: agent.stream.done (final result with execution_results)
```

### User Input Flow (New)
```
Server → Client: agent.user_input_required
  - Execution pauses, waiting for input
  - Client displays input prompt
Client → Server: client.user_input
  - User provides input
  - Execution continues
Server → Client: agent.event (user_input_received)
Server → Client: ... (execution continues)
```

## Backward Compatibility

### Maintained Compatibility
- `Session` type alias for `Chat`
- `sessionAPI` alias for `chatAPI`
- Support for both `session_id` and `chat_id` in message objects
- Support for legacy endpoint responses

### Breaking Changes
- WebSocket URL requires `chat_id` instead of `session_id`
- New message envelope structure with `chat_id`
- `/sessions/*` endpoints replaced with `/chats/*`

## Testing Checklist

- [x] WebSocket connection with chat_id
- [ ] User authentication and chat creation
- [ ] Message sending and receiving
- [ ] Plan streaming display
- [ ] Step execution updates
- [ ] User input requests during execution
- [ ] Error handling and display
- [ ] Chat history loading
- [ ] Chat list refresh
- [ ] Execution results display

## Notes

- All changes maintain backward compatibility where possible
- The frontend now properly handles the full execution lifecycle
- User input during execution is now fully supported
- Enhanced error handling and display
- Execution results are properly captured and displayed

