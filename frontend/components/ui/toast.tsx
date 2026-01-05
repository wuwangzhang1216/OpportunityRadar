"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { create } from "zustand";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  X,
  Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

// Types
export type ToastVariant = "success" | "error" | "warning" | "info" | "ai";

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

// Store
export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    };

    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));

    // Auto-dismiss
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, newToast.duration);
    }

    return id;
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
  clearAll: () => {
    set({ toasts: [] });
  },
}));

// Hook for easy access
export function useToast() {
  const { addToast, removeToast, clearAll } = useToastStore();

  return {
    toast: addToast,
    dismiss: removeToast,
    dismissAll: clearAll,
    success: (title: string, description?: string, action?: Toast["action"]) =>
      addToast({ title, description, variant: "success", action }),
    error: (title: string, description?: string, action?: Toast["action"]) =>
      addToast({ title, description, variant: "error", duration: 8000, action }),
    warning: (title: string, description?: string, action?: Toast["action"]) =>
      addToast({ title, description, variant: "warning", action }),
    info: (title: string, description?: string, action?: Toast["action"]) =>
      addToast({ title, description, variant: "info", action }),
    ai: (title: string, description?: string, action?: Toast["action"]) =>
      addToast({ title, description, variant: "ai", action }),
  };
}

// Icon mapping
const variantIcons: Record<ToastVariant, React.ElementType> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  ai: Sparkles,
};

// Styles mapping
const variantStyles: Record<ToastVariant, string> = {
  success: "border-urgency-safe/30 bg-urgency-safe/10",
  error: "border-urgency-critical/30 bg-urgency-critical/10",
  warning: "border-urgency-warning/30 bg-urgency-warning/10",
  info: "border-primary/30 bg-primary/10",
  ai: "border-purple-500/30 bg-gradient-to-r from-primary/10 to-purple-500/10",
};

const variantIconStyles: Record<ToastVariant, string> = {
  success: "text-urgency-safe",
  error: "text-urgency-critical",
  warning: "text-urgency-warning",
  info: "text-primary",
  ai: "text-purple-500",
};

// Single Toast Component
function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToastStore();
  const Icon = variantIcons[toast.variant];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
      className={cn(
        "pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-xl border p-4 shadow-lg backdrop-blur-sm",
        "bg-background/95",
        variantStyles[toast.variant]
      )}
    >
      {/* AI shimmer for AI variant */}
      {toast.variant === "ai" && (
        <div className="absolute inset-0 ai-shimmer opacity-20" />
      )}

      {/* Icon */}
      <div className={cn("flex-shrink-0 mt-0.5", variantIconStyles[toast.variant])}>
        <Icon className="h-5 w-5" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-foreground">{toast.title}</p>
        {toast.description && (
          <p className="mt-1 text-sm text-muted-foreground">{toast.description}</p>
        )}
        {toast.action && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-7 px-2 text-xs font-medium"
            onClick={() => {
              toast.action?.onClick();
              removeToast(toast.id);
            }}
          >
            {toast.action.label}
          </Button>
        )}
      </div>

      {/* Close button */}
      <button
        onClick={() => removeToast(toast.id)}
        className="flex-shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </motion.div>
  );
}

// Toast Container Component
export function ToastContainer() {
  const { toasts } = useToastStore();

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm pointer-events-none"
      role="region"
      aria-label="Notifications"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
}

// Toaster - wrapper to be used in layout
export function Toaster() {
  return <ToastContainer />;
}
