"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface TooltipProps {
  children: React.ReactNode;
  content: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  delayDuration?: number;
  className?: string;
}

export function Tooltip({
  children,
  content,
  side = "top",
  align = "center",
  delayDuration = 200,
  className,
}: TooltipProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [delayHandler, setDelayHandler] = React.useState<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    const handler = setTimeout(() => setIsOpen(true), delayDuration);
    setDelayHandler(handler);
  };

  const handleMouseLeave = () => {
    if (delayHandler) {
      clearTimeout(delayHandler);
      setDelayHandler(null);
    }
    setIsOpen(false);
  };

  const sidePositions = {
    top: "bottom-full mb-2",
    bottom: "top-full mt-2",
    left: "right-full mr-2",
    right: "left-full ml-2",
  };

  const alignPositions = {
    start: side === "top" || side === "bottom" ? "left-0" : "top-0",
    center: side === "top" || side === "bottom" ? "left-1/2 -translate-x-1/2" : "top-1/2 -translate-y-1/2",
    end: side === "top" || side === "bottom" ? "right-0" : "bottom-0",
  };

  const animationVariants = {
    top: { initial: { opacity: 0, y: 5 }, animate: { opacity: 1, y: 0 } },
    bottom: { initial: { opacity: 0, y: -5 }, animate: { opacity: 1, y: 0 } },
    left: { initial: { opacity: 0, x: 5 }, animate: { opacity: 1, x: 0 } },
    right: { initial: { opacity: 0, x: -5 }, animate: { opacity: 1, x: 0 } },
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      <AnimatePresence>
        {isOpen && content && (
          <motion.div
            initial={animationVariants[side].initial}
            animate={animationVariants[side].animate}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className={cn(
              "absolute z-50 pointer-events-none",
              sidePositions[side],
              alignPositions[align],
              className
            )}
          >
            <div className="bg-popover text-popover-foreground border border-border rounded-lg px-3 py-2 text-sm shadow-lg max-w-xs">
              {content}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Specialized Score Tooltip
interface ScoreBreakdownProps {
  score: number;
  breakdown?: {
    tech_match?: number;
    industry_match?: number;
    goals_match?: number;
    description_match?: number;
  };
  reasons?: string[];
}

export function ScoreTooltip({
  children,
  score,
  breakdown,
  reasons,
}: { children: React.ReactNode } & ScoreBreakdownProps) {
  const getScoreLabel = (score: number) => {
    if (score >= 80) return { label: "Excellent Match", color: "text-green-600" };
    if (score >= 60) return { label: "Good Match", color: "text-primary" };
    if (score >= 40) return { label: "Fair Match", color: "text-yellow-600" };
    return { label: "Low Match", color: "text-gray-500" };
  };

  const { label, color } = getScoreLabel(score);

  const content = (
    <div className="space-y-3 min-w-[200px]">
      <div className="flex items-center justify-between">
        <span className="font-semibold">AI Match Score</span>
        <span className={cn("font-bold", color)}>{score}%</span>
      </div>
      <p className={cn("text-xs", color)}>{label}</p>

      {breakdown && Object.keys(breakdown).length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border">
          <p className="text-xs text-muted-foreground font-medium">Score Breakdown:</p>
          {breakdown.tech_match !== undefined && (
            <ScoreBar label="Tech Stack" value={breakdown.tech_match} />
          )}
          {breakdown.industry_match !== undefined && (
            <ScoreBar label="Industry" value={breakdown.industry_match} />
          )}
          {breakdown.goals_match !== undefined && (
            <ScoreBar label="Goals" value={breakdown.goals_match} />
          )}
          {breakdown.description_match !== undefined && (
            <ScoreBar label="Description" value={breakdown.description_match} />
          )}
        </div>
      )}

      {reasons && reasons.length > 0 && (
        <div className="pt-2 border-t border-border">
          <p className="text-xs text-muted-foreground font-medium mb-1">Match Reasons:</p>
          <ul className="text-xs space-y-0.5">
            {reasons.slice(0, 3).map((reason, i) => (
              <li key={i} className="flex items-start gap-1">
                <span className="text-primary">•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  return (
    <Tooltip content={content} side="top" align="end">
      {children}
    </Tooltip>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
