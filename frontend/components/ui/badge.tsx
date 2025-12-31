import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow-sm hover:bg-primary/90",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-red-100 text-red-700 hover:bg-red-200",
        outline:
          "border-gray-200 text-gray-700 bg-white hover:bg-gray-50",
        success:
          "border-transparent bg-green-100 text-green-700 hover:bg-green-200",
        warning:
          "border-transparent bg-yellow-100 text-yellow-700 hover:bg-yellow-200",
        info:
          "border-transparent bg-blue-100 text-blue-700 hover:bg-blue-200",
        purple:
          "border-transparent bg-purple-100 text-purple-700 hover:bg-purple-200",
        gradient:
          "border-transparent bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md",
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
