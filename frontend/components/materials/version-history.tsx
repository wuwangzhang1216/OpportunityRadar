"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  History,
  Clock,
  ChevronRight,
  RotateCcw,
  GitCompare,
  Eye,
  X,
  Check,
  FileText,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";

interface MaterialVersion {
  id: string;
  version: number;
  content: string;
  created_at: string;
  change_summary?: string;
  is_current?: boolean;
}

interface VersionHistoryProps {
  materialId: string;
  currentVersion: number;
  versions: MaterialVersion[];
  onRestore?: (version: MaterialVersion) => void;
  onCompare?: (v1: MaterialVersion, v2: MaterialVersion) => void;
}

export function VersionHistory({
  materialId,
  currentVersion,
  versions,
  onRestore,
  onCompare,
}: VersionHistoryProps) {
  const [selectedForCompare, setSelectedForCompare] = useState<MaterialVersion | null>(null);
  const [previewVersion, setPreviewVersion] = useState<MaterialVersion | null>(null);

  const handleCompareSelect = (version: MaterialVersion) => {
    if (selectedForCompare) {
      if (selectedForCompare.id === version.id) {
        setSelectedForCompare(null);
      } else {
        onCompare?.(selectedForCompare, version);
        setSelectedForCompare(null);
      }
    } else {
      setSelectedForCompare(version);
    }
  };

  if (versions.length <= 1) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No version history yet</p>
        <p className="text-xs mt-1">Versions are created when you regenerate materials</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Version History</span>
          <Badge variant="secondary" size="sm">
            {versions.length} versions
          </Badge>
        </div>
        {selectedForCompare && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => setSelectedForCompare(null)}
          >
            <X className="h-3 w-3 mr-1" />
            Cancel compare
          </Button>
        )}
      </div>

      <div className="space-y-2">
        {versions.map((version, index) => {
          const isCurrent = version.version === currentVersion;
          const isSelected = selectedForCompare?.id === version.id;

          return (
            <motion.div
              key={version.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <div
                className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                  isCurrent
                    ? "border-primary bg-primary/5"
                    : isSelected
                    ? "border-purple-500 bg-purple-500/5"
                    : "border-border hover:border-muted-foreground/50 hover:bg-secondary/50"
                }`}
              >
                {/* Version indicator */}
                <div className="relative">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      isCurrent
                        ? "bg-primary text-white"
                        : "bg-secondary text-muted-foreground"
                    }`}
                  >
                    v{version.version}
                  </div>
                  {index < versions.length - 1 && (
                    <div className="absolute top-8 left-1/2 w-0.5 h-4 bg-border -translate-x-1/2" />
                  )}
                </div>

                {/* Version info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {isCurrent ? "Current version" : `Version ${version.version}`}
                    </span>
                    {isCurrent && (
                      <Badge variant="secondary" size="sm" className="text-[10px]">
                        <Check className="h-2.5 w-2.5 mr-0.5" />
                        Active
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatRelativeTime(version.created_at)}
                    </span>
                    {version.change_summary && (
                      <span className="text-xs text-muted-foreground">
                        • {version.change_summary}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0"
                    onClick={() => setPreviewVersion(version)}
                    title="Preview"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>

                  {!isCurrent && (
                    <>
                      <Button
                        size="sm"
                        variant={isSelected ? "secondary" : "ghost"}
                        className="h-8 w-8 p-0"
                        onClick={() => handleCompareSelect(version)}
                        title={isSelected ? "Selected for compare" : "Compare"}
                      >
                        <GitCompare className={`h-4 w-4 ${isSelected ? "text-purple-600" : ""}`} />
                      </Button>

                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => onRestore?.(version)}
                        title="Restore this version"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Version Preview Modal */}
      <AnimatePresence>
        {previewVersion && (
          <VersionPreviewModal
            version={previewVersion}
            onClose={() => setPreviewVersion(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function VersionPreviewModal({
  version,
  onClose,
}: {
  version: MaterialVersion;
  onClose: () => void;
}) {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed inset-4 md:inset-10 lg:inset-20 bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-secondary/30">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center">
              <FileText className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Version {version.version}</h3>
              <p className="text-xs text-muted-foreground">
                Created {formatRelativeTime(version.created_at)}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-6">
          <pre className="whitespace-pre-wrap text-sm font-mono">
            {version.content}
          </pre>
        </div>
      </motion.div>
    </>
  );
}

// Version comparison component
interface VersionCompareProps {
  version1: MaterialVersion;
  version2: MaterialVersion;
  onClose: () => void;
}

export function VersionCompare({ version1, version2, onClose }: VersionCompareProps) {
  // Simple diff visualization - in production, use a proper diff library
  const getLineDiff = (content1: string, content2: string) => {
    const lines1 = content1.split("\n");
    const lines2 = content2.split("\n");
    const maxLines = Math.max(lines1.length, lines2.length);

    const diff: Array<{
      line: number;
      left: string;
      right: string;
      status: "same" | "changed" | "added" | "removed";
    }> = [];

    for (let i = 0; i < maxLines; i++) {
      const left = lines1[i] || "";
      const right = lines2[i] || "";

      let status: "same" | "changed" | "added" | "removed" = "same";
      if (left !== right) {
        if (!left) status = "added";
        else if (!right) status = "removed";
        else status = "changed";
      }

      diff.push({ line: i + 1, left, right, status });
    }

    return diff;
  };

  const diff = getLineDiff(version1.content, version2.content);
  const changedLines = diff.filter((d) => d.status !== "same").length;

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed inset-4 md:inset-10 bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-secondary/30">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <GitCompare className="h-5 w-5 text-purple-600" />
              <h3 className="font-semibold">Compare Versions</h3>
            </div>
            <Badge variant="secondary">
              {changedLines} line{changedLines !== 1 ? "s" : ""} changed
            </Badge>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Version labels */}
        <div className="grid grid-cols-2 border-b border-border">
          <div className="px-6 py-2 bg-red-500/5 border-r border-border">
            <span className="text-sm font-medium">Version {version1.version}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {formatRelativeTime(version1.created_at)}
            </span>
          </div>
          <div className="px-6 py-2 bg-green-500/5">
            <span className="text-sm font-medium">Version {version2.version}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {formatRelativeTime(version2.created_at)}
            </span>
          </div>
        </div>

        {/* Diff view */}
        <div className="flex-1 overflow-auto">
          <div className="grid grid-cols-2 text-sm font-mono">
            {diff.map((line) => (
              <div key={line.line} className="contents">
                <div
                  className={`px-4 py-0.5 border-r border-border ${
                    line.status === "removed" || line.status === "changed"
                      ? "bg-red-500/10"
                      : ""
                  }`}
                >
                  <span className="text-muted-foreground w-8 inline-block text-right mr-4">
                    {line.line}
                  </span>
                  <span className={line.status === "removed" ? "text-red-600" : ""}>
                    {line.left}
                  </span>
                </div>
                <div
                  className={`px-4 py-0.5 ${
                    line.status === "added" || line.status === "changed"
                      ? "bg-green-500/10"
                      : ""
                  }`}
                >
                  <span className="text-muted-foreground w-8 inline-block text-right mr-4">
                    {line.line}
                  </span>
                  <span className={line.status === "added" ? "text-green-600" : ""}>
                    {line.right}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </>
  );
}
