"use client";

import { useState, useRef } from "react";
import { motion, useMotionValue, useTransform, PanInfo } from "framer-motion";
import { Bookmark, X, Zap, Check } from "lucide-react";

interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: {
    icon?: React.ReactNode;
    label: string;
    color: string;
  };
  rightAction?: {
    icon?: React.ReactNode;
    label: string;
    color: string;
  };
  threshold?: number;
  className?: string;
}

export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction = {
    icon: <X className="h-5 w-5" />,
    label: "Dismiss",
    color: "bg-red-500",
  },
  rightAction = {
    icon: <Bookmark className="h-5 w-5" />,
    label: "Save",
    color: "bg-green-500",
  },
  threshold = 100,
  className = "",
}: SwipeableCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const constraintsRef = useRef(null);
  const x = useMotionValue(0);

  // Transform x position to opacity for action indicators
  const leftOpacity = useTransform(x, [-threshold, -threshold / 2, 0], [1, 0.5, 0]);
  const rightOpacity = useTransform(x, [0, threshold / 2, threshold], [0, 0.5, 1]);

  // Transform x position to scale for action icons
  const leftScale = useTransform(x, [-threshold, -threshold / 2, 0], [1.2, 1, 0.8]);
  const rightScale = useTransform(x, [0, threshold / 2, threshold], [0.8, 1, 1.2]);

  // Card rotation based on drag
  const rotate = useTransform(x, [-200, 0, 200], [-8, 0, 8]);

  const handleDragEnd = (event: any, info: PanInfo) => {
    setIsDragging(false);
    const offset = info.offset.x;
    const velocity = info.velocity.x;

    // Calculate if we should trigger action (combine offset and velocity)
    const swipeConfidence = Math.abs(offset) + Math.abs(velocity) * 0.5;

    if (offset < -threshold / 2 && swipeConfidence > threshold) {
      // Swiped left
      onSwipeLeft?.();
    } else if (offset > threshold / 2 && swipeConfidence > threshold) {
      // Swiped right
      onSwipeRight?.();
    }
  };

  return (
    <div className={`relative ${className}`} ref={constraintsRef}>
      {/* Left action indicator (dismiss) */}
      <motion.div
        className={`absolute inset-y-0 left-0 w-24 flex items-center justify-center rounded-l-xl ${leftAction.color}`}
        style={{ opacity: leftOpacity }}
      >
        <motion.div
          className="flex flex-col items-center text-white"
          style={{ scale: leftScale }}
        >
          {leftAction.icon}
          <span className="text-xs mt-1 font-medium">{leftAction.label}</span>
        </motion.div>
      </motion.div>

      {/* Right action indicator (save/prep) */}
      <motion.div
        className={`absolute inset-y-0 right-0 w-24 flex items-center justify-center rounded-r-xl ${rightAction.color}`}
        style={{ opacity: rightOpacity }}
      >
        <motion.div
          className="flex flex-col items-center text-white"
          style={{ scale: rightScale }}
        >
          {rightAction.icon}
          <span className="text-xs mt-1 font-medium">{rightAction.label}</span>
        </motion.div>
      </motion.div>

      {/* Card content */}
      <motion.div
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.7}
        onDragStart={() => setIsDragging(true)}
        onDragEnd={handleDragEnd}
        style={{ x, rotate }}
        className={`relative z-10 bg-card rounded-xl transition-shadow ${
          isDragging ? "shadow-lg cursor-grabbing" : "cursor-grab"
        }`}
      >
        {children}
      </motion.div>
    </div>
  );
}

// Specialized swipeable card for opportunities
interface SwipeableOpportunityCardProps {
  children: React.ReactNode;
  onDismiss?: () => void;
  onSave?: () => void;
  onQuickPrep?: () => void;
  className?: string;
}

export function SwipeableOpportunityCard({
  children,
  onDismiss,
  onSave,
  onQuickPrep,
  className = "",
}: SwipeableOpportunityCardProps) {
  return (
    <SwipeableCard
      onSwipeLeft={onDismiss}
      onSwipeRight={onQuickPrep || onSave}
      leftAction={{
        icon: <X className="h-5 w-5" />,
        label: "Dismiss",
        color: "bg-red-500",
      }}
      rightAction={{
        icon: onQuickPrep ? <Zap className="h-5 w-5" /> : <Bookmark className="h-5 w-5" />,
        label: onQuickPrep ? "Quick Prep" : "Save",
        color: onQuickPrep ? "bg-gradient-to-r from-primary to-purple-600" : "bg-green-500",
      }}
      className={className}
    >
      {children}
    </SwipeableCard>
  );
}
