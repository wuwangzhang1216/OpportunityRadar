"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radar,
  LayoutDashboard,
  Search,
  User,
  Kanban,
  Sparkles,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Bell,
  Settings,
  Users,
  Send,
  Globe,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/opportunities", label: "Opportunities", icon: Search },
  { href: "/pipeline", label: "Pipeline", icon: Kanban },
  { href: "/generator", label: "AI Generator", icon: Sparkles },
  { href: "/materials", label: "My Materials", icon: FileText },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/community", label: "Community", icon: Globe },
  { href: "/submissions", label: "Submissions", icon: Send },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/settings", label: "Settings", icon: Settings },
];
const adminNavItem = { href: "/admin", label: "Admin", icon: Settings };

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout, checkAuth, isLoading, hasHydrated } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    // Wait for hydration to complete before doing anything
    if (!hasHydrated) return;

    // Check if we need to verify auth
    const token = localStorage.getItem("auth_token");

    if (!token) {
      // No token at all, redirect to login
      router.push("/login");
      return;
    }

    // If we have a token and user data from hydration, we're good
    if (isAuthenticated && user) {
      setAuthChecked(true);
      return;
    }

    // We have a token but no user data, try to fetch it
    if (!authChecked) {
      checkAuth().then(() => {
        setAuthChecked(true);
      });
    }
  }, [hasHydrated, isAuthenticated, user, authChecked]);

  useEffect(() => {
    // Only redirect after we've done a proper auth check
    if (hasHydrated && authChecked && !isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [hasHydrated, authChecked, isLoading, isAuthenticated, router]);

  useEffect(() => {
    const checkAdminStatus = async () => {
      if (authChecked && isAuthenticated && isAdmin === null) {
        try {
          await apiClient.getAdminAnalytics();
          setIsAdmin(true);
        } catch (error: unknown) {
          if (error && typeof error === "object" && "response" in error) {
            setIsAdmin(false);
            return;
          }
          console.error("Admin check failed:", error);
          setIsAdmin(false);
        }
      }
    };
    checkAdminStatus();
  }, [authChecked, isAuthenticated, isAdmin]);

  // Check onboarding status and redirect if not completed
  useEffect(() => {
    const checkOnboarding = async () => {
      // Only check after auth is confirmed
      if (authChecked && !isLoading && isAuthenticated && !onboardingChecked) {
        try {
          const status = await apiClient.getOnboardingStatus();
          console.log("Onboarding status:", status);
          if (!status.onboarding_completed) {
            router.push("/onboarding");
            return; // Don't set onboardingChecked, let the redirect happen
          }
          setOnboardingChecked(true);
        } catch (error) {
          // If check fails, allow access but log error
          console.error("Failed to check onboarding status:", error);
          setOnboardingChecked(true);
        }
      }
    };
    checkOnboarding();
  }, [authChecked, isLoading, isAuthenticated, onboardingChecked, router]);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  // Show loading while hydrating, checking auth, or checking onboarding
  if (!hasHydrated || isLoading || !authChecked || (isAuthenticated && !onboardingChecked)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-12 w-12 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
            <Sparkles className="absolute inset-0 m-auto h-5 w-5 text-primary animate-pulse" />
          </div>
          <p className="text-sm text-muted-foreground animate-pulse">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const menuItems = isAdmin ? [...navItems, adminNavItem] : navItems;

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 280 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed left-0 top-0 z-40 h-screen hidden lg:block"
      >
        <div className="flex h-full flex-col bg-card border-r border-border">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-border">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="h-10 w-10 bg-primary rounded-xl flex items-center justify-center">
                <Radar className="h-6 w-6 text-white" />
              </div>
              <AnimatePresence>
                {!isCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="text-lg font-bold text-foreground"
                  >
                    OpportunityRadar
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-lg hover:bg-secondary transition-colors"
            >
              <ChevronRight
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform duration-300",
                  isCollapsed && "rotate-180"
                )}
              />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto scrollbar-modern">
            {menuItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}>
                  <motion.div
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isActive
                        ? "text-primary"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeNav"
                        className="absolute inset-0 bg-secondary rounded-xl"
                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                      />
                    )}
                    <div
                      className={cn(
                        "relative z-10 flex items-center justify-center w-9 h-9 rounded-lg transition-colors",
                        isActive
                          ? "bg-primary text-white"
                          : "bg-secondary text-muted-foreground"
                      )}
                    >
                      <item.icon className="h-5 w-5" />
                    </div>
                    <AnimatePresence>
                      {!isCollapsed && (
                        <motion.span
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          className="relative z-10"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </motion.div>
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="border-t border-border p-4">
            <div className={cn("flex items-center gap-3", isCollapsed && "justify-center")}>
              <div className="relative">
                <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
                  <span className="text-sm font-semibold text-white">
                    {user?.full_name?.charAt(0) || "U"}
                  </span>
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 bg-green-500 rounded-full border-2 border-card" />
              </div>
              <AnimatePresence>
                {!isCollapsed && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="flex-1 min-w-0"
                  >
                    <p className="text-sm font-medium truncate">{user?.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-muted-foreground mt-3 hover:text-red-600 hover:bg-red-50"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign out
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.aside>

      {/* Mobile Header */}
      <header className="fixed top-0 left-0 right-0 z-50 lg:hidden">
        <div className="bg-card border-b border-border">
          <div className="flex items-center justify-between h-16 px-4">
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="h-9 w-9 bg-primary rounded-xl flex items-center justify-center">
                <Radar className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-foreground">OpportunityRadar</span>
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/notifications" className="p-2 rounded-lg hover:bg-secondary transition-colors">
                <Bell className="h-5 w-5 text-muted-foreground" />
              </Link>
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 rounded-lg hover:bg-secondary transition-colors"
              >
                {isMobileMenuOpen ? (
                  <X className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <Menu className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 w-72 bg-card border-l border-border z-50 lg:hidden"
            >
              <div className="flex flex-col h-full pt-20 pb-4">
                <nav className="flex-1 space-y-1 px-3">
                  {menuItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <Link key={item.href} href={item.href}>
                        <div
                          className={cn(
                            "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors",
                            isActive
                              ? "bg-secondary text-primary"
                              : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                          )}
                        >
                          <div
                            className={cn(
                              "flex items-center justify-center w-9 h-9 rounded-lg",
                              isActive
                                ? "bg-primary text-white"
                                : "bg-secondary text-muted-foreground"
                            )}
                          >
                            <item.icon className="h-5 w-5" />
                          </div>
                          {item.label}
                        </div>
                      </Link>
                    );
                  })}
                </nav>
                <div className="border-t border-border px-4 pt-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
                      <span className="text-sm font-semibold text-white">
                        {user?.full_name?.charAt(0) || "U"}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{user?.full_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                    </div>
                  </div>
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
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main
        className={cn(
          "min-h-screen transition-all duration-300",
          "lg:ml-[280px]",
          isCollapsed && "lg:ml-20",
          "pt-16 lg:pt-0"
        )}
      >
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
