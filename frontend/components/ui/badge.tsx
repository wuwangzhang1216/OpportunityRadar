import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-red-100 text-red-700",
        outline:
          "border-border text-foreground bg-background",
        success:
          "border-transparent bg-green-100 text-green-700",
        warning:
          "border-transparent bg-yellow-100 text-yellow-700",
        info:
          "border-transparent bg-sky-100 text-sky-700",
        purple:
          "border-transparent bg-purple-100 text-purple-700",
        // AI-specific variants
        ai: "border-primary/20 bg-gradient-to-r from-primary/10 to-purple-500/10 text-primary",
        aiSolid: "border-transparent ai-gradient text-white",
        // Urgency variants
        urgencySafe: "border-transparent bg-urgency-safe/10 text-urgency-safe",
        urgencyWarning: "border-transparent bg-urgency-warning/10 text-urgency-warning",
        urgencyUrgent: "border-transparent bg-urgency-urgent/10 text-urgency-urgent",
        urgencyCritical: "border-transparent bg-urgency-critical/10 text-urgency-critical",
      },
      size: {
        default: "px-2.5 py-0.5 text-xs",
        sm: "px-2 py-0.5 text-[10px]",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
}

function Badge({ className, variant, size, icon, children, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </div>
  );
}

export { Badge, badgeVariants };
