"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Check, AlertCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProfileField {
  key: string;
  label: string;
  weight: number;
  filled: boolean;
  impact: "high" | "medium" | "low";
}

interface ProfileQualityScoreProps {
  profile: {
    product_name?: string;
    description?: string;
    tech_stack?: string[];
    industries?: string[];
    goals?: string[];
    team_size?: string;
    location?: string;
  };
  className?: string;
}

export function ProfileQualityScore({ profile, className }: ProfileQualityScoreProps) {
  const fields = useMemo<ProfileField[]>(() => [
    {
      key: "product_name",
      label: "Product Name",
      weight: 15,
      filled: !!profile.product_name?.trim(),
      impact: "high",
    },
    {
      key: "description",
      label: "Description",
      weight: 25,
      filled: !!profile.description?.trim() && profile.description.length > 50,
      impact: "high",
    },
    {
      key: "tech_stack",
      label: "Tech Stack",
      weight: 20,
      filled: !!profile.tech_stack?.length && profile.tech_stack.length > 0,
      impact: "high",
    },
    {
      key: "industries",
      label: "Industries",
      weight: 15,
      filled: !!profile.industries?.length && profile.industries.length > 0,
      impact: "medium",
    },
    {
      key: "goals",
      label: "Goals",
      weight: 15,
      filled: !!profile.goals?.length && profile.goals.length > 0,
      impact: "medium",
    },
    {
      key: "team_size",
      label: "Team Size",
      weight: 5,
      filled: !!profile.team_size,
      impact: "low",
    },
    {
      key: "location",
      label: "Location",
      weight: 5,
      filled: !!profile.location?.trim(),
      impact: "low",
    },
  ], [profile]);

  const score = useMemo(() => {
    return fields.reduce((acc, field) => acc + (field.filled ? field.weight : 0), 0);
  }, [fields]);

  const filledCount = fields.filter(f => f.filled).length;
  const missingHighImpact = fields.filter(f => !f.filled && f.impact === "high");

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    if (score >= 40) return "text-orange-500";
    return "text-red-500";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Good";
    if (score >= 40) return "Fair";
    return "Needs Work";
  };

  const getStrokeColor = (score: number) => {
    if (score >= 80) return "#22c55e";
    if (score >= 60) return "#eab308";
    if (score >= 40) return "#f97316";
    return "#ef4444";
  };

  // SVG circle properties
  const size = 120;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  return (
    <div className={cn("bg-gradient-to-br from-primary/5 to-purple-500/5 rounded-2xl p-6 border border-primary/20", className)}>
      <div className="flex items-start gap-6">
        {/* Circular Progress */}
        <div className="relative flex-shrink-0">
          <svg width={size} height={size} className="transform -rotate-90">
            {/* Background circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={strokeWidth}
              className="text-secondary"
            />
            {/* Progress circle */}
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={getStrokeColor(score)}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference - progress }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={cn("text-3xl font-bold", getScoreColor(score))}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
            >
              {score}%
            </motion.span>
            <span className="text-xs text-muted-foreground">{getScoreLabel(score)}</span>
          </div>
        </div>

        {/* Field Status */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">Profile Quality</h3>
            <span className="text-xs text-muted-foreground">
              {filledCount}/{fields.length} fields
            </span>
          </div>

          {/* Missing high-impact fields warning */}
          {missingHighImpact.length > 0 && (
            <div className="bg-urgency-warning/10 border border-urgency-warning/20 rounded-lg p-3 mb-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-urgency-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-medium text-urgency-warning">
                    Complete these for better matches:
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {missingHighImpact.map(f => f.label).join(", ")}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Field list */}
          <div className="grid grid-cols-2 gap-2">
            {fields.map((field) => (
              <motion.div
                key={field.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={cn(
                  "flex items-center gap-2 text-xs py-1",
                  field.filled ? "text-foreground" : "text-muted-foreground"
                )}
              >
                <div className={cn(
                  "h-4 w-4 rounded-full flex items-center justify-center flex-shrink-0",
                  field.filled
                    ? "bg-green-100 text-green-600"
                    : "bg-secondary text-muted-foreground"
                )}>
                  {field.filled ? (
                    <Check className="h-2.5 w-2.5" />
                  ) : (
                    <span className="text-[8px]">+{field.weight}</span>
                  )}
                </div>
                <span className={cn(
                  field.filled && "line-through opacity-60"
                )}>
                  {field.label}
                </span>
                {field.impact === "high" && !field.filled && (
                  <span className="text-[9px] px-1 py-0.5 bg-primary/10 text-primary rounded">
                    High Impact
                  </span>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
