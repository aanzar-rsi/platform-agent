import * as React from "react"
import { cn } from "@/lib/utils"

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  description?: React.ReactNode
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, description, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border bg-background p-4 shadow-lg",
          className
        )}
        {...props}
      >
        <div className="text-sm font-semibold">{children}</div>
        {description && (
          <div className="mt-1 text-sm opacity-90">{description}</div>
        )}
      </div>
    )
  }
)
Toast.displayName = "Toast"

export { Toast }

