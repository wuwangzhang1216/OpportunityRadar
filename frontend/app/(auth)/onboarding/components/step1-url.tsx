"use client";

import { useState } from "react";
import { Globe, Github, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useOnboardingStore } from "@/stores/onboarding-store";

export function Step1URL() {
  const { url, setUrl, extractProfile, isExtracting, extractError, skipToManual } =
    useOnboardingStore();
  const [localUrl, setLocalUrl] = useState(url);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUrl(localUrl);
    await extractProfile();
  };

  const isGitHub = localUrl.toLowerCase().includes("github.com");

  return (
    <div className="space-y-6">
      <Card variant="elevated">
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Enter your company website or GitHub repo URL
              </label>
              <div className="relative">
                <Input
                  type="url"
                  placeholder="https://example.com or https://github.com/username/repo"
                  value={localUrl}
                  onChange={(e) => setLocalUrl(e.target.value)}
                  className="pl-10"
                  disabled={isExtracting}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  {isGitHub ? (
                    <Github className="h-4 w-4" />
                  ) : (
                    <Globe className="h-4 w-4" />
                  )}
                </div>
              </div>
              {extractError && (
                <p className="text-red-500 text-sm mt-2">{extractError}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={!localUrl || isExtracting}
            >
              {isExtracting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Extracting profile info...
                </>
              ) : (
                <>
                  Continue
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* URL Type Examples */}
      <div className="grid grid-cols-2 gap-4">
        <Card variant="outline" className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-sm">Website</span>
          </div>
          <p className="text-xs text-gray-500">
            We'll scan your homepage and about page to extract product info
          </p>
        </Card>
        <Card variant="outline" className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Github className="h-4 w-4 text-gray-800" />
            <span className="font-medium text-sm">GitHub Repo</span>
          </div>
          <p className="text-xs text-gray-500">
            We'll analyze your README, tech stack, and repo details
          </p>
        </Card>
      </div>

      {/* Skip option */}
      <div className="text-center">
        <button
          type="button"
          onClick={skipToManual}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Skip and fill in manually
        </button>
      </div>
    </div>
  );
}
