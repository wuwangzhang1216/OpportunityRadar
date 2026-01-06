"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Trophy, ArrowRight, Loader2, Star, Sparkles, Plus, Kanban } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOnboardingStore } from "@/stores/onboarding-store";

export function Step3Matches() {
  const router = useRouter();
  const { topMatches, isLoadingMatches } = useOnboardingStore();

  const handleGoToDashboard = () => {
    router.push("/dashboard");
  };

  const handleGoToGenerator = () => {
    router.push("/generator");
  };

  if (isLoadingMatches) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">Finding your best matches...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success message */}
      <Card variant="feature" className="text-center py-6">
        <CardContent>
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 mb-4">
            <Trophy className="h-6 w-6 text-green-600" />
          </div>
          <h2 className="text-xl font-bold mb-2">Profile Created!</h2>
          <p className="text-gray-600">
            Here are your top opportunity matches based on your profile
          </p>
        </CardContent>
      </Card>

      {/* Top Matches */}
      {topMatches.length > 0 ? (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">Your Top Matches</h3>
          {topMatches.slice(0, 3).map((match, index) => (
            <Card key={match.id} variant="elevated" className="overflow-hidden">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 font-bold text-sm">
                      #{index + 1}
                    </span>
                  </div>

                  {/* Match Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-medium text-gray-900 truncate">
                          {match.opportunity_title || "Opportunity"}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" size="sm">
                            {match.opportunity_category || "General"}
                          </Badge>
                          {match.deadline && (
                            <span className="text-xs text-gray-500">
                              Due: {new Date(match.deadline).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      {/* Score */}
                      <div className="flex items-center gap-1 text-yellow-500">
                        <Star className="h-4 w-4 fill-current" />
                        <span className="text-sm font-medium">
                          {((match.score ?? match.overall_score ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Reasons */}
                    {match.reasons && match.reasons.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {match.reasons.slice(0, 3).map((reason, i) => (
                          <Badge key={i} variant="secondary" size="sm">
                            {reason}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Quick actions for first match */}
                    {index === 0 && (
                      <div className="mt-3 flex gap-2">
                        <Link href={`/generator?batch_id=${match.batch_id || match.id}`}>
                          <Button size="sm" variant="outline" className="text-xs">
                            <Sparkles className="h-3 w-3 mr-1" />
                            Generate Materials
                          </Button>
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {topMatches.length > 3 && (
            <p className="text-center text-sm text-gray-500">
              +{topMatches.length - 3} more matches in your dashboard
            </p>
          )}
        </div>
      ) : (
        <Card variant="outline" className="text-center py-8">
          <CardContent>
            <p className="text-gray-500">
              No matches found yet. Explore opportunities in the dashboard!
            </p>
          </CardContent>
        </Card>
      )}

      {/* What's Next Section */}
      <Card className="bg-gradient-to-r from-primary/5 to-purple-500/5 border-primary/20">
        <CardContent className="py-5">
          <h3 className="font-semibold text-gray-900 mb-3">What's Next?</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-primary">1</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Add opportunities to your Pipeline</p>
                <p className="text-xs text-gray-500">Track your progress from discovery to victory</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-primary">2</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Generate application materials with AI</p>
                <p className="text-xs text-gray-500">Create README, pitch decks, and demo scripts instantly</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-primary">3</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Submit and track your applications</p>
                <p className="text-xs text-gray-500">Stay organized with deadline reminders</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* CTAs */}
      <div className="space-y-3">
        <Button className="w-full" size="lg" onClick={handleGoToDashboard}>
          Go to Dashboard
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>

        <div className="flex gap-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={handleGoToGenerator}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Try AI Generator
          </Button>
          <Link href="/pipeline" className="flex-1">
            <Button variant="outline" className="w-full">
              <Kanban className="h-4 w-4 mr-2" />
              View Pipeline
            </Button>
          </Link>
        </div>
      </div>

      <p className="text-center text-sm text-gray-500">
        You can always access all features from the sidebar menu
      </p>
    </div>
  );
}
