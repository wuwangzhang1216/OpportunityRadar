"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ChevronRight,
  ChevronDown,
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

const stages = [
  { id: "discovered", label: "Discovered", color: "bg-gray-400", textColor: "text-gray-600" },
  { id: "preparing", label: "Preparing", color: "bg-yellow-500", textColor: "text-yellow-600" },
  { id: "submitted", label: "Submitted", color: "bg-blue-500", textColor: "text-blue-600" },
  { id: "pending", label: "Pending", color: "bg-purple-500", textColor: "text-purple-600" },
  { id: "won", label: "Won", color: "bg-green-500", textColor: "text-green-600" },
  { id: "lost", label: "Lost", color: "bg-red-400", textColor: "text-red-600" },
];

export default function PipelinePage() {
  const queryClient = useQueryClient();
  const [draggedItem, setDraggedItem] = useState<any>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);

  const { data: pipelineData, isLoading } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => apiClient.getPipelines({ limit: 100 }),
  });

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
    pipelineItems.filter((item: any) => item.stage === stageId);

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

    if (draggedItem && draggedItem.stage !== stageId) {
      moveMutation.mutate({
        pipelineId: draggedItem.id,
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pipeline</h1>
          <p className="text-muted-foreground mt-1">
            Track your opportunities from discovery to victory. Drag cards to move between stages.
          </p>
        </div>
        <Link href="/opportunities">
          <Button>Add Opportunity</Button>
        </Link>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {activeStages.map((stage) => {
          const items = getItemsByStage(stage.id);
          const isOver = dragOverStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`flex-shrink-0 w-72 rounded-lg p-4 transition-colors ${
                isOver ? "bg-primary/10 ring-2 ring-primary" : "bg-secondary/50"
              }`}
              onDragOver={(e) => handleDragOver(e, stage.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, stage.id)}
            >
              {/* Column Header */}
              <div className="flex items-center gap-2 mb-4">
                <div className={`w-3 h-3 rounded-full ${stage.color}`} />
                <h3 className="font-medium">{stage.label}</h3>
                <Badge variant="secondary" className="ml-auto">
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
                      key={item.id}
                      item={item}
                      currentStage={stage.id}
                      stages={stages}
                      onMove={(newStage) =>
                        moveMutation.mutate({ pipelineId: item.id, stage: newStage })
                      }
                      onDelete={() => {
                        if (confirm("Are you sure you want to permanently remove this from your pipeline?")) {
                          deleteMutation.mutate(item.id);
                        }
                      }}
                      onArchive={() =>
                        moveMutation.mutate({ pipelineId: item.id, stage: "lost" })
                      }
                      onDragStart={(e) => handleDragStart(e, item)}
                      onDragEnd={handleDragEnd}
                      isDragging={draggedItem?.id === item.id}
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
                  key={item.id}
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
                        moveMutation.mutate({ pipelineId: item.id, stage: "discovered" })
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
                          deleteMutation.mutate(item.id);
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
    </div>
  );
}

function PipelineCard({
  item,
  currentStage,
  stages,
  onMove,
  onDelete,
  onArchive,
  onDragStart,
  onDragEnd,
  isDragging,
}: {
  item: any;
  currentStage: string;
  stages: typeof stages;
  onMove: (stage: string) => void;
  onDelete: () => void;
  onArchive: () => void;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
  isDragging: boolean;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const currentIndex = stages.findIndex((s) => s.id === currentStage);
  const nextStage = stages[currentIndex + 1];
  const canMoveNext = nextStage && nextStage.id !== "lost";

  // Close menu when clicking outside
  const handleClickOutside = (e: MouseEvent) => {
    if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
      setShowMenu(false);
    }
  };

  return (
    <Card
      className={`cursor-grab active:cursor-grabbing transition-all ${
        isDragging ? "opacity-50 scale-95 ring-2 ring-primary" : "hover:shadow-md"
      }`}
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
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
                <Link href={`/generator?batch_id=${item.batch_id}`}>
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
                    onMove("won");
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
                    onArchive();
                    setShowMenu(false);
                  }}
                >
                  <Archive className="h-3 w-3" />
                  Archive (Not pursuing)
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

        <Link href={`/opportunities/${item.batch_id}`}>
          <h4 className="font-medium text-sm mb-2 line-clamp-2 hover:text-primary transition-colors">
            {item.opportunity_title || "Untitled"}
          </h4>
        </Link>

        {item.deadline_at && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-3">
            <Calendar className="h-3 w-3" />
            <span>{formatRelativeTime(item.deadline_at)}</span>
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
