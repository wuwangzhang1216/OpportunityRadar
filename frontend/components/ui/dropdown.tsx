"use client";

import * as React from "react";
import { Fragment } from "react";
import { Menu, Transition } from "@headlessui/react";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface DropdownProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  align?: "left" | "right";
  className?: string;
}

export function Dropdown({
  trigger,
  children,
  align = "right",
  className,
}: DropdownProps) {
  return (
    <Menu as="div" className={cn("relative inline-block text-left", className)}>
      <Menu.Button as={Fragment}>{trigger}</Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-200"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-150"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className={cn(
            "absolute z-50 mt-2 w-56 origin-top-right rounded-xl bg-white p-1 shadow-lg ring-1 ring-black/5 focus:outline-none",
            "border border-gray-100",
            align === "right" ? "right-0" : "left-0"
          )}
        >
          {children}
        </Menu.Items>
      </Transition>
    </Menu>
  );
}

interface DropdownItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  icon?: React.ReactNode;
  destructive?: boolean;
  disabled?: boolean;
  selected?: boolean;
}

export function DropdownItem({
  children,
  onClick,
  icon,
  destructive = false,
  disabled = false,
  selected = false,
}: DropdownItemProps) {
  return (
    <Menu.Item disabled={disabled}>
      {({ active }) => (
        <button
          onClick={onClick}
          className={cn(
            "group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
            active && !destructive && "bg-gray-50 text-gray-900",
            active && destructive && "bg-red-50 text-red-600",
            !active && destructive && "text-red-600",
            !active && !destructive && "text-gray-700",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          {icon && (
            <span
              className={cn(
                "h-4 w-4",
                active && !destructive && "text-gray-500",
                active && destructive && "text-red-500",
                !active && "text-gray-400"
              )}
            >
              {icon}
            </span>
          )}
          <span className="flex-1 text-left">{children}</span>
          {selected && <Check className="h-4 w-4 text-primary" />}
        </button>
      )}
    </Menu.Item>
  );
}

export function DropdownDivider() {
  return <div className="my-1 h-px bg-gray-100" />;
}

export function DropdownLabel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider", className)}>
      {children}
    </div>
  );
}

// Dropdown Button Trigger Component
interface DropdownButtonProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "outline" | "ghost";
}

export function DropdownButton({
  children,
  className,
  variant = "default",
}: DropdownButtonProps) {
  const variantClasses = {
    default:
      "bg-white border border-gray-200 hover:bg-gray-50 text-gray-700",
    outline:
      "border-2 border-gray-200 hover:border-gray-300 text-gray-700 bg-transparent",
    ghost: "hover:bg-gray-100 text-gray-700",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20",
        variantClasses[variant],
        className
      )}
    >
      {children}
      <ChevronDown className="h-4 w-4 text-gray-400" />
    </button>
  );
}
