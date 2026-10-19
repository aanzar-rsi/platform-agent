# PlatformAgent Frontend - Setup & Development Guide

A modern React application for PlatformAgent (AI Assistant) with mock mode for development.

---

## Quick Start

```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Open browser
http://localhost:5173
```

That's it! The app runs in **mock mode** - no backend needed.

---

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── ui/            # Shadcn UI components
│   │   ├── ChatInterface.tsx
│   │   ├── ChatSidebar.tsx
│   │   ├── ChatView.tsx
│   │   ├── InfoPanel.tsx
│   │   ├── LiquidEther.tsx
│   │   └── LogoDropdown.tsx
│   ├── pages/             # Page components
│   │   ├── Landing.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Auth.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   ├── hooks/             # Custom React hooks
│   │   ├── use-auth.ts
│   │   ├── use-mock-auth.ts
│   │   └── use-mobile.ts
│   ├── lib/               # Utilities and mock data
│   │   ├── utils.ts
│   │   └── mockData.ts
│   ├── config/            # Configuration
│   │   └── env.ts
│   ├── types/             # TypeScript types
│   │   └── global.d.ts
│   ├── main.tsx           # App entry point
│   └── index.css          # Global styles
├── public/                # Static assets
├── package.json           # Dependencies
├── vite.config.ts         # Vite configuration
├── tsconfig.*.json        # TypeScript configs
└── README.md              # This file
```

---

## Tech Stack

### Core
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **React Router v7** - Routing

### Styling
- **Tailwind CSS v4** - Utility-first CSS
- **Shadcn UI** - Component library
- **Lucide React** - Icons
- **Framer Motion** - Animations

### State & Data
- **Mock Mode** - No backend required for development
- **React Hook Form** - Form management
- **Zod** - Schema validation

---

## Available Scripts

```bash
# Development
pnpm dev              # Start dev server (port 5173)

# Build
pnpm build            # Build for production

# Preview
pnpm preview          # Preview production build

# Code Quality
pnpm lint             # Run ESLint
pnpm format           # Format with Prettier
```

---

## Mock Mode Features

The app currently runs in **mock mode** with:

✅ **Mock Authentication**
- Auto-login as test user
- No real backend needed
- Perfect for development

✅ **Mock Data**
- Sample chat sessions
- Example messages
- User memory samples
- All in `src/lib/mockData.ts`

✅ **Full UI Working**
- Landing page with animations
- Dashboard with chat interface
- Settings page
- All navigation functional

---

## Key Components

### Authentication
- **`use-auth.ts`** - Main auth hook
- **`use-mock-auth.ts`** - Mock authentication
- Auto-login in dev mode

### Chat Interface
- **`ChatInterface.tsx`** - Main chat container
- **`ChatSidebar.tsx`** - Session list & creation
- **`ChatView.tsx`** - Message display & input
- **`InfoPanel.tsx`** - Tools, prompts, memory

### Pages
- **`Landing.tsx`** - Landing page with animation
- **`Dashboard.tsx`** - Main chat interface
- **`Settings.tsx`** - User settings & memory
- **`Auth.tsx`** - Login/signup (mock)

---

## Environment Configuration

The app reads from `VITE_MODE` environment variable:

```bash
# Mock mode (default, no backend)
VITE_MODE=mock
```

Create a `.env` file in the `frontend/` directory:

```env
VITE_MODE=mock
```

---

## Adding Real Backend

To integrate a real backend (AWS, Convex, custom API):

### Option 1: AWS
1. Install AWS SDKs (already in package.json but not used)
2. Implement `use-aws-auth.ts` hook
3. Create AWS service files
4. Update `use-auth.ts` to switch based on env

### Option 2: Convex
1. Run `npx convex dev`
2. Uncomment Convex providers in `main.tsx`
3. Use `useQuery`, `useMutation` from Convex
4. Replace mock data with real queries

### Option 3: Custom API
1. Create API service in `src/services/`
2. Replace mock functions with API calls
3. Add axios/fetch calls
4. Handle authentication tokens

---

## Common Tasks

### Add a New Page

1. Create file in `src/pages/NewPage.tsx`
2. Add route in `src/main.tsx`:
```tsx
<Route path="/new" element={<NewPage />} />
```

### Add a New Component

1. Create in `src/components/MyComponent.tsx`
2. Import and use:
```tsx
import MyComponent from '@/components/MyComponent';
```

### Modify Mock Data

Edit `src/lib/mockData.ts`:
```tsx
export const mockSessions = [ /* your data */ ];
export const mockMessages = [ /* your data */ ];
export const mockMemory = [ /* your data */ ];
```

### Add Shadcn UI Component

```bash
npx shadcn@latest add [component-name]
```

Example:
```bash
npx shadcn@latest add toast
```

---

## Troubleshooting

### Port Already in Use
```bash
# Change port in vite.config.ts
server: { port: 5174 }
```

### Dependencies Issues
```bash
# Clean install
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### TypeScript Errors
```bash
# Rebuild TypeScript
rm -rf tsconfig.*.tsbuildinfo
pnpm build
```

### Blank Page
1. Check browser console (F12)
2. Look for import errors
3. Verify all files in `src/` exist
4. Hard refresh: Ctrl + Shift + R

---

## Development Tips

1. **Hot Reload** - Vite provides instant HMR
2. **TypeScript** - Use types for better DX
3. **Components** - Keep components small & focused
4. **Tailwind** - Use utility classes for styling
5. **Mock Data** - Update `mockData.ts` for testing

---

## Production Build

```bash
# Build
pnpm build

# Output directory
dist/

# Serve locally
pnpm preview
```

Deploy `dist/` folder to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting

---

## Next Steps

1. ✅ App is running in mock mode
2. 🔄 Add real backend (AWS/Convex/Custom)
3. 🔄 Implement real authentication
4. 🔄 Connect to backend API
5. 🔄 Deploy to production

---

## Support

For issues or questions:
1. Check browser console (F12)
2. Review this guide
3. Check `package.json` for dependencies
4. Verify all imports are correct

---

## Summary

✅ **React 19** + **TypeScript** + **Vite**  
✅ **Tailwind v4** + **Shadcn UI**  
✅ **Mock Mode** - No backend needed  
✅ **Fully Functional** - All UI working  
✅ **Ready to Extend** - Add backend when needed  

**Happy coding! 🚀**

