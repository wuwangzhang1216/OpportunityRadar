"use client";

import * as React from "react";
import { Tab } from "@headlessui/react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface TabsProps {
  tabs: {
    id: string;
    label: string;
    icon?: React.ReactNode;
    content?: React.ReactNode;
    badge?: string | number;
  }[];
  defaultIndex?: number;
  activeTab?: string;
  onChange?: (tabIdOrIndex: string | number) => void;
  variant?: "default" | "pills" | "underline";
  className?: string;
}

export function Tabs({
  tabs,
  defaultIndex = 0,
  activeTab,
  onChange,
  variant = "default",
  className,
}: TabsProps) {
  // Determine initial index from activeTab or defaultIndex
  const initialIndex = activeTab
    ? tabs.findIndex((t) => t.id === activeTab)
    : defaultIndex;
  const [selectedIndex, setSelectedIndex] = React.useState(
    initialIndex >= 0 ? initialIndex : 0
  );

  // Sync with external activeTab prop
  React.useEffect(() => {
    if (activeTab) {
      const index = tabs.findIndex((t) => t.id === activeTab);
      if (index >= 0 && index !== selectedIndex) {
        setSelectedIndex(index);
      }
    }
  }, [activeTab, tabs, selectedIndex]);

  const handleChange = (index: number) => {
    setSelectedIndex(index);
    // Pass tab id if activeTab mode is being used, otherwise pass index
    onChange?.(activeTab !== undefined ? tabs[index].id : index);
  };

  const hasContent = tabs.some((tab) => tab.content !== undefined);

  return (
    <Tab.Group selectedIndex={selectedIndex} onChange={handleChange}>
      <Tab.List
        className={cn(
          "flex",
          variant === "default" && "gap-1 rounded-xl bg-gray-100 p-1",
          variant === "pills" && "gap-2",
          variant === "underline" && "gap-6 border-b border-gray-200",
          className
        )}
      >
        {tabs.map((tab, index) => (
          <Tab
            key={tab.id}
            className={({ selected }) =>
              cn(
                "relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all focus:outline-none",
                variant === "default" && [
                  "rounded-lg",
                  selected
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900 hover:bg-white/50",
                ],
                variant === "pills" && [
                  "rounded-full",
                  selected
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100",
                ],
                variant === "underline" && [
                  "pb-3 border-b-2 -mb-px",
                  selected
                    ? "border-primary text-primary"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                ]
              )
            }
          >
            {tab.icon && <span className="h-4 w-4">{tab.icon}</span>}
            {tab.label}
            {tab.badge !== undefined && (
              <span
                className={cn(
                  "ml-1 rounded-full px-2 py-0.5 text-xs font-medium",
                  selectedIndex === index
                    ? "bg-primary/20 text-primary"
                    : "bg-gray-200 text-gray-600"
                )}
              >
                {tab.badge}
              </span>
            )}
            {variant === "default" && selectedIndex === index && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 rounded-lg bg-white shadow-sm -z-10"
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )}
          </Tab>
        ))}
      </Tab.List>

      {hasContent && (
        <Tab.Panels className="mt-4">
          {tabs.map((tab) => (
            <Tab.Panel
              key={tab.id}
              className={cn(
                "rounded-xl focus:outline-none",
                "animate-fade-in"
              )}
            >
              {tab.content}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      )}
    </Tab.Group>
  );
}

// Simple Tab components for custom layouts
export function TabList({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Tab.List className={cn("flex gap-1", className)}>{children}</Tab.List>
  );
}

export function TabItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Tab
      className={({ selected }) =>
        cn(
          "px-4 py-2 text-sm font-medium rounded-lg transition-all focus:outline-none",
          selected
            ? "bg-primary text-primary-foreground shadow-md"
            : "text-gray-600 hover:text-gray-900 hover:bg-gray-100",
          className
        )
      }
    >
      {children}
    </Tab>
  );
}

export function TabPanels({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <Tab.Panels className={cn("mt-4", className)}>{children}</Tab.Panels>;
}

export function TabPanel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Tab.Panel className={cn("animate-fade-in focus:outline-none", className)}>
      {children}
    </Tab.Panel>
  );
}

export { Tab };
