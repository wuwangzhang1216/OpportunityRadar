"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { LucideIcon, Target, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    href: string;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  variant?: "default" | "opportunities" | "profile";
  className?: string;
}

const variantConfig = {
  default: {
    icon: Target,
    iconBg: "bg-secondary",
    iconColor: "text-muted-foreground",
  },
  opportunities: {
    icon: Sparkles,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
  },
  profile: {
    icon: User,
    iconBg: "bg-yellow-100",
    iconColor: "text-yellow-600",
  },
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  variant = "default",
  className,
}: EmptyStateProps) {
  const config = variantConfig[variant];
  const Icon = icon || config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn("text-center py-16 px-4", className)}
    >
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
        className={cn(
          "h-20 w-20 mx-auto rounded-2xl flex items-center justify-center mb-6",
          config.iconBg
        )}
      >
        <Icon className={cn("h-10 w-10", config.iconColor)} />
      </motion.div>

      <motion.h3
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-xl font-semibold text-foreground mb-2"
      >
        {title}
      </motion.h3>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-muted-foreground max-w-md mx-auto mb-6"
      >
        {description}
      </motion.p>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="flex flex-col sm:flex-row items-center justify-center gap-3"
      >
        {action && (
          <Link href={action.href}>
            <Button size="lg" className="gap-2">
              {action.label}
            </Button>
          </Link>
        )}
        {secondaryAction && (
          <Button
            size="lg"
            variant="outline"
            onClick={secondaryAction.onClick}
          >
            {secondaryAction.label}
          </Button>
        )}
      </motion.div>
    </motion.div>
  );
}

// Pre-configured empty states for common scenarios
export function NoMatchesEmptyState() {
  return (
    <EmptyState
      variant="profile"
      title="No matches yet"
      description="Complete your profile with your tech stack, goals, and interests to get personalized opportunity matches."
      action={{
        label: "Complete Profile",
        href: "/profile",
      }}
    />
  );
}

export function NoOpportunitiesEmptyState({
  onClearFilters,
}: {
  onClearFilters?: () => void;
}) {
  return (
    <EmptyState
      variant="opportunities"
      title="No opportunities found"
      description="Try adjusting your search filters or check back later for new opportunities."
      secondaryAction={
        onClearFilters
          ? {
              label: "Clear filters",
              onClick: onClearFilters,
            }
          : undefined
      }
    />
  );
}

export function ComputingMatchesEmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="text-center py-16 px-4"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="h-20 w-20 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center mb-6"
      >
        <Sparkles className="h-10 w-10 text-primary" />
      </motion.div>
      <h3 className="text-xl font-semibold text-foreground mb-2">
        Finding your matches...
      </h3>
      <p className="text-muted-foreground max-w-md mx-auto">
        We're analyzing opportunities to find the best matches for your profile.
        This usually takes a few seconds.
      </p>
    </motion.div>
  );
}
