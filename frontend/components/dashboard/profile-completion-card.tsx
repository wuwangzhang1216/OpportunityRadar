"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  User,
  CheckCircle2,
  Circle,
  ArrowRight,
  Sparkles,
  Target,
  Code,
  FileText,
  Trophy,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { apiClient } from "@/services/api-client";

interface ProfileCheckItem {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  check: (profile: any) => boolean;
  weight: number;
  href: string;
}

const profileChecks: ProfileCheckItem[] = [
  {
    id: "basic_info",
    label: "Basic Information",
    description: "Name and email",
    icon: User,
    check: (p) => !!(p?.name && p?.email),
    weight: 10,
    href: "/profile",
  },
  {
    id: "bio",
    label: "Bio",
    description: "Tell us about yourself",
    icon: FileText,
    check: (p) => !!(p?.bio && p.bio.length > 20),
    weight: 15,
    href: "/profile",
  },
  {
    id: "skills",
    label: "Skills",
    description: "Add your technical skills",
    icon: Code,
    check: (p) => !!(p?.skills && p.skills.length >= 3),
    weight: 20,
    href: "/profile",
  },
  {
    id: "interests",
    label: "Interests",
    description: "What areas excite you?",
    icon: Target,
    check: (p) => !!(p?.interests && p.interests.length >= 2),
    weight: 15,
    href: "/profile",
  },
  {
    id: "experience",
    label: "Experience Level",
    description: "Your hackathon experience",
    icon: Trophy,
    check: (p) => !!(p?.experience_level),
    weight: 10,
    href: "/profile",
  },
  {
    id: "goals",
    label: "Goals",
    description: "What do you want to achieve?",
    icon: Sparkles,
    check: (p) => !!(p?.goals && p.goals.length >= 1),
    weight: 15,
    href: "/profile",
  },
  {
    id: "availability",
    label: "Availability",
    description: "When can you participate?",
    icon: Target,
    check: (p) => !!(p?.availability),
    weight: 15,
    href: "/profile",
  },
];

export function ProfileCompletionCard() {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiClient.getProfile(),
  });

  const { completionScore, completedItems, incompleteItems, nextAction } = useMemo(() => {
    if (!profile) {
      return { completionScore: 0, completedItems: [], incompleteItems: profileChecks, nextAction: profileChecks[0] };
    }

    const completed: ProfileCheckItem[] = [];
    const incomplete: ProfileCheckItem[] = [];
    let score = 0;

    profileChecks.forEach((check) => {
      if (check.check(profile)) {
        completed.push(check);
        score += check.weight;
      } else {
        incomplete.push(check);
      }
    });

    return {
      completionScore: score,
      completedItems: completed,
      incompleteItems: incomplete,
      nextAction: incomplete[0] || null,
    };
  }, [profile]);

  // Don't show if profile is fully complete
  if (completionScore >= 100) {
    return null;
  }

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <CardContent className="py-4">
          <div className="h-4 bg-secondary rounded w-1/3 mb-2" />
          <div className="h-2 bg-secondary/50 rounded w-full" />
        </CardContent>
      </Card>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 50) return "text-yellow-600";
    return "text-orange-600";
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-orange-500";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-primary/20 bg-gradient-to-r from-primary/5 via-transparent to-transparent overflow-hidden">
        <CardContent className="py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Progress info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <User className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">Complete Your Profile</span>
                <span className={`text-sm font-bold ${getScoreColor(completionScore)}`}>
                  {completionScore}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-secondary rounded-full overflow-hidden mb-2">
                <motion.div
                  className={`h-full rounded-full ${getProgressColor(completionScore)}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${completionScore}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                />
              </div>

              {/* Completed checkmarks */}
              <div className="flex items-center gap-1 flex-wrap">
                {profileChecks.map((check) => {
                  const isComplete = completedItems.includes(check);
                  const Icon = check.icon;
                  return (
                    <div
                      key={check.id}
                      className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs ${
                        isComplete
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-secondary text-muted-foreground"
                      }`}
                      title={check.label}
                    >
                      {isComplete ? (
                        <CheckCircle2 className="h-3 w-3" />
                      ) : (
                        <Circle className="h-3 w-3" />
                      )}
                      <span className="hidden sm:inline">{check.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right: Next action */}
            {nextAction && (
              <Link href={nextAction.href}>
                <Button size="sm" className="shrink-0">
                  {nextAction.label}
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            )}
          </div>

          {/* Benefit message */}
          {completionScore < 50 && (
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-primary" />
              Complete your profile for better opportunity matching
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
