"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
  category: "navigation" | "action" | "view";
}

// Global keyboard shortcuts configuration
const defaultShortcuts: Omit<ShortcutConfig, "action">[] = [
  // Navigation shortcuts
  { key: "g", shift: true, description: "Go to Dashboard", category: "navigation" },
  { key: "o", shift: true, description: "Go to Opportunities", category: "navigation" },
  { key: "p", shift: true, description: "Go to Pipeline", category: "navigation" },
  { key: "m", shift: true, description: "Go to Generator", category: "navigation" },
  { key: "s", shift: true, description: "Go to Settings", category: "navigation" },

  // Action shortcuts
  { key: "/", description: "Focus search", category: "action" },
  { key: "?", shift: true, description: "Show keyboard shortcuts", category: "action" },
  { key: "Escape", description: "Close modal / clear focus", category: "action" },
];

export function useKeyboardShortcuts() {
  const router = useRouter();
  const [showHelp, setShowHelp] = useState(false);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        // Only allow Escape in input fields
        if (event.key !== "Escape") {
          return;
        }
      }

      const key = event.key.toLowerCase();
      const hasCtrl = event.ctrlKey || event.metaKey;
      const hasShift = event.shiftKey;
      const hasAlt = event.altKey;

      // Navigation shortcuts (Shift + key)
      if (hasShift && !hasCtrl && !hasAlt) {
        switch (key) {
          case "g":
            event.preventDefault();
            router.push("/dashboard");
            return;
          case "o":
            event.preventDefault();
            router.push("/opportunities");
            return;
          case "p":
            event.preventDefault();
            router.push("/pipeline");
            return;
          case "m":
            event.preventDefault();
            router.push("/generator");
            return;
          case "s":
            event.preventDefault();
            router.push("/settings");
            return;
          case "?":
            event.preventDefault();
            setShowHelp((prev) => !prev);
            return;
        }
      }

      // Single key shortcuts (no modifiers)
      if (!hasCtrl && !hasShift && !hasAlt) {
        switch (key) {
          case "/":
            event.preventDefault();
            // Focus search input if exists
            const searchInput = document.querySelector<HTMLInputElement>(
              'input[placeholder*="Search"], input[type="search"]'
            );
            if (searchInput) {
              searchInput.focus();
            }
            return;
          case "escape":
            // Close any open modals or clear focus
            const activeElement = document.activeElement as HTMLElement;
            if (activeElement) {
              activeElement.blur();
            }
            setShowHelp(false);
            return;
        }
      }
    },
    [router]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    showHelp,
    setShowHelp,
    shortcuts: defaultShortcuts,
  };
}

// Hook for list navigation (j/k for up/down)
export function useListNavigation(
  items: any[],
  onSelect?: (item: any, index: number) => void
) {
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      const key = event.key.toLowerCase();

      switch (key) {
        case "j":
          // Move down
          event.preventDefault();
          setSelectedIndex((prev) =>
            prev < items.length - 1 ? prev + 1 : prev
          );
          break;
        case "k":
          // Move up
          event.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case "enter":
          // Select current item
          if (selectedIndex >= 0 && selectedIndex < items.length && onSelect) {
            event.preventDefault();
            onSelect(items[selectedIndex], selectedIndex);
          }
          break;
        case "escape":
          // Clear selection
          setSelectedIndex(-1);
          break;
      }
    },
    [items, selectedIndex, onSelect]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    selectedIndex,
    setSelectedIndex,
  };
}
