"use client";

import { useState } from "react";
import { apiClient } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useAuthStore } from "@/stores/auth-store";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [exporting, setExporting] = useState(false);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  const handleExportData = async (format: "json" | "csv") => {
    try {
      setExporting(true);
      const blob = await apiClient.exportUserData(format);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `opportunity-radar-export.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export data:", error);
      alert("Failed to export data. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const handleDisconnectOAuth = async (provider: "github" | "google") => {
    if (!confirm(`Are you sure you want to disconnect ${provider}?`)) return;

    try {
      setDisconnecting(provider);
      await apiClient.disconnectOAuth(provider);
      window.location.reload();
    } catch (error: any) {
      alert(error.response?.data?.detail || `Failed to disconnect ${provider}`);
    } finally {
      setDisconnecting(null);
    }
  };

  const handleConnectOAuth = async (provider: "github" | "google") => {
    try {
      const response = await apiClient.getOAuthUrl(provider);
      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      }
    } catch (error) {
      console.error(`Failed to connect ${provider}:`, error);
    }
  };

  const hasGitHub = user?.oauth_connections?.some((c) => c.provider === "github");
  const hasGoogle = user?.oauth_connections?.some((c) => c.provider === "google");

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Connected Accounts */}
      <Card className="p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Connected Accounts</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              <div>
                <p className="font-medium">GitHub</p>
                <p className="text-sm text-gray-500">
                  {hasGitHub ? "Connected" : "Not connected"}
                </p>
              </div>
            </div>
            {hasGitHub ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDisconnectOAuth("github")}
                disabled={disconnecting === "github"}
              >
                {disconnecting === "github" ? "Disconnecting..." : "Disconnect"}
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleConnectOAuth("github")}
              >
                Connect
              </Button>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <div>
                <p className="font-medium">Google</p>
                <p className="text-sm text-gray-500">
                  {hasGoogle ? "Connected" : "Not connected"}
                </p>
              </div>
            </div>
            {hasGoogle ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDisconnectOAuth("google")}
                disabled={disconnecting === "google"}
              >
                {disconnecting === "google" ? "Disconnecting..." : "Disconnect"}
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleConnectOAuth("google")}
              >
                Connect
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Data Export */}
      <Card className="p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Data Export</h2>
        <p className="text-gray-600 mb-4">
          Download all your data including your profile, matches, pipelines, and generated materials.
        </p>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => handleExportData("json")}
            disabled={exporting}
          >
            {exporting ? "Exporting..." : "Export as JSON"}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExportData("csv")}
            disabled={exporting}
          >
            {exporting ? "Exporting..." : "Export as CSV"}
          </Button>
        </div>
      </Card>

      {/* Calendar Subscription */}
      <Card className="p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Calendar Subscription</h2>
        <p className="text-gray-600 mb-4">
          Subscribe to opportunity deadlines in your calendar app.
        </p>
        <CalendarSubscriptionSection />
      </Card>

      {/* Danger Zone */}
      <Card className="p-6 border-red-200">
        <h2 className="text-lg font-semibold text-red-600 mb-4">Danger Zone</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Delete Account</p>
              <p className="text-sm text-gray-500">
                Permanently delete your account and all associated data.
              </p>
            </div>
            <Button variant="outline" className="text-red-600 hover:bg-red-50">
              Delete Account
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function CalendarSubscriptionSection() {
  const [subscriptionUrl, setSubscriptionUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGetSubscriptionUrl = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getCalendarSubscriptionUrls();
      setSubscriptionUrl(response.upcoming_ical);
    } catch (error) {
      console.error("Failed to get subscription URL:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUrl = () => {
    if (subscriptionUrl) {
      navigator.clipboard.writeText(subscriptionUrl);
      alert("URL copied to clipboard!");
    }
  };

  return (
    <div>
      {subscriptionUrl ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={subscriptionUrl}
              readOnly
              className="flex-1 px-3 py-2 border rounded-lg text-sm bg-gray-50"
            />
            <Button variant="outline" size="sm" onClick={handleCopyUrl}>
              Copy
            </Button>
          </div>
          <div className="text-sm text-gray-500">
            <p className="font-medium mb-1">How to subscribe:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <strong>Google Calendar:</strong> Settings → Add calendar → From URL
              </li>
              <li>
                <strong>Outlook:</strong> Add calendar → Subscribe from web
              </li>
              <li>
                <strong>Apple Calendar:</strong> File → New Calendar Subscription
              </li>
            </ul>
          </div>
        </div>
      ) : (
        <Button onClick={handleGetSubscriptionUrl} disabled={loading}>
          {loading ? "Loading..." : "Get Subscription URL"}
        </Button>
      )}
    </div>
  );
}
