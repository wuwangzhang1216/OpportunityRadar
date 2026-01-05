import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const cardVariants = cva(
  "rounded-2xl text-card-foreground transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-card border border-border",
        glass: "glass backdrop-blur-xl",
        elevated: "bg-card border border-border shadow-sm hover:shadow-md",
        outline: "bg-transparent border border-border hover:border-primary/50",
        glow: "bg-card border border-border hover:glow-sm",
        feature: "bg-secondary/50 border border-border",
        // AI-specific variants
        ai: "bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20 hover:border-primary/40 hover:shadow-md",
        aiGlow: "bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20 hover:glow-md ai-shimmer",
        aiSolid: "ai-gradient text-white border-transparent",
        // Urgency variants for deadline cards
        urgencySafe: "bg-card border-l-4 border-l-urgency-safe border-t border-r border-b border-border",
        urgencyWarning: "bg-urgency-warning/5 border-l-4 border-l-urgency-warning border-t border-r border-b border-border",
        urgencyUrgent: "bg-urgency-urgent/5 border-l-4 border-l-urgency-urgent border-t border-r border-b border-border",
        urgencyCritical: "bg-urgency-critical/5 border-l-4 border-l-urgency-critical border-t border-r border-b border-border animate-urgency-pulse",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, className }))}
      {...props}
    />
  )
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent, cardVariants };
