"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Notification, NotificationPreferences } from "@/types";

const NotificationIcon = ({ type }: { type: string }) => {
  const iconClass = "w-5 h-5";

  switch (type) {
    case "deadline_reminder":
      return (
        <svg className={`${iconClass} text-orange-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "new_match":
      return (
        <svg className={`${iconClass} text-green-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "team_invite":
      return (
        <svg className={`${iconClass} text-blue-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      );
    default:
      return (
        <svg className={`${iconClass} text-gray-500`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      );
  }
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPreferences, setShowPreferences] = useState(false);

  useEffect(() => {
    loadNotifications();
    loadPreferences();
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await apiClient.getNotifications();
      setNotifications(response.items || []);
    } catch (error) {
      console.error("Failed to load notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadPreferences = async () => {
    try {
      const prefs = await apiClient.getNotificationPreferences();
      setPreferences(prefs);
    } catch (error) {
      console.error("Failed to load preferences:", error);
    }
  };

  const handleMarkRead = async (notificationId: string) => {
    try {
      await apiClient.markNotificationRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (error) {
      console.error("Failed to mark all notifications as read:", error);
    }
  };

  const handlePreferenceChange = async (key: string, value: boolean | number[]) => {
    if (!preferences) return;

    const updatedPrefs = { ...preferences, [key]: value };
    setPreferences(updatedPrefs);

    try {
      await apiClient.updateNotificationPreferences({ [key]: value });
    } catch (error) {
      console.error("Failed to update preferences:", error);
      // Revert on error
      setPreferences(preferences);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          {unreadCount > 0 && (
            <p className="text-gray-600">{unreadCount} unread</p>
          )}
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" onClick={handleMarkAllRead}>
              Mark all read
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => setShowPreferences(!showPreferences)}
          >
            Settings
          </Button>
        </div>
      </div>

      {showPreferences && preferences && (
        <Card className="p-6 mb-6">
          <h2 className="font-semibold mb-4">Notification Preferences</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Email Notifications</p>
                <p className="text-sm text-gray-500">Receive notifications via email</p>
              </div>
              <Switch
                checked={preferences.email_enabled}
                onCheckedChange={(checked) => handlePreferenceChange("email_enabled", checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Deadline Reminders</p>
                <p className="text-sm text-gray-500">Get reminded before deadlines</p>
              </div>
              <Switch
                checked={preferences.email_deadline_reminders}
                onCheckedChange={(checked) => handlePreferenceChange("email_deadline_reminders", checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">New Match Alerts</p>
                <p className="text-sm text-gray-500">Notified when new opportunities match your profile</p>
              </div>
              <Switch
                checked={preferences.email_new_matches}
                onCheckedChange={(checked) => handlePreferenceChange("email_new_matches", checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Team Updates</p>
                <p className="text-sm text-gray-500">Updates from your teams</p>
              </div>
              <Switch
                checked={preferences.email_team_updates}
                onCheckedChange={(checked) => handlePreferenceChange("email_team_updates", checked)}
              />
            </div>

            <div>
              <p className="font-medium mb-2">Reminder Days Before Deadline</p>
              <div className="flex gap-2">
                {[1, 3, 7, 14].map((day) => (
                  <button
                    key={day}
                    onClick={() => {
                      const current = preferences.reminder_days || [];
                      const updated = current.includes(day)
                        ? current.filter((d) => d !== day)
                        : [...current, day].sort((a, b) => a - b);
                      handlePreferenceChange("reminder_days", updated);
                    }}
                    className={`px-3 py-1 rounded-full text-sm ${
                      preferences.reminder_days?.includes(day)
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {day}d
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {notifications.length === 0 ? (
        <Card className="p-12 text-center">
          <svg
            className="w-16 h-16 text-gray-300 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <p className="text-gray-500">No notifications yet</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <Card
              key={notification.id}
              className={`p-4 cursor-pointer transition-colors ${
                notification.is_read ? "bg-white" : "bg-blue-50"
              }`}
              onClick={() => !notification.is_read && handleMarkRead(notification.id)}
            >
              <div className="flex items-start gap-4">
                <NotificationIcon type={notification.notification_type} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className={`font-medium ${notification.is_read ? "" : "text-blue-900"}`}>
                      {notification.title}
                    </p>
                    <span className="text-xs text-gray-500 ml-2 shrink-0">
                      {formatDate(notification.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                </div>
                {!notification.is_read && (
                  <div className="w-2 h-2 bg-blue-600 rounded-full shrink-0 mt-2" />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
