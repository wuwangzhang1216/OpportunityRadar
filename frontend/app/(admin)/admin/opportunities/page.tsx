"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Plus,
  Upload,
  Trash2,
  Edit,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  X,
  FileJson,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";

const CATEGORIES = ["all", "hackathon", "grant", "bounty", "accelerator", "competition"];
const PAGE_SIZE = 20;

const categoryColors: Record<string, string> = {
  hackathon: "bg-purple-100 text-purple-700",
  grant: "bg-green-100 text-green-700",
  bounty: "bg-orange-100 text-orange-700",
  accelerator: "bg-blue-100 text-blue-700",
  competition: "bg-pink-100 text-pink-700",
};

interface Opportunity {
  id: string;
  title: string;
  category: string;
  opportunity_type?: string;
  host_name?: string;
  deadline?: string;
  prize_pool?: string;
  is_active: boolean;
  source?: string;
  source_url?: string;
  location_city?: string;
  created_at?: string;
}

export default function AdminOpportunities() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(0);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingOpportunity, setEditingOpportunity] = useState<Opportunity | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  // Query
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["admin-opportunities", search, category, page],
    queryFn: () =>
      apiClient.getAdminOpportunities({
        search: search || undefined,
        category: category === "all" ? undefined : category,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
  });

  const opportunities: Opportunity[] = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Mutations
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      apiClient.updateAdminOpportunity(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-opportunities"] });
      setEditingOpportunity(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteAdminOpportunity(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-opportunities"] });
    },
  });

  const bulkMutation = useMutation({
    mutationFn: ({ action, ids }: { action: "activate" | "deactivate" | "delete"; ids: string[] }) =>
      apiClient.bulkActionOpportunities(action, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-opportunities"] });
      setSelectedIds([]);
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => apiClient.importOpportunities(file),
    onSuccess: (result) => {
      setImportResult(result);
      queryClient.invalidateQueries({ queryKey: ["admin-opportunities"] });
    },
    onError: (error: any) => {
      setImportResult({ error: error.response?.data?.detail || "Import failed" });
    },
  });

  // Handlers
  const handleSelectAll = () => {
    if (selectedIds.length === opportunities.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(opportunities.map((o) => o.id));
    }
  };

  const handleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Opportunities</h1>
          <p className="text-muted-foreground">Manage opportunity data</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowImportModal(true)}
          >
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button className="bg-orange-500 hover:bg-orange-600" disabled>
            <Plus className="h-4 w-4 mr-2" />
            Add New
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search opportunities..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {CATEGORIES.map((cat) => (
                <Button
                  key={cat}
                  variant={category === cat ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setCategory(cat);
                    setPage(0);
                  }}
                  className={category === cat ? "bg-orange-500 hover:bg-orange-600" : ""}
                >
                  {cat === "all" ? "All" : cat.charAt(0).toUpperCase() + cat.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      <AnimatePresence>
        {selectedIds.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="border-orange-500">
              <CardContent className="py-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {selectedIds.length} selected
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => bulkMutation.mutate({ action: "activate", ids: selectedIds })}
                      disabled={bulkMutation.isPending}
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Activate
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => bulkMutation.mutate({ action: "deactivate", ids: selectedIds })}
                      disabled={bulkMutation.isPending}
                    >
                      <XCircle className="h-4 w-4 mr-1" />
                      Deactivate
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => bulkMutation.mutate({ action: "delete", ids: selectedIds })}
                      disabled={bulkMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-secondary/50">
                  <th className="p-4 text-left">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === opportunities.length && opportunities.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300"
                    />
                  </th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Title</th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Type</th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Location</th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Created</th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Status</th>
                  <th className="p-4 text-left text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b">
                      <td colSpan={7} className="p-4">
                        <div className="h-8 bg-secondary animate-pulse rounded" />
                      </td>
                    </tr>
                  ))
                ) : opportunities.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      No opportunities found
                    </td>
                  </tr>
                ) : (
                  opportunities.map((opp) => (
                    <tr
                      key={opp.id}
                      className="border-b hover:bg-secondary/30 transition-colors"
                    >
                      <td className="p-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(opp.id)}
                          onChange={() => handleSelect(opp.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="p-4">
                        <div className="max-w-xs truncate font-medium">{opp.title}</div>
                        {opp.source_url && (
                          <div className="text-xs text-muted-foreground truncate max-w-xs">{opp.source_url}</div>
                        )}
                      </td>
                      <td className="p-4">
                        <Badge className={opp.opportunity_type ? categoryColors[opp.opportunity_type] || "bg-gray-100 text-gray-700" : "bg-gray-100 text-gray-700"}>
                          {opp.opportunity_type || "-"}
                        </Badge>
                      </td>
                      <td className="p-4 text-sm">{opp.location_city || "-"}</td>
                      <td className="p-4 text-sm">{formatDate(opp.created_at)}</td>
                      <td className="p-4">
                        <Badge variant={opp.is_active ? "default" : "secondary"}>
                          {opp.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingOpportunity(opp)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => {
                              if (confirm("Delete this opportunity?")) {
                                deleteMutation.mutate(opp.id);
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between p-4 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {page * PAGE_SIZE + 1}-{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0 || isFetching}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="flex items-center px-3 text-sm">
                Page {page + 1} of {totalPages || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1 || isFetching}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <AnimatePresence>
        {editingOpportunity && (
          <EditModal
            opportunity={editingOpportunity}
            onClose={() => setEditingOpportunity(null)}
            onSave={(data) => updateMutation.mutate({ id: editingOpportunity.id, data })}
            isLoading={updateMutation.isPending}
          />
        )}
      </AnimatePresence>

      {/* Import Modal */}
      <AnimatePresence>
        {showImportModal && (
          <ImportModal
            onClose={() => {
              setShowImportModal(false);
              setImportResult(null);
            }}
            onImport={(file) => importMutation.mutate(file)}
            isLoading={importMutation.isPending}
            result={importResult}
          />
        )}
      </AnimatePresence>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.csv"
        className="hidden"
        onChange={handleFileImport}
      />
    </div>
  );
}

// Edit Modal Component
function EditModal({
  opportunity,
  onClose,
  onSave,
  isLoading,
}: {
  opportunity: Opportunity;
  onClose: () => void;
  onSave: (data: any) => void;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState({
    title: opportunity.title,
    is_active: opportunity.is_active,
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.95 }}
        className="bg-card rounded-xl p-6 w-full max-w-md shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Edit Opportunity</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Title</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-gray-300"
            />
            <label htmlFor="is_active" className="text-sm">Active</label>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            className="bg-orange-500 hover:bg-orange-600"
            onClick={() => onSave(formData)}
            disabled={isLoading}
          >
            {isLoading ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// Import Modal Component
function ImportModal({
  onClose,
  onImport,
  isLoading,
  result,
}: {
  onClose: () => void;
  onImport: (file: File) => void;
  isLoading: boolean;
  result: any;
}) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith(".json") || file.name.endsWith(".csv"))) {
      onImport(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImport(file);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.95 }}
        className="bg-card rounded-xl p-6 w-full max-w-md shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Import Opportunities</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {result ? (
          <div className="space-y-4">
            {result.error ? (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <p className="font-medium text-red-700">Import Failed</p>
                  <p className="text-sm text-red-600">{result.error}</p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-green-50 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-medium text-green-700">Import Complete</span>
                </div>
                <div className="text-sm text-green-600 space-y-1">
                  <p>Imported: {result.imported}</p>
                  <p>Skipped (duplicates): {result.skipped}</p>
                  {result.failed > 0 && <p>Failed: {result.failed}</p>}
                </div>
              </div>
            )}
            <Button className="w-full" onClick={onClose}>
              Close
            </Button>
          </div>
        ) : (
          <>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? "border-orange-500 bg-orange-50" : "border-gray-300"
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
            >
              {isLoading ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="h-10 w-10 rounded-full border-4 border-orange-500/20 border-t-orange-500 animate-spin" />
                  <p className="text-sm text-muted-foreground">Importing...</p>
                </div>
              ) : (
                <>
                  <FileJson className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground mb-2">
                    Drag and drop a JSON or CSV file here
                  </p>
                  <p className="text-xs text-muted-foreground mb-4">or</p>
                  <Button
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Browse Files
                  </Button>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Supported formats: JSON, CSV (max 10MB)
            </p>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.csv"
          className="hidden"
          onChange={handleFileSelect}
        />
      </motion.div>
    </motion.div>
  );
}
