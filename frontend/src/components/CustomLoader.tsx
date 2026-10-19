import { cn } from "@/lib/utils";

export default function CustomLoader({ className }: { className?: string }) {
  return (
    <span className={cn("custom-loader-frame", className)} aria-hidden>
      <span className="custom-loader" />
    </span>
  );
}
