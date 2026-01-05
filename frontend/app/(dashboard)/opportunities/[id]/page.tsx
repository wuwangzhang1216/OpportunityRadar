"use client";

import { useState } from "react";
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
  Download,
  Share2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropdown } from "@/components/ui/dropdown";
import { apiClient } from "@/services/api-client";
import { formatDate, formatCurrency } from "@/lib/utils";

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = params.id as string;
  const [showCalendarMenu, setShowCalendarMenu] = useState(false);

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

  const handleAddToCalendar = async (calendarType: "google" | "outlook" | "ical") => {
    try {
      if (calendarType === "ical") {
        const url = await apiClient.getOpportunityIcalUrl(id);
        window.open(url, "_blank");
      } else if (calendarType === "google") {
        const response = await apiClient.getOpportunityGoogleCalendarUrl(id);
        window.open(response.url, "_blank");
      } else if (calendarType === "outlook") {
        const response = await apiClient.getOpportunityOutlookCalendarUrl(id);
        window.open(response.url, "_blank");
      }
    } catch (error) {
      console.error("Failed to add to calendar:", error);
      alert("Failed to add to calendar. This opportunity may not have a deadline set.");
    }
    setShowCalendarMenu(false);
  };

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
          <div className="relative">
            <Button
              variant="outline"
              onClick={() => setShowCalendarMenu(!showCalendarMenu)}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Add to Calendar
            </Button>
            {showCalendarMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-1 z-10">
                <button
                  onClick={() => handleAddToCalendar("google")}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google Calendar
                </button>
                <button
                  onClick={() => handleAddToCalendar("outlook")}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#0078D4">
                    <path d="M24 7.387v10.478c0 .23-.08.424-.238.576-.157.152-.355.228-.594.228h-8.457v-6.182l1.262 1.23h.003l.088.074c.236.2.555.2.79-.006l.09-.074 1.258-1.224v6.182h4.882c.067 0 .125-.025.175-.076.05-.05.076-.11.076-.175V8.456l-7.668 5.934-.002.001a.396.396 0 01-.456.024l-.003-.002-7.665-5.957v9.175c0 .066.026.125.076.175.05.05.11.076.176.076h4.881v-6.183l1.257 1.225.09.073c.117.1.253.15.396.15.143 0 .279-.05.396-.15l.09-.074 1.261-1.23v6.189H0V7.387c0-.23.08-.424.238-.576.157-.152.355-.229.594-.229h.006l11.16 8.666 11.17-8.666h.006c.238 0 .437.077.594.229.158.152.237.346.237.576z"/>
                  </svg>
                  Outlook
                </button>
                <button
                  onClick={() => handleAddToCalendar("ical")}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download .ics
                </button>
              </div>
            )}
          </div>
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
