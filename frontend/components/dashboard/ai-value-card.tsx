"use client";

import { motion } from "framer-motion";
import {
  Sparkles,
  Clock,
  Target,
  TrendingUp,
  Zap,
  Brain,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface AIValueCardProps {
  matchesCount: number;
  materialsGenerated?: number;
  pipelineItems?: number;
}

export function AIValueCard({
  matchesCount,
  materialsGenerated = 0,
  pipelineItems = 0,
}: AIValueCardProps) {
  // Calculate estimated time saved
  // Average time to manually find and evaluate an opportunity: 30 mins
  // Average time to write materials (README, pitch, etc.): 2 hours each
  const timeSavedMinutes = matchesCount * 30 + materialsGenerated * 120;
  const timeSavedHours = Math.round(timeSavedMinutes / 60);

  // Calculate match quality (assuming AI improves relevance by 2x)
  const matchQualityBoost = matchesCount > 0 ? "2x" : "-";

  const stats = [
    {
      icon: Clock,
      label: "Time Saved",
      value: timeSavedHours > 0 ? `${timeSavedHours}h` : "0h",
      description: "vs manual search",
      color: "text-green-500",
      bgColor: "bg-green-500/10",
    },
    {
      icon: Target,
      label: "Matches Found",
      value: matchesCount.toString(),
      description: "personalized matches",
      color: "text-primary",
      bgColor: "bg-primary/10",
    },
    {
      icon: Brain,
      label: "Match Quality",
      value: matchQualityBoost,
      description: "relevance vs search",
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      icon: Zap,
      label: "Pipeline",
      value: pipelineItems.toString(),
      description: "opportunities tracked",
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    },
  ];

  return (
    <Card variant="ai" className="overflow-hidden relative">
      {/* AI Shimmer Background */}
      <div className="absolute inset-0 ai-shimmer opacity-10" />

      <CardHeader className="relative pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg ai-gradient flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <CardTitle className="text-lg">AI Value Dashboard</CardTitle>
          </div>
          <Badge variant="ai" className="gap-1">
            <TrendingUp className="h-3 w-3" />
            Active
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          See how OpportunityRadar's AI is helping you succeed
        </p>
      </CardHeader>

      <CardContent className="relative pt-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative bg-background/60 backdrop-blur-sm rounded-xl p-3 border border-border/50"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`p-1.5 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </div>
              <motion.p
                className="text-2xl font-bold"
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
              >
                {stat.value}
              </motion.p>
              <p className="text-xs text-muted-foreground mt-0.5 truncate">
                {stat.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Value Proposition */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4 pt-4 border-t border-border/50"
        >
          <div className="flex items-start gap-3 p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple-500/5">
            <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">Your AI Advantage</p>
              <p className="text-xs text-muted-foreground mt-1">
                {timeSavedHours >= 10
                  ? `You've saved over ${timeSavedHours} hours of manual research. Our AI analyzed ${matchesCount} opportunities to find your best matches.`
                  : matchesCount > 0
                    ? `Our AI has analyzed ${matchesCount} opportunities tailored to your profile. Continue building your pipeline for better results.`
                    : "Complete your profile to unlock AI-powered opportunity matching and save hours of manual research."}
              </p>
            </div>
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}
