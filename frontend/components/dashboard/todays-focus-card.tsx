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
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

interface Recommendation {
  type: "deadline" | "material" | "opportunity" | "profile";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  actionLabel: string;
  actionUrl: string;
  metadata?: {
    daysLeft?: number;
    opportunityId?: string;
    opportunityTitle?: string;
    materialsReady?: number;
    materialsTotal?: number;
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
    default:
      return Zap;
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
    recommendations.push({
      type: "material",
      priority: "medium",
      title: "Generate Materials",
      description: `Create winning materials for "${itemNeedingMaterials.opportunity_title}"`,
      actionLabel: "Generate Now",
      actionUrl: `/generator?batch_id=${itemNeedingMaterials.opportunity_id}`,
      metadata: {
        opportunityId: itemNeedingMaterials.opportunity_id,
        opportunityTitle: itemNeedingMaterials.opportunity_title,
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
      priority: "low",
      title: `${score}% Match Found`,
      description: topMatch.opportunity_title,
      actionLabel: "View Match",
      actionUrl: `/opportunities/${topMatch.batch_id}`,
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
              <div className={`p-3 rounded-xl ${
                primaryRec.priority === "high"
                  ? "bg-urgency-critical/10"
                  : primaryRec.priority === "medium"
                  ? "bg-urgency-warning/10"
                  : "bg-primary/10"
              }`}>
                {primaryRec.priority === "high" ? (
                  <AlertTriangle className={`h-6 w-6 text-urgency-critical`} />
                ) : (
                  <PrimaryIcon className={`h-6 w-6 ${
                    primaryRec.priority === "medium" ? "text-urgency-warning" : "text-primary"
                  }`} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {primaryRec.metadata?.daysLeft !== undefined && (
                    <Badge variant={getUrgencyVariant(primaryRec.metadata.daysLeft)} size="sm">
                      {primaryRec.metadata.daysLeft === 0
                        ? "Today!"
                        : primaryRec.metadata.daysLeft === 1
                        ? "Tomorrow"
                        : `${primaryRec.metadata.daysLeft} days left`}
                    </Badge>
                  )}
                </div>
                <h4 className="font-semibold text-lg mb-1 truncate">{primaryRec.title}</h4>
                <p className="text-sm text-muted-foreground mb-4">{primaryRec.description}</p>
                <Link href={primaryRec.actionUrl}>
                  <Button className="group">
                    {primaryRec.actionLabel}
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
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
