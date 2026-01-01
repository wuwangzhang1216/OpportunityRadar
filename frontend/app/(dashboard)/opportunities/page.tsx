"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Filter, Target, Calendar, DollarSign, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";
import { formatDate, formatCurrency } from "@/lib/utils";
import Link from "next/link";

const categories = [
  { value: "", label: "All Categories" },
  { value: "hackathon", label: "Hackathons" },
  { value: "grant", label: "Grants" },
  { value: "bounty", label: "Bug Bounties" },
  { value: "accelerator", label: "Accelerators" },
  { value: "competition", label: "Competitions" },
];

export default function OpportunitiesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["opportunities", search, category, page],
    queryFn: () =>
      apiClient.getOpportunities({
        search: search || undefined,
        category: category || undefined,
        skip: page * limit,
        limit,
      }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Opportunities</h1>
        <p className="text-muted-foreground mt-1">
          Discover hackathons, grants, and funding opportunities
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search opportunities..."
            className="pl-10"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
          />
        </div>
        <div className="flex gap-2">
          {categories.map((cat) => (
            <Button
              key={cat.value}
              variant={category === cat.value ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setCategory(cat.value);
                setPage(0);
              }}
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
      ) : data?.items?.length > 0 ? (
        <>
          <div className="text-sm text-muted-foreground">
            Showing {data.items.length} of {data.total} opportunities
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.items.map((opp: any) => (
              <OpportunityCard key={opp.id || opp._id} opportunity={opp} />
            ))}
          </div>

          {/* Pagination */}
          {data.total > limit && (
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
      ) : (
        <div className="text-center py-12">
          <Target className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground">
            No opportunities found
          </h3>
          <p className="text-muted-foreground mt-1">
            Try adjusting your search or filters
          </p>
        </div>
      )}
    </div>
  );
}

function OpportunityCard({ opportunity }: { opportunity: any }) {
  const categoryColors: Record<string, string> = {
    hackathon: "bg-sky-100 text-sky-800",
    grant: "bg-green-100 text-green-800",
    bounty: "bg-orange-100 text-orange-800",
    accelerator: "bg-purple-100 text-purple-800",
    competition: "bg-pink-100 text-pink-800",
  };

  // MongoDB returns _id, Beanie may serialize it as id or _id
  const opportunityId = opportunity.id || opportunity._id;
  // Backend uses opportunity_type, frontend may expect category
  const category = opportunity.category || opportunity.opportunity_type || "hackathon";

  return (
    <Link href={`/opportunities/${opportunityId}`}>
      <Card className="h-full hover:shadow-md transition cursor-pointer border-border">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between mb-3">
            <Badge
              className={
                categoryColors[category] || "bg-secondary text-secondary-foreground"
              }
            >
              {category}
            </Badge>
            {opportunity.match_score && (
              <div className="text-sm font-medium text-primary">
                {Math.round(opportunity.match_score * 100)}% match
              </div>
            )}
          </div>

          <h3 className="font-semibold text-lg mb-2 line-clamp-2 text-foreground">
            {opportunity.title}
          </h3>

          {opportunity.description && (
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {opportunity.description}
            </p>
          )}

          <div className="space-y-2 text-sm text-muted-foreground">
            {opportunity.deadline && (
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span>Deadline: {formatDate(opportunity.deadline)}</span>
              </div>
            )}
            {opportunity.prize_pool && (
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                <span>Prize: {formatCurrency(opportunity.prize_pool)}</span>
              </div>
            )}
            {opportunity.team_size && (
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <span>Team size: {opportunity.team_size}</span>
              </div>
            )}
          </div>

          {opportunity.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-4">
              {opportunity.tags.slice(0, 3).map((tag: string) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {opportunity.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{opportunity.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
