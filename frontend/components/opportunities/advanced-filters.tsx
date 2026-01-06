"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  SlidersHorizontal,
  X,
  Calendar,
  DollarSign,
  Users,
  Clock,
  Filter,
  Save,
  Trash2,
  ChevronDown,
  Check,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export interface FilterState {
  categories: string[];
  deadlineRange: { min: number | null; max: number | null }; // days from now
  prizeRange: { min: number | null; max: number | null };
  teamSizeRange: { min: number | null; max: number | null };
  matchScoreMin: number | null;
  format: string[];
  sortBy: string;
  sortOrder: "asc" | "desc";
}

interface SavedFilter {
  id: string;
  name: string;
  filters: FilterState;
}

const defaultFilters: FilterState = {
  categories: [],
  deadlineRange: { min: null, max: null },
  prizeRange: { min: null, max: null },
  teamSizeRange: { min: null, max: null },
  matchScoreMin: null,
  format: [],
  sortBy: "match_score",
  sortOrder: "desc",
};

const categories = [
  { id: "hackathon", label: "Hackathon" },
  { id: "grant", label: "Grant" },
  { id: "bounty", label: "Bounty" },
  { id: "accelerator", label: "Accelerator" },
  { id: "competition", label: "Competition" },
];

const formats = [
  { id: "online", label: "Online" },
  { id: "in-person", label: "In-Person" },
  { id: "hybrid", label: "Hybrid" },
];

const sortOptions = [
  { id: "match_score", label: "Match Score" },
  { id: "deadline", label: "Deadline" },
  { id: "prize", label: "Prize Amount" },
  { id: "created_at", label: "Recently Added" },
];

const STORAGE_KEY = "opportunity_saved_filters";

interface AdvancedFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onClose?: () => void;
  isOpen?: boolean;
}

export function AdvancedFilters({
  filters,
  onFiltersChange,
  onClose,
  isOpen = true,
}: AdvancedFiltersProps) {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters);
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([]);
  const [saveFilterName, setSaveFilterName] = useState("");
  const [showSaveInput, setShowSaveInput] = useState(false);

  // Load saved filters from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setSavedFilters(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse saved filters");
      }
    }
  }, []);

  // Count active filters
  const activeFilterCount =
    localFilters.categories.length +
    localFilters.format.length +
    (localFilters.deadlineRange.min !== null || localFilters.deadlineRange.max !== null ? 1 : 0) +
    (localFilters.prizeRange.min !== null || localFilters.prizeRange.max !== null ? 1 : 0) +
    (localFilters.teamSizeRange.min !== null || localFilters.teamSizeRange.max !== null ? 1 : 0) +
    (localFilters.matchScoreMin !== null ? 1 : 0);

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setLocalFilters((prev) => ({ ...prev, [key]: value }));
  };

  const toggleCategory = (category: string) => {
    const newCategories = localFilters.categories.includes(category)
      ? localFilters.categories.filter((c) => c !== category)
      : [...localFilters.categories, category];
    updateFilter("categories", newCategories);
  };

  const toggleFormat = (format: string) => {
    const newFormats = localFilters.format.includes(format)
      ? localFilters.format.filter((f) => f !== format)
      : [...localFilters.format, format];
    updateFilter("format", newFormats);
  };

  const handleApply = () => {
    onFiltersChange(localFilters);
    onClose?.();
  };

  const handleReset = () => {
    setLocalFilters(defaultFilters);
    onFiltersChange(defaultFilters);
  };

  const handleSaveFilter = () => {
    if (!saveFilterName.trim()) return;

    const newFilter: SavedFilter = {
      id: Date.now().toString(),
      name: saveFilterName.trim(),
      filters: { ...localFilters },
    };

    const newSavedFilters = [...savedFilters, newFilter];
    setSavedFilters(newSavedFilters);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newSavedFilters));
    setSaveFilterName("");
    setShowSaveInput(false);
  };

  const handleLoadFilter = (saved: SavedFilter) => {
    setLocalFilters(saved.filters);
    onFiltersChange(saved.filters);
  };

  const handleDeleteSavedFilter = (id: string) => {
    const newSavedFilters = savedFilters.filter((f) => f.id !== id);
    setSavedFilters(newSavedFilters);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newSavedFilters));
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="mb-6 overflow-hidden">
        <CardHeader className="pb-3 bg-secondary/30 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">Advanced Filters</CardTitle>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" size="sm">
                  {activeFilterCount} active
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <Trash2 className="h-4 w-4 mr-1" />
                Reset
              </Button>
              {onClose && (
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4 space-y-6">
          {/* Categories */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">
              Categories
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => toggleCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    localFilters.categories.includes(cat.id)
                      ? "bg-primary text-white"
                      : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                  }`}
                >
                  {localFilters.categories.includes(cat.id) && (
                    <Check className="h-3 w-3 inline mr-1" />
                  )}
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Format */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">
              Format
            </label>
            <div className="flex flex-wrap gap-2">
              {formats.map((fmt) => (
                <button
                  key={fmt.id}
                  onClick={() => toggleFormat(fmt.id)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    localFilters.format.includes(fmt.id)
                      ? "bg-primary text-white"
                      : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                  }`}
                >
                  {localFilters.format.includes(fmt.id) && (
                    <Check className="h-3 w-3 inline mr-1" />
                  )}
                  {fmt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Range Filters Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Deadline Range */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 flex items-center gap-1">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                Deadline (days)
              </label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={localFilters.deadlineRange.min ?? ""}
                  onChange={(e) =>
                    updateFilter("deadlineRange", {
                      ...localFilters.deadlineRange,
                      min: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
                <span className="text-muted-foreground">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={localFilters.deadlineRange.max ?? ""}
                  onChange={(e) =>
                    updateFilter("deadlineRange", {
                      ...localFilters.deadlineRange,
                      max: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
              </div>
            </div>

            {/* Prize Range */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 flex items-center gap-1">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                Prize ($)
              </label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={localFilters.prizeRange.min ?? ""}
                  onChange={(e) =>
                    updateFilter("prizeRange", {
                      ...localFilters.prizeRange,
                      min: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
                <span className="text-muted-foreground">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={localFilters.prizeRange.max ?? ""}
                  onChange={(e) =>
                    updateFilter("prizeRange", {
                      ...localFilters.prizeRange,
                      max: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
              </div>
            </div>

            {/* Team Size Range */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 flex items-center gap-1">
                <Users className="h-4 w-4 text-muted-foreground" />
                Team Size
              </label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={localFilters.teamSizeRange.min ?? ""}
                  onChange={(e) =>
                    updateFilter("teamSizeRange", {
                      ...localFilters.teamSizeRange,
                      min: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
                <span className="text-muted-foreground">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={localFilters.teamSizeRange.max ?? ""}
                  onChange={(e) =>
                    updateFilter("teamSizeRange", {
                      ...localFilters.teamSizeRange,
                      max: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="h-9"
                />
              </div>
            </div>

            {/* Match Score Min */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 flex items-center gap-1">
                <Filter className="h-4 w-4 text-muted-foreground" />
                Min Match Score
              </label>
              <Input
                type="number"
                placeholder="e.g., 70"
                min={0}
                max={100}
                value={localFilters.matchScoreMin ?? ""}
                onChange={(e) =>
                  updateFilter(
                    "matchScoreMin",
                    e.target.value ? parseInt(e.target.value) : null
                  )
                }
                className="h-9"
              />
            </div>
          </div>

          {/* Sort Options */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-foreground">Sort by:</label>
              <select
                value={localFilters.sortBy}
                onChange={(e) => updateFilter("sortBy", e.target.value)}
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                {sortOptions.map((opt) => (
                  <option key={opt.id} value={opt.id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() =>
                  updateFilter("sortOrder", localFilters.sortOrder === "asc" ? "desc" : "asc")
                }
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm hover:bg-secondary transition-colors"
              >
                {localFilters.sortOrder === "desc" ? "Descending" : "Ascending"}
                <ChevronDown
                  className={`h-4 w-4 inline ml-1 transition-transform ${
                    localFilters.sortOrder === "asc" ? "rotate-180" : ""
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Saved Filters */}
          {savedFilters.length > 0 && (
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Saved Views
              </label>
              <div className="flex flex-wrap gap-2">
                {savedFilters.map((saved) => (
                  <div
                    key={saved.id}
                    className="flex items-center gap-1 bg-secondary rounded-full pl-3 pr-1 py-1"
                  >
                    <button
                      onClick={() => handleLoadFilter(saved)}
                      className="text-sm font-medium hover:text-primary transition-colors"
                    >
                      {saved.name}
                    </button>
                    <button
                      onClick={() => handleDeleteSavedFilter(saved.id)}
                      className="p-1 hover:bg-red-100 hover:text-red-600 rounded-full transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <div className="flex items-center gap-2">
              {showSaveInput ? (
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="View name..."
                    value={saveFilterName}
                    onChange={(e) => setSaveFilterName(e.target.value)}
                    className="h-9 w-40"
                    onKeyDown={(e) => e.key === "Enter" && handleSaveFilter()}
                  />
                  <Button size="sm" onClick={handleSaveFilter} disabled={!saveFilterName.trim()}>
                    Save
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowSaveInput(false)}>
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button size="sm" variant="outline" onClick={() => setShowSaveInput(true)}>
                  <Save className="h-4 w-4 mr-1" />
                  Save View
                </Button>
              )}
            </div>
            <Button onClick={handleApply}>
              <Filter className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Compact filter bar for quick access
export function FilterBar({
  filters,
  onFiltersChange,
  onOpenAdvanced,
}: {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onOpenAdvanced: () => void;
}) {
  const activeCount =
    filters.categories.length +
    filters.format.length +
    (filters.deadlineRange.min !== null || filters.deadlineRange.max !== null ? 1 : 0) +
    (filters.prizeRange.min !== null || filters.prizeRange.max !== null ? 1 : 0) +
    (filters.teamSizeRange.min !== null || filters.teamSizeRange.max !== null ? 1 : 0) +
    (filters.matchScoreMin !== null ? 1 : 0);

  const clearFilter = (type: keyof FilterState) => {
    const newFilters = { ...filters };
    if (type === "categories" || type === "format") {
      newFilters[type] = [];
    } else if (type === "deadlineRange" || type === "prizeRange" || type === "teamSizeRange") {
      newFilters[type] = { min: null, max: null };
    } else if (type === "matchScoreMin") {
      newFilters[type] = null;
    }
    onFiltersChange(newFilters);
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Button variant="outline" size="sm" onClick={onOpenAdvanced} className="gap-2">
        <SlidersHorizontal className="h-4 w-4" />
        Filters
        {activeCount > 0 && (
          <Badge variant="secondary" size="sm" className="ml-1">
            {activeCount}
          </Badge>
        )}
      </Button>

      {/* Active filter badges */}
      <AnimatePresence>
        {filters.categories.map((cat) => (
          <motion.div
            key={`cat-${cat}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <Badge variant="outline" className="gap-1">
              {cat}
              <button
                onClick={() =>
                  onFiltersChange({
                    ...filters,
                    categories: filters.categories.filter((c) => c !== cat),
                  })
                }
                className="hover:text-red-500"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </motion.div>
        ))}

        {filters.matchScoreMin !== null && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <Badge variant="outline" className="gap-1">
              Score &ge; {filters.matchScoreMin}%
              <button onClick={() => clearFilter("matchScoreMin")} className="hover:text-red-500">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </motion.div>
        )}

        {(filters.deadlineRange.min !== null || filters.deadlineRange.max !== null) && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <Badge variant="outline" className="gap-1">
              <Calendar className="h-3 w-3" />
              {filters.deadlineRange.min ?? "0"}-{filters.deadlineRange.max ?? "∞"} days
              <button onClick={() => clearFilter("deadlineRange")} className="hover:text-red-500">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </motion.div>
        )}
      </AnimatePresence>

      {activeCount > 1 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFiltersChange(defaultFilters)}
          className="text-muted-foreground"
        >
          Clear all
        </Button>
      )}
    </div>
  );
}

export { defaultFilters };
