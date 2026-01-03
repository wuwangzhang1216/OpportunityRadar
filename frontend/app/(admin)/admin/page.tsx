"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Database,
  Users,
  TrendingUp,
  Activity,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

export default function AdminDashboard() {
  const { data: analytics, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin-analytics"],
    queryFn: () => apiClient.getAdminAnalytics(),
  });

  const stats = [
    {
      label: "Total Opportunities",
      value: analytics?.opportunities?.total ?? "-",
      icon: Database,
      color: "bg-blue-500",
      subtext: `${analytics?.opportunities?.active ?? 0} active`,
    },
    {
      label: "Total Users",
      value: analytics?.users?.total ?? "-",
      icon: Users,
      color: "bg-green-500",
      subtext: `${analytics?.users?.with_profiles ?? 0} with profiles`,
    },
    {
      label: "Total Matches",
      value: analytics?.matches?.total ?? "-",
      icon: TrendingUp,
      color: "bg-purple-500",
      subtext: `${analytics?.matches?.interested ?? 0} interested`,
    },
    {
      label: "Pipeline Items",
      value: analytics?.pipeline?.total ?? "-",
      icon: Activity,
      color: "bg-orange-500",
      subtext: `${analytics?.pipeline?.won ?? 0} won`,
    },
  ];

  const categoryBreakdown = analytics?.opportunities?.by_category || {};

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">System overview and statistics</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <div className={`${stat.color} p-2 rounded-lg`}>
                  <stat.icon className="h-4 w-4 text-white" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {isLoading ? (
                    <div className="h-8 w-20 bg-secondary animate-pulse rounded" />
                  ) : (
                    stat.value.toLocaleString()
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">{stat.subtext}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Opportunities by Category</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-8 bg-secondary animate-pulse rounded" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(categoryBreakdown).map(([category, count]) => {
                const total = analytics?.opportunities?.total || 1;
                const percentage = Math.round((Number(count) / total) * 100);
                return (
                  <div key={category} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize">{category.replace("_", " ")}</span>
                      <span className="text-muted-foreground">
                        {String(count)} ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="h-full bg-primary rounded-full"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" asChild>
              <a href="/admin/opportunities">Manage Opportunities</a>
            </Button>
            <Button variant="outline" disabled>
              View Crawlers (CLI)
            </Button>
            <Button variant="outline" disabled>
              Manage Users (CLI)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
