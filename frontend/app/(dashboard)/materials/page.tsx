"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  FileText,
  Mic,
  PlayCircle,
  HelpCircle,
  Copy,
  Check,
  Trash2,
  ExternalLink,
  Sparkles,
  Clock,
  Star,
  StarOff,
  ChevronDown,
  ChevronUp,
  Plus,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";
import { formatRelativeTime } from "@/lib/utils";

const materialTypeInfo: Record<string, { icon: any; label: string; color: string }> = {
  readme: { icon: FileText, label: "README", color: "bg-primary" },
  pitch_1min: { icon: Mic, label: "1-min Pitch", color: "bg-purple-500" },
  pitch_3min: { icon: Mic, label: "3-min Pitch", color: "bg-purple-500" },
  pitch_5min: { icon: Mic, label: "5-min Pitch", color: "bg-purple-500" },
  demo_script: { icon: PlayCircle, label: "Demo Script", color: "bg-green-500" },
  qa_pred: { icon: HelpCircle, label: "Q&A Prep", color: "bg-orange-500" },
};

export default function MaterialsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["materials"],
    queryFn: () => apiClient.getMaterials({}),
  });

  const materials = data?.items || data || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">My Materials</h1>
          <p className="text-muted-foreground mt-1">
            View and manage your AI-generated hackathon materials
          </p>
        </div>
        <Link href="/generator">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Generate New
          </Button>
        </Link>
      </div>

      {/* Materials List */}
      {isLoading ? (
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-4 bg-secondary rounded w-1/4 mb-4" />
                <div className="h-24 bg-secondary/50 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : materials.length > 0 ? (
        <div className="grid gap-4">
          {materials.map((material: any) => (
            <MaterialCard key={material.id || material._id} material={material} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="h-16 w-16 mx-auto bg-secondary rounded-full flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground">No materials yet</h3>
            <p className="text-muted-foreground mt-1 mb-4">
              Generate your first hackathon materials with AI
            </p>
            <Link href="/generator">
              <Button>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Materials
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MaterialCard({ material }: { material: any }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const materialId = material.id || material._id;
  const typeInfo = materialTypeInfo[material.material_type] || {
    icon: FileText,
    label: material.material_type,
    color: "bg-gray-500",
  };
  const Icon = typeInfo.icon;

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteMaterial(materialId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials"] });
    },
  });

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(material.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border bg-secondary/30 py-4">
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-xl ${typeInfo.color} flex items-center justify-center`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base">{material.title || typeInfo.label}</CardTitle>
              <Badge variant="secondary" className="text-xs">
                {typeInfo.label}
              </Badge>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatRelativeTime(material.created_at)}
              </span>
              {material.opportunity_title && (
                <span className="flex items-center gap-1">
                  For: {material.opportunity_title}
                </span>
              )}
              {material.version > 1 && (
                <Badge variant="outline" className="text-xs">
                  v{material.version}
                </Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={copyToClipboard}>
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-1 text-green-600" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="text-red-500 hover:text-red-600 hover:bg-red-50"
            onClick={() => {
              if (confirm("Are you sure you want to delete this material?")) {
                deleteMutation.mutate();
              }
            }}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="p-0">
          <pre className="whitespace-pre-wrap text-sm p-6 overflow-x-auto max-h-[500px] bg-secondary/10 scrollbar-modern">
            {material.content}
          </pre>
        </CardContent>
      )}

      {!expanded && (
        <CardContent className="py-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {material.content?.substring(0, 200)}...
          </p>
          <Button
            variant="link"
            size="sm"
            className="px-0 mt-1"
            onClick={() => setExpanded(true)}
          >
            Show full content
          </Button>
        </CardContent>
      )}
    </Card>
  );
}
