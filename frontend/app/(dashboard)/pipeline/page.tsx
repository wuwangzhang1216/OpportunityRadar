"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ChevronRight,
  MoreHorizontal,
  ExternalLink,
  Trash2,
  Sparkles,
  Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";
import { formatRelativeTime } from "@/lib/utils";
import Link from "next/link";

const stages = [
  { id: "discovered", label: "Discovered", color: "bg-gray-400" },
  { id: "preparing", label: "Preparing", color: "bg-yellow-500" },
  { id: "submitted", label: "Submitted", color: "bg-blue-500" },
  { id: "pending", label: "Pending", color: "bg-purple-500" },
  { id: "won", label: "Won", color: "bg-green-500" },
  { id: "lost", label: "Lost", color: "bg-red-400" },
];

export default function PipelinePage() {
  const queryClient = useQueryClient();

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
    mutationFn: (pipelineId: string) =>
      apiClient.updatePipeline(pipelineId, { stage: "lost" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      queryClient.invalidateQueries({ queryKey: ["pipelineStats"] });
    },
  });

  const pipelineItems = pipelineData?.items || [];

  const getItemsByStage = (stageId: string) =>
    pipelineItems.filter((item: any) => item.stage === stageId);

  const handleMoveNext = (item: any) => {
    const currentIndex = stages.findIndex((s) => s.id === item.stage);
    if (currentIndex < stages.length - 2) {
      // Don't move past 'won'
      moveMutation.mutate({
        pipelineId: item.id,
        stage: stages[currentIndex + 1].id,
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pipeline</h1>
          <p className="text-gray-600 mt-1">
            Track your opportunities from discovery to victory
          </p>
        </div>
        <Link href="/opportunities">
          <Button>Add Opportunity</Button>
        </Link>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.slice(0, -1).map((stage) => {
          // Exclude 'lost' from main view
          const items = getItemsByStage(stage.id);
          return (
            <div
              key={stage.id}
              className="flex-shrink-0 w-72 bg-gray-50 rounded-lg p-4"
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
              <div className="space-y-3">
                {isLoading ? (
                  [...Array(2)].map((_, i) => (
                    <Card key={i} className="animate-pulse">
                      <CardContent className="pt-4">
                        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                        <div className="h-3 bg-gray-100 rounded w-1/2" />
                      </CardContent>
                    </Card>
                  ))
                ) : items.length === 0 ? (
                  <div className="text-center py-8 text-gray-400 text-sm">
                    No items
                  </div>
                ) : (
                  items.map((item: any) => (
                    <PipelineCard
                      key={item.id}
                      item={item}
                      onMoveNext={() => handleMoveNext(item)}
                      onDelete={() => deleteMutation.mutate(item.id)}
                      isLastStage={stage.id === "won"}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Lost items (collapsed) */}
      {getItemsByStage("lost").length > 0 && (
        <Card>
          <CardHeader className="py-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <CardTitle className="text-base">
                Archived ({getItemsByStage("lost").length})
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {getItemsByStage("lost").map((item: any) => (
                <Badge key={item.id} variant="secondary" className="text-xs">
                  {item.opportunity_title}
                </Badge>
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
  onMoveNext,
  onDelete,
  isLastStage,
}: {
  item: any;
  onMoveNext: () => void;
  onDelete: () => void;
  isLastStage: boolean;
}) {
  const [showActions, setShowActions] = useState(false);

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between mb-2">
          <Badge variant="secondary" className="text-xs">
            {item.opportunity_category || "hackathon"}
          </Badge>
          {showActions && (
            <div className="flex gap-1">
              <Link href={`/generator?batch_id=${item.batch_id}`}>
                <Button size="icon" variant="ghost" className="h-6 w-6">
                  <Sparkles className="h-3 w-3" />
                </Button>
              </Link>
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6 text-red-500"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>

        <Link href={`/opportunities/${item.batch_id}`}>
          <h4 className="font-medium text-sm mb-2 line-clamp-2 hover:text-blue-600">
            {item.opportunity_title || "Untitled"}
          </h4>
        </Link>

        {item.deadline_at && (
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-3">
            <Calendar className="h-3 w-3" />
            <span>{formatRelativeTime(item.deadline_at)}</span>
          </div>
        )}

        {item.notes && (
          <p className="text-xs text-gray-600 mb-3 line-clamp-2">{item.notes}</p>
        )}

        {!isLastStage && (
          <Button
            size="sm"
            variant="outline"
            className="w-full text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onMoveNext();
            }}
          >
            Move to next stage
            <ChevronRight className="h-3 w-3 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
