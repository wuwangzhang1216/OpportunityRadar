"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  LayoutDashboard,
  Database,
  LogOut,
  ArrowLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

const adminNavItems = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard },
  { href: "/admin/opportunities", label: "Opportunities", icon: Database },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout, checkAuth, isLoading, hasHydrated } = useAuthStore();
  const [authChecked, setAuthChecked] = useState(false);
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    if (!hasHydrated) return;

    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    if (isAuthenticated && user) {
      setAuthChecked(true);
      return;
    }

    if (!authChecked) {
      checkAuth().then(() => setAuthChecked(true));
    }
  }, [hasHydrated, isAuthenticated, user, authChecked]);

  // Check admin status
  useEffect(() => {
    const checkAdminStatus = async () => {
      if (authChecked && isAuthenticated && isAdmin === null) {
        try {
          // Try to access admin endpoint to verify admin status
          await apiClient.getAdminAnalytics();
          setIsAdmin(true);
        } catch (error: any) {
          if (error.response?.status === 403) {
            setIsAdmin(false);
            router.push("/dashboard");
          } else {
            // Other error, might be network issue
            console.error("Admin check failed:", error);
            setIsAdmin(false);
            router.push("/dashboard");
          }
        }
      }
    };
    checkAdminStatus();
  }, [authChecked, isAuthenticated, isAdmin, router]);

  useEffect(() => {
    if (hasHydrated && authChecked && !isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [hasHydrated, authChecked, isLoading, isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  // Loading state
  if (!hasHydrated || isLoading || !authChecked || isAdmin === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-12 w-12 rounded-full border-4 border-orange-500/20 border-t-orange-500 animate-spin" />
            <Shield className="absolute inset-0 m-auto h-5 w-5 text-orange-500 animate-pulse" />
          </div>
          <p className="text-sm text-muted-foreground animate-pulse">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Admin Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 hidden lg:block">
        <div className="flex h-full flex-col bg-card border-r border-border">
          {/* Header */}
          <div className="flex h-16 items-center gap-3 px-4 border-b border-border bg-orange-500/5">
            <div className="h-10 w-10 bg-orange-500 rounded-xl flex items-center justify-center">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-foreground">Admin</span>
              <p className="text-xs text-muted-foreground">OpportunityRadar</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {adminNavItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}>
                  <motion.div
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isActive
                        ? "bg-orange-500/10 text-orange-600"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                    )}
                  >
                    <div
                      className={cn(
                        "flex items-center justify-center w-9 h-9 rounded-lg transition-colors",
                        isActive
                          ? "bg-orange-500 text-white"
                          : "bg-secondary text-muted-foreground"
                      )}
                    >
                      <item.icon className="h-5 w-5" />
                    </div>
                    <span>{item.label}</span>
                  </motion.div>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-border p-4 space-y-2">
            <Link href="/dashboard">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-muted-foreground hover:text-primary"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to App
              </Button>
            </Link>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-muted-foreground hover:text-red-600 hover:bg-red-50"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="fixed top-0 left-0 right-0 z-50 lg:hidden">
        <div className="bg-card border-b border-border">
          <div className="flex items-center justify-between h-16 px-4">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 bg-orange-500 rounded-xl flex items-center justify-center">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-foreground">Admin</span>
            </div>
            <div className="flex items-center gap-2">
              {adminNavItems.map((item) => (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={pathname === item.href ? "default" : "ghost"}
                    size="sm"
                    className={pathname === item.href ? "bg-orange-500 hover:bg-orange-600" : ""}
                  >
                    <item.icon className="h-4 w-4" />
                  </Button>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="min-h-screen lg:ml-64 pt-16 lg:pt-0">
        <div className="p-4 lg:p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
