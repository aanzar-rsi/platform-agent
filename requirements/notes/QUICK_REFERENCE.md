# Quick Reference Guide

## 🎨 Color Theme

The app now features a vibrant color palette:
- **Primary (Blue)**: Main actions, links
- **Secondary (Purple)**: Accents, secondary actions
- **Success (Green)**: Confirmations, active states
- **Warning (Amber)**: Cautions, settings
- **Danger (Red)**: Destructive actions, errors

## 🗺️ Navigation Map

```
/ (Landing)
├── /dashboard (Overview with stats)
├── /mcp-config (MCP Server setup)
├── /knowledge-config (Prompts, Tools, Memory, Cache)
├── /playground (AI Tool Generator)
├── /settings (Agent configuration)
└── /auth (Login/Signup)
```

## 🚀 Quick Start

1. **Dashboard** → View stats & quick actions
2. **Start Chatting** → Enter enhanced chat interface
3. **Configure** → Click any quick action card

## 💬 Enhanced Chat Features

| Feature | Button | Description |
|---------|--------|-------------|
| Voice Input | 🎤 Mic | Record voice messages |
| Attachments | 📎 Paperclip | Attach files/images |
| Constraints | ⚙️ Settings | Max tokens, format, temp |
| Instructions | 📄 FileText | Per-message instructions |

## ⚙️ Agent Parameters (from main.py)

All configurable in `/settings`:

### Core
- `name`: Agent identifier
- `server_url`: MCP server endpoint
- `temperature`: 0-1 (creativity)
- `top_p`: 0-1 (nucleus sampling)
- `max_replans`: Replanning attempts

### Memory
- `short_term_memory_size`: Messages in context
- `short_term_memory_token_limit`: Before summarization

### Models
- `model_default`: Fallback model
- `model_agent`: Decision making
- `model_planning`: Plan generation
- `model_respond`: Response generation
- `model_summarize`: Summarization
- `model_evaluation`: Plan evaluation

### Options
- `enable_logging`: Enable logs
- `log_level`: DEBUG | INFO | WARNING | ERROR
- `enable_streaming`: Stream responses

## 🛠️ Internal Tools

Toggle in `/settings` → Internal Tools tab:
- `get_long_term_memory`
- `update_long_term_memory`
- `list_user_sessions`
- `get_chat_session`

## 🎯 Shortcuts

- **Dashboard stats** → Click card to navigate
- **Enter** → Send message
- **Shift + Enter** → New line in chat
- **Voice recording** → Auto-transcribes (mock)
- **Collapsible panels** → Click to expand/collapse

## 📝 Mock Mode

All features work without backend:
- ✅ All UI interactive
- ✅ Toast notifications
- ✅ Simulated actions
- ✅ Mock data displays

## 🎨 UI Components

Built with:
- Shadcn UI (buttons, cards, inputs)
- Framer Motion (animations)
- Tailwind CSS v4 (styling)
- Lucide React (icons)

## 🔥 Pro Tips

1. **Color coding**: Each section has its own color theme
2. **Stats refresh**: Dashboard shows live counts
3. **Tool generation**: Describe tools in natural language
4. **Constraints**: Override agent behavior per message
5. **Voice input**: Great for hands-free operation

---

**Everything is ready!** Just refresh your browser. 🚀

