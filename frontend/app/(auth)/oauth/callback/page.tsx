"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/services/api-client";
import { useAuthStore } from "@/stores/auth-store";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const { setUser } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const errorParam = searchParams.get("error");

      if (errorParam) {
        setError(`OAuth error: ${errorParam}`);
        return;
      }

      if (!code) {
        setError("No authorization code received");
        return;
      }

      // Determine provider from the URL path or state
      const provider = state?.startsWith("github") ? "github" : "google";

      try {
        const response = await apiClient.handleOAuthCallback(provider, code, state || undefined);

        if (response.access_token) {
          apiClient.setToken(response.access_token);

          // Fetch user data
          const userData = await apiClient.getMe();
          setUser(userData);

          // Check if onboarding is needed
          if (!userData.has_profile) {
            router.push("/onboarding");
          } else {
            router.push("/dashboard");
          }
        } else {
          setError("No access token received");
        }
      } catch (err: any) {
        console.error("OAuth callback error:", err);
        setError(err.response?.data?.detail || "Failed to complete authentication");
      }
    };

    handleCallback();
  }, [searchParams, router, setUser]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg max-w-md text-center">
          <h2 className="font-semibold mb-2">Authentication Failed</h2>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => router.push("/login")}
            className="mt-4 text-blue-600 hover:underline"
          >
            Return to login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4" />
      <p className="text-gray-600">Completing authentication...</p>
    </div>
  );
}
