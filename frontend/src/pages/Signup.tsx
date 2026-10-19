import { Link } from "react-router";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#fff7bf_0%,#fffdee_45%,#f0f0f0_100%)] px-6 py-10">
      <div className="mx-auto flex min-h-[80vh] w-full max-w-3xl items-center justify-center">
        <div className="w-full rounded-3xl border border-black/20 bg-white/90 p-8 shadow-[0_26px_80px_rgba(0,0,0,0.15)] md:p-10">
          <div className="mb-5 inline-flex rounded-full border border-black/20 bg-[#fff9ce] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#4f3f00]">
            Mock page
          </div>
          <h1 className="text-3xl font-bold text-[#171717] md:text-4xl">Sign up is coming soon</h1>
          <p className="mt-3 text-[#2b2b2b]/80">
            This is a placeholder signup screen for now. We will connect full registration flow in a later step.
          </p>

          <div className="mt-7 rounded-2xl border border-black/10 bg-[#fffef6] p-5">
            <p className="mb-3 text-sm font-semibold text-[#171717]">Planned support</p>
            <ul className="space-y-2 text-sm text-[#2b2b2b]/80">
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#7b6500]" />Email sign-up</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#7b6500]" />SSO onboarding</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#7b6500]" />Organization invite flow</li>
            </ul>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild className="bg-[#171717] text-white hover:bg-[#2b2b2b]">
              <Link to="/login">Go to login</Link>
            </Button>
            <Button asChild variant="outline" className="border-black/25 bg-white text-[#171717] hover:bg-[#fff8d1]">
              <Link to="/login">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
