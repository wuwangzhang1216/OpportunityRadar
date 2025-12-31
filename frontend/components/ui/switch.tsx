"use client";

import * as React from "react";
import { Switch as HeadlessSwitch } from "@headlessui/react";
import { cn } from "@/lib/utils";

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "success" | "ai";
  label?: string;
  description?: string;
  className?: string;
}

const sizeClasses = {
  sm: {
    switch: "h-5 w-9",
    thumb: "h-3 w-3",
    translate: "translate-x-4",
  },
  md: {
    switch: "h-6 w-11",
    thumb: "h-4 w-4",
    translate: "translate-x-5",
  },
  lg: {
    switch: "h-7 w-14",
    thumb: "h-5 w-5",
    translate: "translate-x-7",
  },
};

const variantClasses = {
  default: "bg-primary",
  success: "bg-green-500",
  ai: "bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500",
};

export function Switch({
  checked,
  onChange,
  disabled = false,
  size = "md",
  variant = "default",
  label,
  description,
  className,
}: SwitchProps) {
  const sizes = sizeClasses[size];

  return (
    <HeadlessSwitch.Group>
      <div className={cn("flex items-center gap-3", className)}>
        <HeadlessSwitch
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className={cn(
            "relative inline-flex shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
            sizes.switch,
            checked ? variantClasses[variant] : "bg-gray-200",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none inline-block transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out",
              sizes.thumb,
              checked ? sizes.translate : "translate-x-1"
            )}
          />
        </HeadlessSwitch>

        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <HeadlessSwitch.Label
                className={cn(
                  "text-sm font-medium text-gray-900 cursor-pointer",
                  disabled && "cursor-not-allowed opacity-50"
                )}
              >
                {label}
              </HeadlessSwitch.Label>
            )}
            {description && (
              <HeadlessSwitch.Description className="text-sm text-gray-500">
                {description}
              </HeadlessSwitch.Description>
            )}
          </div>
        )}
      </div>
    </HeadlessSwitch.Group>
  );
}

// Controlled Switch with internal state
interface ToggleProps extends Omit<SwitchProps, "checked" | "onChange"> {
  defaultChecked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export function Toggle({
  defaultChecked = false,
  onCheckedChange,
  ...props
}: ToggleProps) {
  const [checked, setChecked] = React.useState(defaultChecked);

  const handleChange = (value: boolean) => {
    setChecked(value);
    onCheckedChange?.(value);
  };

  return <Switch checked={checked} onChange={handleChange} {...props} />;
}
