"use client";

import * as React from "react";
import { Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  showCloseButton?: boolean;
}

const sizeClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  full: "max-w-4xl",
};

export function Modal({
  isOpen,
  onClose,
  children,
  className,
  size = "md",
  showCloseButton = true,
}: ModalProps) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95 translate-y-4"
              enterTo="opacity-100 scale-100 translate-y-0"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100 translate-y-0"
              leaveTo="opacity-0 scale-95 translate-y-4"
            >
              <Dialog.Panel
                className={cn(
                  "w-full transform overflow-hidden rounded-2xl bg-white p-6 shadow-2xl transition-all",
                  "border border-gray-100",
                  sizeClasses[size],
                  className
                )}
              >
                {showCloseButton && (
                  <button
                    onClick={onClose}
                    className="absolute right-4 top-4 rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
                {children}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export function ModalHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("mb-4", className)} {...props}>
      {children}
    </div>
  );
}

export function ModalTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <Dialog.Title
      as="h3"
      className={cn(
        "text-xl font-semibold leading-6 text-gray-900",
        className
      )}
      {...props}
    >
      {children}
    </Dialog.Title>
  );
}

export function ModalDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <Dialog.Description
      className={cn("mt-2 text-sm text-gray-500", className)}
      {...props}
    >
      {children}
    </Dialog.Description>
  );
}

export function ModalBody({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("mt-4", className)} {...props}>
      {children}
    </div>
  );
}

export function ModalFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("mt-6 flex items-center justify-end gap-3", className)}
      {...props}
    >
      {children}
    </div>
  );
}
