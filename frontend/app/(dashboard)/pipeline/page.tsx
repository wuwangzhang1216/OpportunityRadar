"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Trash2,
  Sparkles,
  Calendar,
  MoreVertical,
  ArrowRight,
  Trophy,
  XCircle,
  Archive,
  RotateCcw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";
import { formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import { Tooltip } from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { ResultFeedbackModal, ResultFeedback } from "@/components/pipeline/result-feedback-modal";
import { pipelineLogger } from "@/lib/logger";

interface Stage {
  id: string;
  label: string;
  color: string;
  textColor: string;
  description: string;
  tips: string[];
}

const stages: Stage[] = [
  {
    id: "discovered",
    label: "Discovered",
    color: "bg-gray-400",
    textColor: "text-gray-600",
    description: "Opportunities you've found and are considering",
    tips: ["Review eligibility criteria", "Check deadlines", "Add to pipeline from Matches page"],
  },
  {
    id: "preparing",
    label: "Preparing",
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
    description: "Actively working on application materials",
    tips: ["Use AI Generator for materials", "Prepare demo if needed", "Review submission requirements"],
  },
  {
    id: "submitted",
    label: "Submitted",
    color: "bg-blue-500",
    textColor: "text-blue-600",
    description: "Application has been submitted",
    tips: ["Save confirmation details", "Note expected response timeline", "Prepare for follow-up"],
  },
  {
    id: "pending",
    label: "Pending",
    color: "bg-purple-500",
    textColor: "text-purple-600",
    description: "Awaiting results or next stage",
    tips: ["Monitor for updates", "Prepare presentation if advancing", "Keep materials ready"],
  },
  {
    id: "won",
    label: "Won",
    color: "bg-green-500",
    textColor: "text-green-600",
    description: "Congratulations! You succeeded",
    tips: ["Celebrate your win! 🎉", "Document lessons learned", "Share your experience"],
  },
  {
    id: "lost",
    label: "Lost",
    color: "bg-red-400",
    textColor: "text-red-600",
    description: "Archived or unsuccessful attempts",
    tips: ["Review feedback if provided", "Learn for next time", "Materials can be reused"],
  },
];

// Urgency levels for deadline visualization
type UrgencyLevel = "safe" | "warning" | "urgent" | "critical" | "expired" | null;

interface DeadlineUrgency {
  level: UrgencyLevel;
  daysLeft: number | null;
  label: string;
  borderColor: string;
  bgColor: string;
  textColor: string;
}

function getDeadlineUrgency(deadline: string | undefined): DeadlineUrgency {
  if (!deadline) {
    return {
      level: null,
      daysLeft: null,
      label: "",
      borderColor: "",
      bgColor: "",
      textColor: "text-muted-foreground",
    };
  }

  const deadlineDate = new Date(deadline);
  const now = new Date();
  const diffTime = deadlineDate.getTime() - now.getTime();
  const daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (daysLeft < 0) {
    return {
      level: "expired",
      daysLeft,
      label: "Expired",
      borderColor: "border-l-urgency-expired",
      bgColor: "bg-urgency-expired/5",
      textColor: "text-urgency-expired",
    };
  }
  if (daysLeft === 0) {
    return {
      level: "critical",
      daysLeft: 0,
      label: "Today!",
      borderColor: "border-l-urgency-critical",
      bgColor: "bg-urgency-critical/5",
      textColor: "text-urgency-critical",
    };
  }
  if (daysLeft <= 3) {
    return {
      level: "critical",
      daysLeft,
      label: `${daysLeft}d left`,
      borderColor: "border-l-urgency-critical",
      bgColor: "bg-urgency-critical/5",
      textColor: "text-urgency-critical",
    };
  }
  if (daysLeft <= 7) {
    return {
      level: "urgent",
      daysLeft,
      label: `${daysLeft}d left`,
      borderColor: "border-l-urgency-urgent",
      bgColor: "bg-urgency-urgent/5",
      textColor: "text-urgency-urgent",
    };
  }
  if (daysLeft <= 14) {
    return {
      level: "warning",
      daysLeft,
      label: `${daysLeft}d left`,
      borderColor: "border-l-urgency-warning",
      bgColor: "bg-urgency-warning/5",
      textColor: "text-urgency-warning",
    };
  }
  return {
    level: "safe",
    daysLeft,
    label: `${daysLeft}d left`,
    borderColor: "border-l-urgency-safe",
    bgColor: "",
    textColor: "text-urgency-safe",
  };
}

export default function PipelinePage() {
  const queryClient = useQueryClient();
  const [draggedItem, setDraggedItem] = useState<any>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);
  const [mobileStageIndex, setMobileStageIndex] = useState(0);
  const [feedbackItem, setFeedbackItem] = useState<{ item: any; outcome: "won" | "lost" | "withdrew" } | null>(null);

  const { data: pipelineData, isLoading, error } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => apiClient.getPipelines({ limit: 100 }),
  });

  // Debug logging (only in development)
  pipelineLogger.debug("Pipeline data:", pipelineData);
  pipelineLogger.debug("Pipeline items:", pipelineData?.items);
  pipelineLogger.debug("isLoading:", isLoading);
  if (error) pipelineLogger.error("Pipeline error:", error);

  const moveMutation = useMutation({
    mutationFn: ({
      pipelineId,
      stage,
    }: {
      pipelineId: string;
      stage: string;
    }) => apiClient.movePipelineStage(pipelineId, stage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      queryClient.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (pipelineId: string) => apiClient.deletePipeline(pipelineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      queryClient.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });

  const pipelineItems = pipelineData?.items || [];

  const getItemsByStage = (stageId: string) =>
    pipelineItems.filter((item: any) => item.status === stageId);

  const handleDragStart = (e: React.DragEvent, item: any) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverStage(stageId);
  };

  const handleDragLeave = () => {
    setDragOverStage(null);
  };

  const handleDrop = (e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    setDragOverStage(null);

    if (draggedItem && draggedItem.status !== stageId) {
      moveMutation.mutate({
        pipelineId: draggedItem.id || draggedItem._id,
        stage: stageId,
      });
    }
    setDraggedItem(null);
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setDragOverStage(null);
  };

  const activeStages = stages.slice(0, -1); // Exclude 'lost' from main view
  const currentMobileStage = activeStages[mobileStageIndex];

  const goToPrevStage = () => {
    setMobileStageIndex((prev) => Math.max(0, prev - 1));
  };

  const goToNextStage = () => {
    setMobileStageIndex((prev) => Math.min(activeStages.length - 1, prev + 1));
  };

  const handleMarkOutcome = (item: any, outcome: "won" | "lost" | "withdrew") => {
    setFeedbackItem({ item, outcome });
  };

  const handleFeedbackSubmit = async (feedback: ResultFeedback) => {
    if (!feedbackItem) return;

    const pipelineId = feedbackItem.item.id || feedbackItem.item._id;
    const targetStage = feedback.outcome === "won" ? "won" : "lost";

    // Move to appropriate stage
    await moveMutation.mutateAsync({ pipelineId, stage: targetStage });

    // In production, also save the feedback to the backend
    pipelineLogger.info("Feedback submitted:", { pipelineId, feedback });

    // Close modal
    setFeedbackItem(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Pipeline</h1>
          <p className="text-muted-foreground mt-1 text-sm md:text-base hidden sm:block">
            Track your opportunities from discovery to victory.
          </p>
        </div>
        <Link href="/opportunities">
          <Button size="sm" className="md:size-default">Add</Button>
        </Link>
      </div>

      {/* Mobile Stage Selector */}
      <div className="md:hidden">
        <div className="flex items-center justify-between bg-secondary/50 rounded-xl p-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={goToPrevStage}
            disabled={mobileStageIndex === 0}
            className="h-10 w-10"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>

          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-2">
              <div className={`w-3 h-3 rounded-full ${currentMobileStage?.color}`} />
              <span className="font-semibold">{currentMobileStage?.label}</span>
              <Tooltip
                content={
                  <div className="space-y-1">
                    <p className="text-muted-foreground text-xs">{currentMobileStage?.description}</p>
                  </div>
                }
                side="bottom"
              >
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
              </Tooltip>
              <Badge variant="secondary" size="sm">
                {getItemsByStage(currentMobileStage?.id || "").length}
              </Badge>
            </div>
            <div className="flex items-center justify-center gap-1 mt-1">
              {activeStages.map((stage, idx) => (
                <button
                  key={stage.id}
                  onClick={() => setMobileStageIndex(idx)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    idx === mobileStageIndex ? stage.color : "bg-muted-foreground/30"
                  }`}
                />
              ))}
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={goToNextStage}
            disabled={mobileStageIndex === activeStages.length - 1}
            className="h-10 w-10"
          >
            <ChevronRight className="h-5 w-5" />
          </Button>
        </div>

        {/* Mobile Card List */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentMobileStage?.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="mt-4 space-y-3"
          >
            {isLoading ? (
              [...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="pt-4">
                    <div className="h-4 bg-secondary rounded w-3/4 mb-2" />
                    <div className="h-3 bg-secondary/50 rounded w-1/2" />
                  </CardContent>
                </Card>
              ))
            ) : getItemsByStage(currentMobileStage?.id || "").length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border-2 border-dashed border-border rounded-xl">
                <p className="text-sm">No opportunities in this stage</p>
                <p className="text-xs mt-1">Add from Opportunities page</p>
              </div>
            ) : (
              getItemsByStage(currentMobileStage?.id || "").map((item: any) => (
                <PipelineCard
                  key={item.id || item._id}
                  item={item}
                  currentStage={currentMobileStage?.id || ""}
                  stages={stages}
                  onMove={(newStage) =>
                    moveMutation.mutate({ pipelineId: item.id || item._id, stage: newStage })
                  }
                  onDelete={() => {
                    if (confirm("Remove from pipeline?")) {
                      deleteMutation.mutate(item.id || item._id);
                    }
                  }}
                  onMarkWon={() => handleMarkOutcome(item, "won")}
                  onMarkLost={() => handleMarkOutcome(item, "lost")}
                  onDragStart={(e) => handleDragStart(e, item)}
                  onDragEnd={handleDragEnd}
                  isDragging={false}
                  isMobile={true}
                />
              ))
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Desktop Kanban Board */}
      <div className="hidden md:grid grid-cols-5 gap-3 min-w-0">
        {activeStages.map((stage) => {
          const items = getItemsByStage(stage.id);
          const isOver = dragOverStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`min-w-0 rounded-lg p-3 transition-colors ${
                isOver ? "bg-primary/10 ring-2 ring-primary" : "bg-secondary/50"
              }`}
              onDragOver={(e) => handleDragOver(e, stage.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, stage.id)}
            >
              {/* Column Header */}
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${stage.color}`} />
                <h3 className="font-medium text-sm truncate">{stage.label}</h3>
                <Tooltip
                  content={
                    <div className="space-y-2">
                      <p className="font-medium">{stage.label}</p>
                      <p className="text-muted-foreground">{stage.description}</p>
                      {stage.tips.length > 0 && (
                        <div className="pt-2 border-t border-border">
                          <p className="text-xs font-medium text-muted-foreground mb-1">Tips:</p>
                          <ul className="text-xs space-y-0.5">
                            {stage.tips.map((tip, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-primary">•</span>
                                <span>{tip}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  }
                  side="top"
                >
                  <HelpCircle className="h-3.5 w-3.5 text-muted-foreground hover:text-primary cursor-help transition-colors" />
                </Tooltip>
                <Badge variant="secondary" className="ml-auto flex-shrink-0 text-xs">
                  {items.length}
                </Badge>
              </div>

              {/* Cards */}
              <div className="space-y-3 min-h-[100px]">
                {isLoading ? (
                  [...Array(2)].map((_, i) => (
                    <Card key={i} className="animate-pulse">
                      <CardContent className="pt-4">
                        <div className="h-4 bg-secondary rounded w-3/4 mb-2" />
                        <div className="h-3 bg-secondary/50 rounded w-1/2" />
                      </CardContent>
                    </Card>
                  ))
                ) : items.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed border-border rounded-lg">
                    {isOver ? "Drop here" : "No items"}
                  </div>
                ) : (
                  items.map((item: any) => (
                    <PipelineCard
                      key={item.id || item._id}
                      item={item}
                      currentStage={stage.id}
                      stages={stages}
                      onMove={(newStage) =>
                        moveMutation.mutate({ pipelineId: item.id || item._id, stage: newStage })
                      }
                      onDelete={() => {
                        if (confirm("Are you sure you want to permanently remove this from your pipeline?")) {
                          deleteMutation.mutate(item.id || item._id);
                        }
                      }}
                      onMarkWon={() => handleMarkOutcome(item, "won")}
                      onMarkLost={() => handleMarkOutcome(item, "lost")}
                      onDragStart={(e) => handleDragStart(e, item)}
                      onDragEnd={handleDragEnd}
                      isDragging={(draggedItem?.id || draggedItem?._id) === (item.id || item._id)}
                      isMobile={false}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Archived (Lost) items */}
      {getItemsByStage("lost").length > 0 && (
        <Card>
          <CardHeader className="py-3">
            <div className="flex items-center gap-2">
              <Archive className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">
                Archived ({getItemsByStage("lost").length})
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
              {getItemsByStage("lost").map((item: any) => (
                <div
                  key={item.id || item._id}
                  className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.opportunity_title}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.opportunity_category}
                    </p>
                  </div>
                  <div className="flex gap-1 ml-2">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7"
                      onClick={() =>
                        moveMutation.mutate({ pipelineId: item.id || item._id, stage: "discovered" })
                      }
                      title="Restore to Discovered"
                    >
                      <RotateCcw className="h-3 w-3" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-red-500 hover:text-red-600"
                      onClick={() => {
                        if (confirm("Permanently delete this item?")) {
                          deleteMutation.mutate(item.id || item._id);
                        }
                      }}
                      title="Delete permanently"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Result Feedback Modal */}
      <AnimatePresence>
        {feedbackItem && (
          <ResultFeedbackModal
            isOpen={true}
            onClose={() => setFeedbackItem(null)}
            onSubmit={handleFeedbackSubmit}
            opportunityTitle={feedbackItem.item.opportunity_title || "Untitled"}
            initialOutcome={feedbackItem.outcome}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function PipelineCard({
  item,
  currentStage,
  stages: stagesParam,
  onMove,
  onDelete,
  onMarkWon,
  onMarkLost,
  onDragStart,
  onDragEnd,
  isDragging,
  isMobile = false,
}: {
  item: any;
  currentStage: string;
  stages: Stage[];
  onMove: (stage: string) => void;
  onDelete: () => void;
  onMarkWon: () => void;
  onMarkLost: () => void;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
  isDragging: boolean;
  isMobile?: boolean;
}) {
  // Use the passed stages parameter
  const stages = stagesParam;
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const currentIndex = stages.findIndex((s) => s.id === currentStage);
  const nextStage = stages[currentIndex + 1];
  const canMoveNext = nextStage && nextStage.id !== "lost";

  // Get deadline urgency for color coding
  const urgency = getDeadlineUrgency(item.deadline);

  // Close menu when clicking outside
  const handleClickOutside = (e: MouseEvent) => {
    if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
      setShowMenu(false);
    }
  };

  return (
    <Card
      className={`transition-all border-l-4 ${
        urgency.borderColor || "border-l-transparent"
      } ${urgency.bgColor} ${
        isDragging ? "opacity-50 scale-95 ring-2 ring-primary" : "hover:shadow-md"
      } ${urgency.level === "critical" ? "animate-urgency-pulse" : ""} ${
        urgency.level === "urgent" ? "animate-urgency-glow" : ""
      } ${urgency.level === "warning" ? "animate-urgency-subtle" : ""} ${
        !isMobile ? "cursor-grab active:cursor-grabbing" : ""
      }`}
      draggable={!isMobile}
      onDragStart={!isMobile ? onDragStart : undefined}
      onDragEnd={!isMobile ? onDragEnd : undefined}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between mb-2">
          <Badge variant="secondary" className="text-xs">
            {item.opportunity_category || "hackathon"}
          </Badge>

          {/* Action menu */}
          <div className="relative" ref={menuRef}>
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
            >
              <MoreVertical className="h-3 w-3" />
            </Button>

            {showMenu && (
              <div className="absolute right-0 top-7 z-10 w-48 bg-popover border border-border rounded-lg shadow-lg py-1">
                {/* Move to stage options */}
                <div className="px-2 py-1 text-xs font-medium text-muted-foreground">
                  Move to stage
                </div>
                {stages.slice(0, -1).map((stage) => (
                  stage.id !== currentStage && (
                    <button
                      key={stage.id}
                      className="w-full px-3 py-1.5 text-sm text-left hover:bg-secondary flex items-center gap-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        onMove(stage.id);
                        setShowMenu(false);
                      }}
                    >
                      <div className={`w-2 h-2 rounded-full ${stage.color}`} />
                      {stage.label}
                    </button>
                  )
                ))}

                <div className="border-t border-border my-1" />

                {/* Quick actions */}
                <Link href={`/generator?batch_id=${item.opportunity_id}`}>
                  <button
                    className="w-full px-3 py-1.5 text-sm text-left hover:bg-secondary flex items-center gap-2"
                    onClick={() => setShowMenu(false)}
                  >
                    <Sparkles className="h-3 w-3" />
                    Generate Materials
                  </button>
                </Link>

                <div className="border-t border-border my-1" />

                {/* Mark as Won/Lost */}
                <button
                  className="w-full px-3 py-1.5 text-sm text-left hover:bg-secondary flex items-center gap-2 text-green-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onMarkWon();
                    setShowMenu(false);
                  }}
                >
                  <Trophy className="h-3 w-3" />
                  Mark as Won
                </button>
                <button
                  className="w-full px-3 py-1.5 text-sm text-left hover:bg-secondary flex items-center gap-2 text-orange-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onMarkLost();
                    setShowMenu(false);
                  }}
                >
                  <Archive className="h-3 w-3" />
                  Archive / Didn't Win
                </button>

                <div className="border-t border-border my-1" />

                <button
                  className="w-full px-3 py-1.5 text-sm text-left hover:bg-secondary flex items-center gap-2 text-red-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                    setShowMenu(false);
                  }}
                >
                  <Trash2 className="h-3 w-3" />
                  Delete permanently
                </button>
              </div>
            )}
          </div>
        </div>

        <Link href={`/opportunities/${item.opportunity_id}`}>
          <h4 className="font-medium text-sm mb-2 line-clamp-2 hover:text-primary transition-colors">
            {item.opportunity_title || "Untitled"}
          </h4>
        </Link>

        {item.deadline && (
          <div className={`flex items-center gap-1 text-xs mb-3 ${urgency.textColor}`}>
            <Calendar className="h-3 w-3" />
            <span className="font-medium">{urgency.label}</span>
            {urgency.level === "critical" && (
              <span className="ml-1 px-1.5 py-0.5 bg-urgency-critical/10 rounded text-urgency-critical text-[10px] font-semibold">
                URGENT
              </span>
            )}
          </div>
        )}

        {item.notes && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{item.notes}</p>
        )}

        {/* Quick move button */}
        {canMoveNext && (
          <Button
            size="sm"
            variant="outline"
            className="w-full text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onMove(nextStage.id);
            }}
          >
            Move to {nextStage.label}
            <ChevronRight className="h-3 w-3 ml-1" />
          </Button>
        )}

        {currentStage === "won" && (
          <div className="flex items-center justify-center gap-1 text-green-600 text-sm font-medium">
            <Trophy className="h-4 w-4" />
            Victory!
          </div>
        )}
      </CardContent>
    </Card>
  );
}
