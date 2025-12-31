"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  Users,
  Globe,
  ExternalLink,
  Plus,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";
import { formatDate, formatCurrency } from "@/lib/utils";

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = params.id as string;

  const { data: opportunity, isLoading } = useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => apiClient.getOpportunity(id),
  });

  const addToPipeline = useMutation({
    mutationFn: () => apiClient.addToPipeline(id, "discovered"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelineStats"] });
      router.push("/pipeline");
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 animate-pulse" />
        <div className="h-64 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium">Opportunity not found</h3>
        <Link href="/opportunities">
          <Button className="mt-4">Back to opportunities</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <Link
        href="/opportunities"
        className="inline-flex items-center text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to opportunities
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge
              className={
                opportunity.category === "hackathon"
                  ? "bg-blue-100 text-blue-800"
                  : opportunity.category === "grant"
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-800"
              }
            >
              {opportunity.category}
            </Badge>
            {opportunity.status && (
              <Badge variant="outline">{opportunity.status}</Badge>
            )}
          </div>
          <h1 className="text-3xl font-bold">{opportunity.title}</h1>
          {opportunity.host_name && (
            <p className="text-gray-600 mt-1">by {opportunity.host_name}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => addToPipeline.mutate()}
            disabled={addToPipeline.isPending}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add to Pipeline
          </Button>
          <Link href={`/generator?batch_id=${id}`}>
            <Button variant="outline">
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Materials
            </Button>
          </Link>
        </div>
      </div>

      {/* Key Info */}
      <div className="grid gap-4 md:grid-cols-4">
        {opportunity.deadline && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Calendar className="h-4 w-4" />
                <span className="text-sm">Deadline</span>
              </div>
              <p className="font-medium">{formatDate(opportunity.deadline)}</p>
            </CardContent>
          </Card>
        )}
        {opportunity.prize_pool && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <DollarSign className="h-4 w-4" />
                <span className="text-sm">Prize Pool</span>
              </div>
              <p className="font-medium">
                {formatCurrency(opportunity.prize_pool)}
              </p>
            </CardContent>
          </Card>
        )}
        {(opportunity.team_min || opportunity.team_max) && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Users className="h-4 w-4" />
                <span className="text-sm">Team Size</span>
              </div>
              <p className="font-medium">
                {opportunity.team_min || 1} - {opportunity.team_max || "Any"}
              </p>
            </CardContent>
          </Card>
        )}
        {opportunity.regions?.length > 0 && (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Globe className="h-4 w-4" />
                <span className="text-sm">Location</span>
              </div>
              <p className="font-medium">
                {opportunity.remote_ok ? "Remote" : opportunity.regions[0]}
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Description */}
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            {opportunity.description ? (
              <p className="whitespace-pre-wrap">{opportunity.description}</p>
            ) : (
              <p className="text-gray-500">No description available.</p>
            )}
          </div>
          {opportunity.url && (
            <a
              href={opportunity.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-blue-600 hover:underline mt-4"
            >
              View original posting <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </CardContent>
      </Card>

      {/* Tags */}
      {opportunity.tags?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Tags & Technologies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {opportunity.tags.map((tag: string) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Requirements */}
      {opportunity.requirements?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2">
              {opportunity.requirements.map((req: any, i: number) => (
                <li key={i} className="text-gray-700">
                  {req.description || JSON.stringify(req)}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Prizes */}
      {opportunity.prizes?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Prizes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {opportunity.prizes.map((prize: any, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium">{prize.name}</p>
                    {prize.description && (
                      <p className="text-sm text-gray-600">{prize.description}</p>
                    )}
                  </div>
                  {prize.amount && (
                    <Badge variant="success">
                      {formatCurrency(prize.amount)}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
