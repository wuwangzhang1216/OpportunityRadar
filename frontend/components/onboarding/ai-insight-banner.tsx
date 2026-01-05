"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Sparkles, Brain, Target, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface AIInsightBannerProps {
  profile: {
    product_name?: string;
    description?: string;
    tech_stack?: string[];
    industries?: string[];
    goals?: string[];
    team_size?: string;
  };
  urlType?: "github" | "website" | "manual";
  className?: string;
}

export function AIInsightBanner({ profile, urlType, className }: AIInsightBannerProps) {
  const insights = useMemo(() => {
    const result: { icon: typeof Sparkles; label: string; value: string }[] = [];

    // Determine profile type based on data
    const profileType = determineProfileType(profile);
    if (profileType) {
      result.push({
        icon: Target,
        label: "Profile Type",
        value: profileType,
      });
    }

    // Primary industry
    if (profile.industries?.length) {
      result.push({
        icon: Brain,
        label: "Focus Area",
        value: profile.industries.slice(0, 2).join(" & "),
      });
    }

    // Tech focus
    const techFocus = determineTechFocus(profile.tech_stack || []);
    if (techFocus) {
      result.push({
        icon: Zap,
        label: "Tech Focus",
        value: techFocus,
      });
    }

    // Opportunity fit
    const opportunityFit = determineOpportunityFit(profile);
    if (opportunityFit) {
      result.push({
        icon: Sparkles,
        label: "Best Match",
        value: opportunityFit,
      });
    }

    return result;
  }, [profile]);

  // Generate AI summary
  const summary = useMemo(() => {
    const parts: string[] = [];

    if (urlType === "github") {
      parts.push("Based on your GitHub profile");
    } else if (urlType === "website") {
      parts.push("Based on your website");
    } else {
      parts.push("Based on your profile");
    }

    const profileType = determineProfileType(profile);
    if (profileType) {
      parts.push(`I've identified you as a ${profileType.toLowerCase()}`);
    }

    if (profile.industries?.length) {
      parts.push(`focused on ${profile.industries[0]}`);
    }

    if (profile.tech_stack?.length) {
      const techFocus = determineTechFocus(profile.tech_stack);
      if (techFocus) {
        parts.push(`with expertise in ${techFocus.toLowerCase()}`);
      }
    }

    return parts.join(", ") + ".";
  }, [profile, urlType]);

  if (insights.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-primary/20",
        "bg-gradient-to-r from-primary/5 via-purple-500/5 to-primary/5",
        className
      )}
    >
      {/* Animated shimmer effect */}
      <div className="absolute inset-0 ai-shimmer opacity-30" />

      <div className="relative p-4 sm:p-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <div className="h-8 w-8 rounded-lg ai-gradient flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">AI Analysis</h3>
            <p className="text-xs text-muted-foreground">Personalized insights</p>
          </div>
        </div>

        {/* Summary */}
        <p className="text-sm text-foreground mb-4 leading-relaxed">
          {summary}
        </p>

        {/* Insights grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {insights.map((insight, index) => {
            const Icon = insight.icon;
            return (
              <motion.div
                key={insight.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="bg-background/60 backdrop-blur-sm rounded-xl p-3 border border-border/50"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon className="h-3.5 w-3.5 text-primary" />
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                    {insight.label}
                  </span>
                </div>
                <p className="text-sm font-medium truncate" title={insight.value}>
                  {insight.value}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

function determineProfileType(profile: AIInsightBannerProps["profile"]): string | null {
  const techStack = profile.tech_stack || [];
  const description = (profile.description || "").toLowerCase();
  const goals = profile.goals || [];

  // Check for specific patterns
  if (techStack.some(t => ["solidity", "web3", "ethereum", "blockchain"].includes(t.toLowerCase()))) {
    return "Web3 Developer";
  }
  if (techStack.some(t => ["tensorflow", "pytorch", "ml", "ai", "machine learning"].includes(t.toLowerCase()))) {
    return "AI/ML Developer";
  }
  if (techStack.some(t => ["react native", "flutter", "swift", "kotlin"].includes(t.toLowerCase()))) {
    return "Mobile Developer";
  }
  if (description.includes("startup") || goals.some(g => g.toLowerCase().includes("startup"))) {
    return "Startup Founder";
  }
  if (techStack.some(t => ["react", "vue", "angular", "next.js", "nextjs"].includes(t.toLowerCase()))) {
    return "Frontend Developer";
  }
  if (techStack.some(t => ["python", "java", "go", "rust", "node"].includes(t.toLowerCase()))) {
    return "Full-Stack Developer";
  }
  if (description.includes("research") || description.includes("academic")) {
    return "Researcher";
  }

  return "Developer";
}

function determineTechFocus(techStack: string[]): string | null {
  if (!techStack.length) return null;

  const categories = {
    "Web Development": ["react", "vue", "angular", "next.js", "nextjs", "html", "css", "javascript", "typescript"],
    "AI & Machine Learning": ["tensorflow", "pytorch", "ml", "ai", "machine learning", "scikit", "keras"],
    "Blockchain": ["solidity", "web3", "ethereum", "blockchain", "smart contracts", "hardhat"],
    "Mobile Development": ["react native", "flutter", "swift", "kotlin", "ios", "android"],
    "Cloud & DevOps": ["aws", "gcp", "azure", "docker", "kubernetes", "terraform"],
    "Backend": ["python", "java", "go", "rust", "node", "django", "fastapi", "express"],
  };

  const normalizedStack = techStack.map(t => t.toLowerCase());
  let bestMatch = { category: "", count: 0 };

  for (const [category, keywords] of Object.entries(categories)) {
    const count = keywords.filter(k => normalizedStack.some(s => s.includes(k))).length;
    if (count > bestMatch.count) {
      bestMatch = { category, count };
    }
  }

  return bestMatch.count > 0 ? bestMatch.category : techStack.slice(0, 3).join(", ");
}

function determineOpportunityFit(profile: AIInsightBannerProps["profile"]): string | null {
  const techStack = profile.tech_stack || [];
  const industries = profile.industries || [];
  const goals = profile.goals || [];

  const normalizedStack = techStack.map(t => t.toLowerCase());
  const normalizedIndustries = industries.map(i => i.toLowerCase());
  const normalizedGoals = goals.map(g => g.toLowerCase());

  // Check for specific opportunity fits
  if (normalizedStack.some(t => ["solidity", "web3", "ethereum"].includes(t)) ||
      normalizedIndustries.some(i => i.includes("blockchain") || i.includes("crypto"))) {
    return "Web3 Hackathons";
  }

  if (normalizedStack.some(t => ["tensorflow", "pytorch", "ml"].includes(t)) ||
      normalizedIndustries.some(i => i.includes("ai") || i.includes("machine"))) {
    return "AI Hackathons";
  }

  if (normalizedGoals.some(g => g.includes("funding") || g.includes("investment") || g.includes("grant"))) {
    return "Grant Programs";
  }

  if (normalizedIndustries.some(i => i.includes("health") || i.includes("medical"))) {
    return "Healthcare Innovation";
  }

  if (normalizedIndustries.some(i => i.includes("fintech") || i.includes("finance"))) {
    return "FinTech Challenges";
  }

  if (normalizedGoals.some(g => g.includes("social") || g.includes("impact"))) {
    return "Social Impact Grants";
  }

  return "Tech Hackathons";
}
