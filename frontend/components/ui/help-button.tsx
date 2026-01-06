"use client";

import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";

interface HelpButtonProps {
  onTrigger: () => void;
  tooltipText?: string;
  className?: string;
}

export function HelpButton({
  onTrigger,
  tooltipText = "Show tutorial",
  className,
}: HelpButtonProps) {
  return (
    <Tooltip content={tooltipText} side="bottom">
      <Button
        variant="ghost"
        size="icon"
        onClick={onTrigger}
        aria-label={tooltipText}
        className={className}
      >
        <HelpCircle className="h-5 w-5" />
      </Button>
    </Tooltip>
  );
}
