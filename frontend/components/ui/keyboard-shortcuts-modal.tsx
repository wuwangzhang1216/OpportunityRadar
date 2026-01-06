"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Keyboard, Command } from "lucide-react";
import { Button } from "./button";

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const shortcuts = [
  {
    category: "Navigation",
    items: [
      { keys: ["Shift", "G"], description: "Go to Dashboard" },
      { keys: ["Shift", "O"], description: "Go to Opportunities" },
      { keys: ["Shift", "P"], description: "Go to Pipeline" },
      { keys: ["Shift", "M"], description: "Go to Material Generator" },
      { keys: ["Shift", "S"], description: "Go to Settings" },
    ],
  },
  {
    category: "Actions",
    items: [
      { keys: ["/"], description: "Focus search" },
      { keys: ["Esc"], description: "Close modal / clear focus" },
      { keys: ["Shift", "?"], description: "Show this help" },
    ],
  },
  {
    category: "List Navigation",
    items: [
      { keys: ["J"], description: "Move down in list" },
      { keys: ["K"], description: "Move up in list" },
      { keys: ["Enter"], description: "Select item" },
    ],
  },
];

function KeyBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 bg-secondary border border-border rounded text-xs font-mono font-medium text-foreground">
      {children}
    </span>
  );
}

export function KeyboardShortcutsModal({
  isOpen,
  onClose,
}: KeyboardShortcutsModalProps) {
  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-secondary/30">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
                    <Keyboard className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
                    <p className="text-xs text-muted-foreground">
                      Navigate faster with these shortcuts
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)] space-y-6">
                {shortcuts.map((section) => (
                  <div key={section.category}>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                      {section.category}
                    </h3>
                    <div className="space-y-2">
                      {section.items.map((shortcut, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-secondary/50 transition-colors"
                        >
                          <span className="text-sm text-foreground">
                            {shortcut.description}
                          </span>
                          <div className="flex items-center gap-1">
                            {shortcut.keys.map((key, keyIndex) => (
                              <span key={keyIndex} className="flex items-center gap-1">
                                <KeyBadge>{key}</KeyBadge>
                                {keyIndex < shortcut.keys.length - 1 && (
                                  <span className="text-muted-foreground text-xs">+</span>
                                )}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-border bg-secondary/20">
                <p className="text-xs text-muted-foreground text-center">
                  Press <KeyBadge>Shift</KeyBadge> + <KeyBadge>?</KeyBadge> anytime
                  to show this help
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
