"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Target,
  Calendar,
  DollarSign,
  Users,
  Bookmark,
  BookmarkCheck,
  X,
  Plus,
  Sparkles,
  Star,
  Filter,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";
import { formatDate, formatCurrency, formatRelativeTime } from "@/lib/utils";
import type { Match } from "@/types";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { NoMatchesEmptyState, NoOpportunitiesEmptyState } from "@/components/ui/empty-state";
import { ScoreTooltip } from "@/components/ui/tooltip";
import { useToast } from "@/components/ui/toast";

const categories = [
  { value: "", label: "All" },
  { value: "hackathon", label: "Hackathons" },
  { value: "grant", label: "Grants" },
  { value: "bounty", label: "Bounties" },
  { value: "accelerator", label: "Accelerators" },
  { value: "competition", label: "Competitions" },
];

const filterOptions = [
  { value: "all", label: "All Matches" },
  { value: "bookmarked", label: "Bookmarked" },
  { value: "dismissed", label: "Dismissed" },
];

export default function OpportunitiesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(0);
  const limit = 20;
  const queryClient = useQueryClient();

  // Use matches API for personalized results
  const { data, isLoading } = useQuery({
    queryKey: ["matches", filter, page],
    queryFn: () =>
      apiClient.getMatches({
        skip: page * limit,
        limit,
        bookmarked: filter === "bookmarked" ? true : undefined,
        dismissed: filter === "dismissed" ? true : filter === "all" ? false : undefined,
      }),
  });

  // Filter by search and category on client side (matches API doesn't support these)
  const filteredItems = data?.items?.filter((match: Match) => {
    const matchesSearch = !search ||
      match.opportunity_title?.toLowerCase().includes(search.toLowerCase()) ||
      match.opportunity_description?.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !category ||
      match.opportunity_category === category ||
      match.opportunity_type === category;
    return matchesSearch && matchesCategory;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Opportunities</h1>
          <p className="text-muted-foreground mt-1">
            Discover hackathons, grants, and funding opportunities matched to your profile
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-4">
        <div className="flex gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search opportunities..."
              className="pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            {filterOptions.map((opt) => (
              <Button
                key={opt.value}
                variant={filter === opt.value ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setFilter(opt.value);
                  setPage(0);
                }}
              >
                {opt.value === "bookmarked" && <Bookmark className="h-3 w-3 mr-1" />}
                {opt.label}
              </Button>
            ))}
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map((cat) => (
            <Button
              key={cat.value}
              variant={category === cat.value ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setCategory(cat.value)}
            >
              {cat.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-4 bg-secondary rounded w-3/4 mb-2" />
                <div className="h-3 bg-secondary/50 rounded w-1/2 mb-4" />
                <div className="h-20 bg-secondary/30 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredItems.length > 0 ? (
        <>
          <div className="text-sm text-muted-foreground">
            Showing {filteredItems.length} opportunities
            {filter === "bookmarked" && " (bookmarked)"}
            {filter === "dismissed" && " (dismissed)"}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((match: Match) => (
              <MatchCard key={match.id || match._id} match={match} />
            ))}
          </div>

          {/* Pagination */}
          {data?.total > limit && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <span className="flex items-center px-4 text-sm text-muted-foreground">
                Page {page + 1} of {Math.ceil(data.total / limit)}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * limit >= data.total}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : data?.total === 0 && filter === "all" && !search && !category ? (
        // No matches at all - profile likely incomplete
        <NoMatchesEmptyState />
      ) : filter === "bookmarked" ? (
        <div className="text-center py-12">
          <Bookmark className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground">No bookmarked opportunities</h3>
          <p className="text-muted-foreground mt-1">
            Bookmark opportunities you're interested in to see them here
          </p>
          <Button variant="outline" className="mt-4" onClick={() => setFilter("all")}>
            View all opportunities
          </Button>
        </div>
      ) : filter === "dismissed" ? (
        <div className="text-center py-12">
          <X className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground">No dismissed opportunities</h3>
          <p className="text-muted-foreground mt-1">
            Dismissed opportunities will appear here
          </p>
          <Button variant="outline" className="mt-4" onClick={() => setFilter("all")}>
            View all opportunities
          </Button>
        </div>
      ) : (
        // Filtered results empty
        <NoOpportunitiesEmptyState
          onClearFilters={() => {
            setSearch("");
            setCategory("");
            setFilter("all");
          }}
        />
      )}
    </div>
  );
}

function MatchCard({ match }: { match: Match }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { warning, success } = useToast();
  const matchId = match.id || match._id;
  const batchId = match.batch_id;

  const categoryColors: Record<string, string> = {
    hackathon: "bg-sky-100 text-sky-800",
    grant: "bg-green-100 text-green-800",
    bounty: "bg-orange-100 text-orange-800",
    accelerator: "bg-purple-100 text-purple-800",
    competition: "bg-pink-100 text-pink-800",
  };

  const category = match.opportunity_category || match.opportunity_type || "hackathon";
  const scorePercent = Math.round((match.overall_score || match.score || 0) * 100);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-primary";
    if (score >= 40) return "bg-yellow-500";
    return "bg-gray-400";
  };

  const bookmarkMutation = useMutation({
    mutationFn: () => {
      if (match.is_bookmarked) {
        return apiClient.unbookmarkMatch(matchId);
      }
      return apiClient.bookmarkMatch(matchId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
      queryClient.invalidateQueries({ queryKey: ["topMatches"] });
      if (!match.is_bookmarked) {
        success("Bookmarked", "Opportunity saved to your bookmarks");
      }
    },
  });

  const restoreMutation = useMutation({
    mutationFn: () => apiClient.restoreMatch(matchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
      queryClient.invalidateQueries({ queryKey: ["topMatches"] });
      success("Restored", "Opportunity has been restored to your matches");
    },
  });

  const dismissMutation = useMutation({
    mutationFn: () => {
      if (match.is_dismissed) {
        return apiClient.restoreMatch(matchId);
      }
      return apiClient.dismissMatch(matchId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
      queryClient.invalidateQueries({ queryKey: ["topMatches"] });

      // Show toast with undo option only when dismissing
      if (!match.is_dismissed) {
        warning(
          "Opportunity dismissed",
          `"${match.opportunity_title?.slice(0, 30)}..." has been dismissed`,
          {
            label: "Undo",
            onClick: () => {
              restoreMutation.mutate();
            },
          }
        );
      }
    },
  });

  const addToPipelineMutation = useMutation({
    mutationFn: () => apiClient.addToPipeline(batchId, "discovered"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelineStats"] });
      router.push("/pipeline");
    },
  });

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking on action buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    router.push(`/opportunities/${batchId}`);
  };

  return (
    <Card
      className="h-full hover:shadow-md transition cursor-pointer border-border group relative"
      onClick={handleCardClick}
    >
      <CardContent className="pt-6">
        {/* Quick action buttons - visible on hover */}
        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="icon"
            variant="ghost"
            className={`h-8 w-8 ${match.is_bookmarked ? "text-yellow-600" : ""}`}
            onClick={(e) => {
              e.stopPropagation();
              bookmarkMutation.mutate();
            }}
            disabled={bookmarkMutation.isPending}
            title={match.is_bookmarked ? "Remove bookmark" : "Bookmark"}
          >
            {match.is_bookmarked ? (
              <BookmarkCheck className="h-4 w-4" />
            ) : (
              <Bookmark className="h-4 w-4" />
            )}
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className={`h-8 w-8 ${match.is_dismissed ? "text-gray-400" : "hover:text-red-600"}`}
            onClick={(e) => {
              e.stopPropagation();
              dismissMutation.mutate();
            }}
            disabled={dismissMutation.isPending}
            title={match.is_dismissed ? "Restore" : "Dismiss"}
          >
            <X className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8 hover:text-primary"
            onClick={(e) => {
              e.stopPropagation();
              addToPipelineMutation.mutate();
            }}
            disabled={addToPipelineMutation.isPending}
            title="Add to Pipeline"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-start justify-between mb-3">
          <Badge
            className={
              categoryColors[category] || "bg-secondary text-secondary-foreground"
            }
          >
            {category}
          </Badge>
          {/* Match Score with Tooltip */}
          <ScoreTooltip
            score={scorePercent}
            breakdown={match.score_breakdown}
            reasons={match.reasons}
          >
            <div
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-white text-sm font-medium cursor-help ${getScoreColor(scorePercent)}`}
            >
              <Star className="h-3 w-3 fill-current" />
              {scorePercent}%
            </div>
          </ScoreTooltip>
        </div>

        <h3 className="font-semibold text-lg mb-2 line-clamp-2 text-foreground group-hover:text-primary transition-colors">
          {match.opportunity_title}
        </h3>

        {match.opportunity_description && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
            {match.opportunity_description}
          </p>
        )}

        <div className="space-y-2 text-sm text-muted-foreground">
          {match.deadline && (
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>{formatRelativeTime(match.deadline)}</span>
            </div>
          )}
          {match.opportunity_prize_pool && (
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              <span>{formatCurrency(match.opportunity_prize_pool)}</span>
            </div>
          )}
        </div>

        {/* Match reasons */}
        {match.reasons && match.reasons.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-4">
            {match.reasons.slice(0, 2).map((reason: string, i: number) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {reason}
              </Badge>
            ))}
            {match.reasons.length > 2 && (
              <Badge variant="secondary" className="text-xs">
                +{match.reasons.length - 2}
              </Badge>
            )}
          </div>
        )}

        {/* Eligibility indicator */}
        {match.eligibility_status && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className={`text-xs font-medium ${
              match.eligibility_status === "eligible"
                ? "text-green-600"
                : match.eligibility_status === "partial"
                ? "text-yellow-600"
                : "text-red-600"
            }`}>
              {match.eligibility_status === "eligible"
                ? "✓ Eligible"
                : match.eligibility_status === "partial"
                ? "⚠ Partially eligible"
                : "✗ Check eligibility"}
            </div>
          </div>
        )}

        {/* Status indicators */}
        <div className="flex gap-2 mt-3">
          {match.is_bookmarked && (
            <Badge variant="outline" className="text-xs text-yellow-600 border-yellow-300">
              <Bookmark className="h-3 w-3 mr-1" />
              Saved
            </Badge>
          )}
          {match.is_dismissed && (
            <Badge variant="outline" className="text-xs text-gray-500">
              Dismissed
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
