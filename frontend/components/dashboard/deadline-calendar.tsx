"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Calendar,
  Clock,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";
import { apiClient } from "@/services/api-client";

interface DeadlineItem {
  id: string;
  title: string;
  deadline: string;
  status: string;
  opportunityId: string;
  category?: string;
}

interface CalendarDay {
  date: Date;
  isToday: boolean;
  isCurrentMonth: boolean;
  deadlines: DeadlineItem[];
}

function getUrgencyColor(daysLeft: number): string {
  if (daysLeft < 0) return "bg-gray-300";
  if (daysLeft === 0) return "bg-urgency-critical";
  if (daysLeft <= 3) return "bg-urgency-critical";
  if (daysLeft <= 7) return "bg-urgency-urgent";
  if (daysLeft <= 14) return "bg-urgency-warning";
  return "bg-urgency-safe";
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function DeadlineCalendar() {
  const { data: pipelineData } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => apiClient.getPipelines({ limit: 100 }),
  });

  // Build deadline items from pipeline data
  const deadlineItems: DeadlineItem[] = useMemo(() => {
    const items = pipelineData?.items || [];
    return items
      .filter((item: any) => item.deadline && item.status !== "won" && item.status !== "lost")
      .map((item: any) => ({
        id: item.id || item._id,
        title: item.opportunity_title || "Untitled",
        deadline: item.deadline,
        status: item.status,
        opportunityId: item.opportunity_id,
        category: item.opportunity_category,
      }));
  }, [pipelineData]);

  // Get current week's dates
  const currentWeek = useMemo(() => {
    const today = new Date();
    const days: { date: Date; deadlines: DeadlineItem[] }[] = [];

    for (let i = 0; i < 14; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      date.setHours(0, 0, 0, 0);

      const deadlinesOnDay = deadlineItems.filter((item) => {
        const deadlineDate = new Date(item.deadline);
        deadlineDate.setHours(0, 0, 0, 0);
        return deadlineDate.getTime() === date.getTime();
      });

      days.push({ date, deadlines: deadlinesOnDay });
    }

    return days;
  }, [deadlineItems]);

  // Count total conflicts (days with 2+ deadlines)
  const conflictCount = currentWeek.filter((day) => day.deadlines.length >= 2).length;

  // Total deadlines in next 2 weeks
  const totalDeadlines = deadlineItems.filter((item) => {
    const daysLeft = Math.ceil(
      (new Date(item.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );
    return daysLeft >= 0 && daysLeft <= 14;
  }).length;

  if (deadlineItems.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Upcoming Deadlines</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-10 w-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No upcoming deadlines</p>
            <p className="text-xs mt-1">Add opportunities to your pipeline to track them here</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Deadline Timeline</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {conflictCount > 0 && (
              <Badge variant="urgencyWarning" size="sm">
                <AlertTriangle className="h-3 w-3 mr-1" />
                {conflictCount} conflict{conflictCount > 1 ? "s" : ""}
              </Badge>
            )}
            <Badge variant="secondary" size="sm">
              {totalDeadlines} upcoming
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Timeline View */}
        <div className="relative">
          {/* Time axis */}
          <div className="flex items-center gap-1 mb-3 overflow-x-auto pb-2 scrollbar-modern">
            {currentWeek.map((day, index) => {
              const isToday = index === 0;
              const hasDeadlines = day.deadlines.length > 0;
              const hasConflict = day.deadlines.length >= 2;
              const daysFromNow = index;

              return (
                <Tooltip
                  key={index}
                  content={
                    <div className="space-y-1">
                      <p className="font-medium">{formatDate(day.date)}</p>
                      {day.deadlines.length > 0 ? (
                        <ul className="text-xs space-y-1">
                          {day.deadlines.map((d) => (
                            <li key={d.id} className="flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-current" />
                              {d.title}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">No deadlines</p>
                      )}
                    </div>
                  }
                  side="top"
                >
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                    className={`flex flex-col items-center min-w-[40px] p-2 rounded-lg cursor-pointer transition-all ${
                      isToday
                        ? "bg-primary text-white"
                        : hasConflict
                        ? "bg-urgency-warning/20 hover:bg-urgency-warning/30"
                        : hasDeadlines
                        ? "bg-primary/10 hover:bg-primary/20"
                        : "hover:bg-secondary"
                    }`}
                  >
                    <span
                      className={`text-[10px] font-medium ${
                        isToday ? "text-white/80" : "text-muted-foreground"
                      }`}
                    >
                      {day.date.toLocaleDateString("en-US", { weekday: "short" }).slice(0, 2)}
                    </span>
                    <span
                      className={`text-sm font-bold ${
                        isToday ? "text-white" : hasDeadlines ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      {day.date.getDate()}
                    </span>
                    {hasDeadlines && (
                      <div className="flex gap-0.5 mt-1">
                        {day.deadlines.slice(0, 3).map((_, i) => (
                          <div
                            key={i}
                            className={`w-1.5 h-1.5 rounded-full ${
                              isToday ? "bg-white" : getUrgencyColor(daysFromNow)
                            }`}
                          />
                        ))}
                        {day.deadlines.length > 3 && (
                          <span className={`text-[8px] ${isToday ? "text-white" : "text-muted-foreground"}`}>
                            +{day.deadlines.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </motion.div>
                </Tooltip>
              );
            })}
          </div>

          {/* Deadline list for next 7 days */}
          <div className="space-y-2 mt-4">
            <p className="text-xs font-medium text-muted-foreground">Coming up</p>
            {deadlineItems
              .filter((item) => {
                const daysLeft = Math.ceil(
                  (new Date(item.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
                );
                return daysLeft >= 0 && daysLeft <= 7;
              })
              .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime())
              .slice(0, 5)
              .map((item, index) => {
                const daysLeft = Math.ceil(
                  (new Date(item.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
                );
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Link href={`/opportunities/${item.opportunityId}`}>
                      <div className="flex items-center justify-between p-2 rounded-lg hover:bg-secondary/50 transition-colors group">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <div
                            className={`w-2 h-2 rounded-full flex-shrink-0 ${getUrgencyColor(daysLeft)}`}
                          />
                          <span className="text-sm truncate group-hover:text-primary transition-colors">
                            {item.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              daysLeft <= 3
                                ? "urgencyCritical"
                                : daysLeft <= 7
                                ? "urgencyWarning"
                                : "secondary"
                            }
                            size="sm"
                          >
                            {daysLeft === 0
                              ? "Today"
                              : daysLeft === 1
                              ? "Tomorrow"
                              : `${daysLeft}d`}
                          </Badge>
                          <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                );
              })}
          </div>
        </div>

        {/* Workload indicator */}
        {totalDeadlines > 0 && (
          <div className="pt-3 border-t border-border">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>2-week workload</span>
              <span>{totalDeadlines} deadline{totalDeadlines > 1 ? "s" : ""}</span>
            </div>
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(totalDeadlines * 15, 100)}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className={`h-full rounded-full ${
                  totalDeadlines >= 6
                    ? "bg-urgency-critical"
                    : totalDeadlines >= 4
                    ? "bg-urgency-warning"
                    : "bg-primary"
                }`}
              />
            </div>
            {totalDeadlines >= 4 && (
              <p className="text-xs text-urgency-warning mt-2 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Heavy workload ahead. Consider prioritizing.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
