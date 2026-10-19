import { useState, useEffect, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { Eye, EyeOff, Github, Loader2, ShieldCheck, KeyRound } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import LiquidEther from "@/components/LiquidEther";

function SsoButton({
  label,
  onClick,
  disabled,
}: {
  label: string;
  onClick: () => void;
  disabled: boolean;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      disabled={disabled}
      className="h-11 justify-start border-[#171717]/20 bg-white/90 text-[#171717] hover:bg-[#fff8c6] hover:border-[#171717]/40"
    >
      {label === "GitHub" ? <Github className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
      <span>{label}</span>
    </Button>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, isAuthenticated, isLoading: authBooting } = useAuth();

  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = (location.state as { from?: string })?.from || "/";
  const formLoading = authBooting || isSubmitting;

  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectTo]);

  const handleLogin = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (formLoading) return;

      if (!userId.trim()) {
        toast.error("Please enter a user ID");
        return;
      }

      setIsSubmitting(true);
      try {
        const result = await signIn(userId.trim(), password);
        if (!result.success) return;
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : "Login failed";
        toast.error(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [formLoading, password, signIn, userId],
  );

  const handleSso = useCallback((provider: string) => {
    toast.info(`${provider} SSO is a mock flow for now.`);
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_20%_20%,#fff8c6_0%,#fffdf0_35%,#f2f2f2_70%,#e7e7e7_100%)]">
      <div className="pointer-events-none fixed inset-0 opacity-35">
        <LiquidEther
          colors={["#fbe232", "#171717", "#f8f8f6"]}
          mouseForce={6}
          cursorSize={90}
          resolution={0.45}
          autoDemo={true}
          autoSpeed={0.25}
          autoIntensity={0.3}
          className="h-full w-full"
        />
      </div>

      <div className="relative z-10 mx-auto grid min-h-screen w-full max-w-7xl grid-cols-1 gap-8 px-6 py-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:px-10">
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="relative overflow-hidden rounded-3xl border border-black/10 bg-gradient-to-br from-[#fffde8] via-[#fff9ce] to-[#f3f3f3] p-8 shadow-[0_24px_80px_rgba(0,0,0,0.12)] lg:p-12"
        >
          <div className="pointer-events-none absolute -top-20 -left-20 h-72 w-72 rounded-full bg-[#fbe232]/20 blur-3xl" />
          <div className="relative mb-8 max-w-fit">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#fbe232]/20 via-white/5 to-transparent blur-md" />
            <div className="relative inline-flex items-center gap-3 py-2 pr-6">
              <img src="/rs_stacked.svg" alt="Rimini Street" width={56} height={40} className="h-10 w-14 rounded-md bg-black p-1.5 shadow-md" />
              <div>
                <p className="text-sm font-semibold tracking-wide text-[#171717]/80">Rimini Street</p>
                <p className="text-base font-bold text-[#171717]">Your AI workspace</p>
              </div>
            </div>
          </div>
          <h1 className="text-4xl font-bold leading-tight text-[#171717] lg:text-6xl">
            Work faster.
            <span className="block text-[#7b6500]">Fast, focused, and secure.</span>
          </h1>
          <p className="mt-5 max-w-xl text-base text-[#2b2b2b]/80 lg:text-lg">
            Organize chats, memory, and tools in one place. Sign in to continue from where you left off.
          </p>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
          className="order-first rounded-3xl border border-black/20 bg-[linear-gradient(165deg,#fffef5_0%,#ffffff_35%,#fff8d1_100%)] p-6 shadow-[0_28px_90px_rgba(0,0,0,0.18)] backdrop-blur md:order-last md:p-8"
        >
          <div className="mb-8 text-center">
            <h2 className="mt-1 text-3xl font-bold text-[#171717]">Welcome Back</h2>
            <p className="mt-1 text-sm text-[#2b2b2b]/70">Sign in to access your AI assistant</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="userId" className="text-[#171717]">Username or Email</Label>
              <Input
                id="userId"
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                disabled={formLoading}
                autoComplete="username"
                className="h-12 border-black/20 bg-white/90 text-[#171717] focus-visible:ring-[#fbe232]"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-[#171717]">Password</Label>
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-[#5f4d00] hover:text-[#171717]"
                >
                  {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  {showPassword ? "Hide" : "View"} password
                </button>
              </div>

              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={formLoading}
                autoComplete="current-password"
                className="h-12 border-black/20 bg-white/90 text-[#171717] focus-visible:ring-[#fbe232]"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-black/10 bg-[#fffdf1] px-3 py-2">
              <label htmlFor="remember" className="inline-flex items-center gap-2 text-sm text-[#171717]/80">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(v) => setRememberMe(v === true)}
                  className="border-black/25 bg-white data-[state=checked]:bg-[#fbe232] data-[state=checked]:text-[#171717]"
                />
                Remember me
              </label>
              <button
                type="button"
                onClick={() => toast.info("Password reset is a mock flow for now.")}
                className="text-xs font-semibold text-[#5f4d00] hover:text-[#171717]"
              >
                Forgot password?
              </button>
            </div>

            <Button
              type="submit"
              disabled={formLoading}
              className="h-12 w-full rounded-xl bg-[#171717] text-white transition hover:bg-[#2d2d2d]"
            >
              {formLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>

            <div className="flex items-center gap-3 text-xs text-black/50">
              <span className="h-px flex-1 bg-black/15" />
              Or continue with
              <span className="h-px flex-1 bg-black/15" />
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <SsoButton label="Google" onClick={() => handleSso("Google")} disabled={formLoading} />
              <SsoButton label="Microsoft" onClick={() => handleSso("Microsoft")} disabled={formLoading} />
              <SsoButton label="GitHub" onClick={() => handleSso("GitHub")} disabled={formLoading} />
            </div>

            <div className="pt-2 text-center text-sm text-black/70">
              New here?{" "}
              <Link to="/signup" className="font-semibold text-[#5f4d00] underline-offset-4 hover:underline">
                Create an account
              </Link>
            </div>

            <div className="rounded-xl border border-black/10 bg-[#fffdf1] p-3">
              <button
                type="button"
                onClick={() => toast.info("Magic link is a mock flow for now.")}
                className="inline-flex w-full items-center justify-center gap-2 text-sm font-semibold text-[#171717] hover:text-[#5f4d00]"
              >
                <KeyRound className="h-4 w-4" />
                Sign in with magic link
              </button>
            </div>
          </form>
        </motion.section>
      </div>
    </div>
  );
}
