"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles,
  Clock,
  Target,
  ArrowRight,
  AlertTriangle,
  FileText,
  TrendingUp,
  Zap,
  CheckCircle2,
  Trophy,
  Calendar,
  Rocket,
  ListChecks,
  MessageSquare,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

interface Recommendation {
  type: "deadline" | "material" | "opportunity" | "profile" | "result" | "review";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  actionLabel: string;
  actionUrl: string;
  secondaryAction?: {
    label: string;
    url: string;
  };
  metadata?: {
    daysLeft?: number;
    opportunityId?: string;
    opportunityTitle?: string;
    materialsReady?: number;
    materialsTotal?: number;
    scorePercent?: number;
    status?: string;
  };
}

function getUrgencyVariant(daysLeft: number | undefined): "urgencyCritical" | "urgencyUrgent" | "urgencyWarning" | "urgencySafe" {
  if (daysLeft === undefined) return "urgencySafe";
  if (daysLeft <= 3) return "urgencyCritical";
  if (daysLeft <= 7) return "urgencyUrgent";
  if (daysLeft <= 14) return "urgencyWarning";
  return "urgencySafe";
}

function getRecommendationIcon(type: Recommendation["type"]) {
  switch (type) {
    case "deadline":
      return Clock;
    case "material":
      return FileText;
    case "opportunity":
      return Target;
    case "profile":
      return TrendingUp;
    case "result":
      return Trophy;
    case "review":
      return MessageSquare;
    default:
      return Zap;
  }
}

function getRecommendationColor(type: Recommendation["type"], priority: Recommendation["priority"]) {
  if (priority === "high") return "bg-urgency-critical/10 text-urgency-critical";
  if (priority === "medium") return "bg-urgency-warning/10 text-urgency-warning";

  switch (type) {
    case "opportunity":
      return "bg-primary/10 text-primary";
    case "material":
      return "bg-purple-500/10 text-purple-600";
    case "result":
      return "bg-green-500/10 text-green-600";
    case "review":
      return "bg-orange-500/10 text-orange-600";
    default:
      return "bg-primary/10 text-primary";
  }
}

export function TodaysFocusCard() {
  // Fetch pipeline data to find items with upcoming deadlines
  const { data: pipelineData } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => apiClient.getPipelines({ limit: 100 }),
  });

  // Fetch top matches for new opportunity recommendations
  const { data: matchData } = useQuery({
    queryKey: ["topMatches"],
    queryFn: () => apiClient.getTopMatches(3),
  });

  // Build recommendations based on data
  const recommendations: Recommendation[] = [];

  // Check for items with upcoming deadlines
  const pipelineItems = pipelineData?.items || [];
  const itemsWithDeadlines = pipelineItems
    .filter((item: any) => item.deadline && item.status !== "won" && item.status !== "lost")
    .map((item: any) => {
      const deadline = new Date(item.deadline);
      const now = new Date();
      const daysLeft = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return { ...item, daysLeft };
    })
    .filter((item: any) => item.daysLeft >= 0 && item.daysLeft <= 14)
    .sort((a: any, b: any) => a.daysLeft - b.daysLeft);

  // Add deadline-based recommendation
  if (itemsWithDeadlines.length > 0) {
    const urgentItem = itemsWithDeadlines[0];
    recommendations.push({
      type: "deadline",
      priority: urgentItem.daysLeft <= 3 ? "high" : urgentItem.daysLeft <= 7 ? "medium" : "low",
      title: urgentItem.opportunity_title || "Upcoming Deadline",
      description: urgentItem.daysLeft === 0
        ? "Deadline is today! Make sure everything is ready."
        : urgentItem.daysLeft === 1
        ? "Deadline is tomorrow. Final preparations time!"
        : `${urgentItem.daysLeft} days until deadline. ${urgentItem.status === "discovered" ? "Consider moving to Preparing." : ""}`,
      actionLabel: urgentItem.status === "discovered" ? "Start Preparing" : "View Details",
      actionUrl: `/opportunities/${urgentItem.opportunity_id}`,
      metadata: {
        daysLeft: urgentItem.daysLeft,
        opportunityId: urgentItem.opportunity_id,
        opportunityTitle: urgentItem.opportunity_title,
      },
    });
  }

  // Add material generation recommendation for preparing items
  const preparingItems = pipelineItems.filter((item: any) => item.status === "preparing");
  if (preparingItems.length > 0) {
    const itemNeedingMaterials = preparingItems[0];
    // Calculate days left for preparing item
    let prepDaysLeft = null;
    if (itemNeedingMaterials.deadline) {
      const deadline = new Date(itemNeedingMaterials.deadline);
      prepDaysLeft = Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    }
    recommendations.push({
      type: "material",
      priority: prepDaysLeft !== null && prepDaysLeft <= 7 ? "high" : "medium",
      title: "Continue Preparation",
      description: `Create winning materials for "${itemNeedingMaterials.opportunity_title}"`,
      actionLabel: "Generate Materials",
      actionUrl: `/generator?batch_id=${itemNeedingMaterials.opportunity_id}`,
      secondaryAction: {
        label: "View Details",
        url: `/opportunities/${itemNeedingMaterials.opportunity_id}`,
      },
      metadata: {
        opportunityId: itemNeedingMaterials.opportunity_id,
        opportunityTitle: itemNeedingMaterials.opportunity_title,
        daysLeft: prepDaysLeft || undefined,
      },
    });
  }

  // Check for submitted items that may need result logging (past deadline)
  const submittedItems = pipelineItems.filter((item: any) => item.status === "submitted" || item.status === "pending");
  const itemsNeedingResult = submittedItems.filter((item: any) => {
    if (!item.deadline) return false;
    const deadline = new Date(item.deadline);
    const daysSinceDeadline = Math.ceil((Date.now() - deadline.getTime()) / (1000 * 60 * 60 * 24));
    return daysSinceDeadline > 7; // More than a week past deadline, probably have results
  });

  if (itemsNeedingResult.length > 0) {
    const item = itemsNeedingResult[0];
    recommendations.push({
      type: "result",
      priority: "medium",
      title: "Log Your Result",
      description: `Did you hear back from "${item.opportunity_title}"? Track your outcome to improve future recommendations.`,
      actionLabel: "Won It!",
      actionUrl: `/pipeline?mark_won=${item.id || item._id}`,
      secondaryAction: {
        label: "Didn't Win",
        url: `/pipeline?archive=${item.id || item._id}`,
      },
      metadata: {
        opportunityId: item.opportunity_id,
        opportunityTitle: item.opportunity_title,
        status: item.status,
      },
    });
  }

  // Add new opportunity recommendation
  const matches = matchData?.items || [];
  if (matches.length > 0) {
    const topMatch = matches[0];
    const score = Math.round((topMatch.score || topMatch.overall_score || 0) * 100);
    recommendations.push({
      type: "opportunity",
      priority: score >= 85 ? "medium" : "low",
      title: score >= 85 ? "Excellent Match!" : `${score}% Match Found`,
      description: topMatch.opportunity_title,
      actionLabel: score >= 85 ? "Quick Prep" : "View Match",
      actionUrl: score >= 85 ? `/generator?batch_id=${topMatch.batch_id}` : `/opportunities/${topMatch.batch_id}`,
      secondaryAction: score >= 85 ? {
        label: "View Details",
        url: `/opportunities/${topMatch.batch_id}`,
      } : undefined,
      metadata: {
        scorePercent: score,
        opportunityId: topMatch.batch_id,
      },
    });
  }

  // If no recommendations, show a default
  if (recommendations.length === 0) {
    recommendations.push({
      type: "opportunity",
      priority: "low",
      title: "Discover Opportunities",
      description: "Browse personalized matches to find your next hackathon or grant.",
      actionLabel: "Browse Matches",
      actionUrl: "/opportunities",
    });
  }

  const primaryRec = recommendations[0];
  const secondaryRecs = recommendations.slice(1, 3);
  const PrimaryIcon = getRecommendationIcon(primaryRec.type);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <Card variant="ai" className="overflow-hidden">
        <CardContent className="p-0">
          {/* Header */}
          <div className="flex items-center gap-2 px-6 py-4 border-b border-primary/10 bg-gradient-to-r from-primary/5 to-purple-500/5">
            <div className="h-8 w-8 rounded-lg ai-gradient flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">AI Assistant</h3>
              <p className="text-xs text-muted-foreground">Your recommended next steps</p>
            </div>
            <Badge variant="ai" className="ml-auto">
              <Zap className="h-3 w-3 mr-1" />
              Smart Suggestions
            </Badge>
          </div>

          {/* Primary Recommendation */}
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-xl ${getRecommendationColor(primaryRec.type, primaryRec.priority)}`}>
                {primaryRec.priority === "high" ? (
                  <AlertTriangle className="h-6 w-6" />
                ) : (
                  <PrimaryIcon className="h-6 w-6" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  {primaryRec.metadata?.daysLeft !== undefined && (
                    <Badge variant={getUrgencyVariant(primaryRec.metadata.daysLeft)} size="sm">
                      {primaryRec.metadata.daysLeft === 0
                        ? "Today!"
                        : primaryRec.metadata.daysLeft === 1
                        ? "Tomorrow"
                        : `${primaryRec.metadata.daysLeft} days left`}
                    </Badge>
                  )}
                  {primaryRec.metadata?.scorePercent !== undefined && primaryRec.metadata.scorePercent >= 85 && (
                    <Badge variant="ai" size="sm">
                      <Sparkles className="h-3 w-3 mr-1" />
                      {primaryRec.metadata.scorePercent}% Match
                    </Badge>
                  )}
                  {primaryRec.type === "result" && (
                    <Badge variant="secondary" size="sm">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Track Outcome
                    </Badge>
                  )}
                </div>
                <h4 className="font-semibold text-lg mb-1 truncate">{primaryRec.title}</h4>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{primaryRec.description}</p>
                <div className="flex items-center gap-2 flex-wrap">
                  <Link href={primaryRec.actionUrl}>
                    <Button className="group" size="sm">
                      {primaryRec.type === "result" && <Trophy className="h-4 w-4 mr-1.5" />}
                      {primaryRec.type === "material" && <Sparkles className="h-4 w-4 mr-1.5" />}
                      {primaryRec.type === "opportunity" && primaryRec.metadata?.scorePercent && primaryRec.metadata.scorePercent >= 85 && <Zap className="h-4 w-4 mr-1.5" />}
                      {primaryRec.actionLabel}
                      <ArrowRight className="h-4 w-4 ml-1.5 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                  {primaryRec.secondaryAction && (
                    <Link href={primaryRec.secondaryAction.url}>
                      <Button variant="outline" size="sm">
                        {primaryRec.secondaryAction.label}
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Secondary Recommendations */}
          {secondaryRecs.length > 0 && (
            <div className="px-6 pb-6">
              <div className="border-t border-border pt-4">
                <p className="text-xs font-medium text-muted-foreground mb-3">Also recommended</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {secondaryRecs.map((rec, index) => {
                    const Icon = getRecommendationIcon(rec.type);
                    return (
                      <Link key={index} href={rec.actionUrl}>
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors cursor-pointer group"
                        >
                          <div className="p-2 rounded-lg bg-background">
                            <Icon className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                              {rec.title}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {rec.description}
                            </p>
                          </div>
                          <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                        </motion.div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
