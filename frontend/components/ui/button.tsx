import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg active:scale-[0.98]",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-md hover:shadow-lg active:scale-[0.98]",
        outline:
          "border-2 border-input bg-background hover:bg-accent hover:text-accent-foreground hover:border-accent",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        gradient:
          "bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-lg hover:shadow-xl hover:opacity-90 active:scale-[0.98]",
        glow: "bg-primary text-primary-foreground shadow-md hover:shadow-lg hover:glow-md active:scale-[0.98]",
        glass:
          "glass text-gray-800 hover:bg-white/80 backdrop-blur-xl shadow-lg",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 rounded-lg px-4 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
        xl: "h-14 rounded-2xl px-10 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      asChild = false,
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : "button";

    if (asChild) {
      return (
        <Comp
          className={cn(buttonVariants({ variant, size, className }))}
          ref={ref}
          {...props}
        >
          {children}
        </Comp>
      );
    }

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : leftIcon ? (
          <span className="mr-2">{leftIcon}</span>
        ) : null}
        {children}
        {rightIcon && !loading && <span className="ml-2">{rightIcon}</span>}
      </Comp>
    );
  }
);
Button.displayName = "Button";

// Icon Button Component
const IconButton = React.forwardRef<
  HTMLButtonElement,
  Omit<ButtonProps, "leftIcon" | "rightIcon"> & { icon: React.ReactNode }
>(({ className, icon, size = "icon", ...props }, ref) => (
  <Button ref={ref} size={size} className={cn("p-0", className)} {...props}>
    {icon}
  </Button>
));
IconButton.displayName = "IconButton";

export { Button, IconButton, buttonVariants };
