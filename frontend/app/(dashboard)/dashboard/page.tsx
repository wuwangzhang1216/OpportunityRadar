"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  Clock,
  Trophy,
  ArrowRight,
  Calendar,
  Sparkles,
  Zap,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";
import { formatRelativeTime } from "@/lib/utils";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const { data: matches, isLoading: matchesLoading } = useQuery({
    queryKey: ["topMatches"],
    queryFn: () => apiClient.getTopMatches(5),
  });

  const { data: pipelineStats } = useQuery({
    queryKey: ["pipelineStats"],
    queryFn: () => apiClient.getPipelineStats(),
  });

  const { data: matchStats } = useQuery({
    queryKey: ["matchStats"],
    queryFn: () => apiClient.getMatches({ limit: 1 }),
  });

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={item}>
        <div className="flex items-center gap-3 mb-2">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur-lg opacity-50 animate-pulse" />
            <div className="relative h-12 w-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">
              Your personalized hackathon command center
            </p>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={item} className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total Matches"
          value={matchStats?.total || 0}
          icon={<Target className="h-5 w-5" />}
          description="Opportunities for you"
          color="blue"
          delay={0}
        />
        <StatCard
          title="In Pipeline"
          value={pipelineStats?.total || 0}
          icon={<TrendingUp className="h-5 w-5" />}
          description="Active opportunities"
          color="green"
          delay={0.1}
        />
        <StatCard
          title="Preparing"
          value={pipelineStats?.by_stage?.preparing || 0}
          icon={<Clock className="h-5 w-5" />}
          description="In progress"
          color="yellow"
          delay={0.2}
        />
        <StatCard
          title="Won"
          value={pipelineStats?.by_stage?.won || 0}
          icon={<Trophy className="h-5 w-5" />}
          description="Victories"
          color="purple"
          delay={0.3}
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Matches */}
        <motion.div variants={item}>
          <Card variant="elevated" className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between bg-gradient-to-r from-blue-50/50 to-purple-50/50 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                  <Zap className="h-4 w-4 text-white" />
                </div>
                <CardTitle className="text-lg">Top Matches</CardTitle>
              </div>
              <Link href="/opportunities">
                <Button variant="ghost" size="sm" className="group">
                  View all
                  <ChevronRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-4">
              {matchesLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div
                      key={i}
                      className="h-16 rounded-xl skeleton"
                    />
                  ))}
                </div>
              ) : matches?.items?.length > 0 ? (
                <div className="space-y-3">
                  {matches.items.slice(0, 5).map((match: any, index: number) => (
                    <motion.div
                      key={match.batch_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <MatchCard match={match} />
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="relative inline-block mb-4">
                    <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl" />
                    <div className="relative h-16 w-16 mx-auto bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
                      <Target className="h-8 w-8 text-blue-500" />
                    </div>
                  </div>
                  <p className="font-medium text-gray-900">No matches yet</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Complete your profile to get matched
                  </p>
                  <Link href="/profile">
                    <Button variant="gradient" size="sm" className="mt-4">
                      Complete Profile
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Pipeline Overview */}
        <motion.div variants={item}>
          <Card variant="elevated" className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between bg-gradient-to-r from-green-50/50 to-blue-50/50 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center">
                  <TrendingUp className="h-4 w-4 text-white" />
                </div>
                <CardTitle className="text-lg">Pipeline Overview</CardTitle>
              </div>
              <Link href="/pipeline">
                <Button variant="ghost" size="sm" className="group">
                  View all
                  <ChevronRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-4">
                <PipelineStage
                  label="Discovered"
                  count={pipelineStats?.by_stage?.discovered || 0}
                  color="gray"
                  total={pipelineStats?.total || 1}
                />
                <PipelineStage
                  label="Preparing"
                  count={pipelineStats?.by_stage?.preparing || 0}
                  color="yellow"
                  total={pipelineStats?.total || 1}
                />
                <PipelineStage
                  label="Submitted"
                  count={pipelineStats?.by_stage?.submitted || 0}
                  color="blue"
                  total={pipelineStats?.total || 1}
                />
                <PipelineStage
                  label="Pending"
                  count={pipelineStats?.by_stage?.pending || 0}
                  color="purple"
                  total={pipelineStats?.total || 1}
                />
                <PipelineStage
                  label="Won"
                  count={pipelineStats?.by_stage?.won || 0}
                  color="green"
                  total={pipelineStats?.total || 1}
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div variants={item}>
        <Card variant="ai" className="overflow-hidden">
          <CardHeader className="border-b border-purple-100/50">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid gap-4 md:grid-cols-3">
              <QuickActionCard
                href="/opportunities"
                icon={<Target className="h-6 w-6" />}
                title="Browse Opportunities"
                description="Explore all available hackathons"
                color="blue"
              />
              <QuickActionCard
                href="/generator"
                icon={<Sparkles className="h-6 w-6" />}
                title="Generate Materials"
                description="Create README, pitch, and more"
                color="purple"
              />
              <QuickActionCard
                href="/profile"
                icon={<TrendingUp className="h-6 w-6" />}
                title="Improve Profile"
                description="Get better matches"
                color="green"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

function StatCard({
  title,
  value,
  icon,
  description,
  color,
  delay,
}: {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  description: string;
  color: "blue" | "green" | "yellow" | "purple";
  delay: number;
}) {
  const colorClasses = {
    blue: {
      bg: "from-blue-500 to-blue-600",
      light: "from-blue-50 to-blue-100/50",
      text: "text-blue-600",
    },
    green: {
      bg: "from-green-500 to-green-600",
      light: "from-green-50 to-green-100/50",
      text: "text-green-600",
    },
    yellow: {
      bg: "from-yellow-500 to-orange-500",
      light: "from-yellow-50 to-orange-50/50",
      text: "text-yellow-600",
    },
    purple: {
      bg: "from-purple-500 to-purple-600",
      light: "from-purple-50 to-purple-100/50",
      text: "text-purple-600",
    },
  };

  const colors = colorClasses[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <Card variant="elevated" className="overflow-hidden group cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">{title}</p>
              <motion.p
                className="text-3xl font-bold mt-1"
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ delay: delay + 0.2, type: "spring" }}
              >
                {value}
              </motion.p>
              <p className="text-xs text-gray-400 mt-1">{description}</p>
            </div>
            <div
              className={`relative p-3 rounded-xl bg-gradient-to-br ${colors.light} group-hover:scale-110 transition-transform duration-300`}
            >
              <div
                className={`absolute inset-0 bg-gradient-to-r ${colors.bg} rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
              />
              <div className={`relative ${colors.text} group-hover:text-white transition-colors`}>
                {icon}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function MatchCard({ match }: { match: any }) {
  const scorePercent = Math.round((match.score || 0) * 100);

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 bg-white hover:border-blue-200 hover:shadow-md transition-all cursor-pointer group"
    >
      <div
        className="relative h-14 w-14 rounded-xl flex items-center justify-center text-white font-bold shadow-lg overflow-hidden"
        style={{
          background: `linear-gradient(135deg, hsl(${Math.min(scorePercent * 1.2, 120)}, 70%, 50%), hsl(${Math.min(scorePercent * 1.2 + 20, 140)}, 70%, 45%))`,
        }}
      >
        <span className="relative z-10">{scorePercent}%</span>
        <div className="absolute inset-0 bg-white/20 shimmer" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate group-hover:text-blue-600 transition-colors">
          {match.opportunity_title}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="secondary" className="text-xs">
            {match.opportunity_category}
          </Badge>
          {match.deadline && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatRelativeTime(match.deadline)}
            </span>
          )}
        </div>
      </div>
      <Link href={`/opportunities/${match.batch_id}`}>
        <Button size="sm" variant="ghost" className="group-hover:bg-blue-50">
          <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
        </Button>
      </Link>
    </motion.div>
  );
}

function PipelineStage({
  label,
  count,
  color,
  total,
}: {
  label: string;
  count: number;
  color: string;
  total: number;
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  const colorClasses: Record<string, { dot: string; bar: string }> = {
    gray: { dot: "bg-gray-400", bar: "from-gray-400 to-gray-500" },
    yellow: { dot: "bg-yellow-500", bar: "from-yellow-400 to-orange-500" },
    blue: { dot: "bg-blue-500", bar: "from-blue-400 to-blue-600" },
    purple: { dot: "bg-purple-500", bar: "from-purple-400 to-purple-600" },
    green: { dot: "bg-green-500", bar: "from-green-400 to-green-600" },
  };

  const colors = colorClasses[color] || colorClasses.gray;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${colors.dot}`} />
          <span className="text-sm font-medium text-gray-700">{label}</span>
        </div>
        <span className="text-sm font-semibold">{count}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full bg-gradient-to-r ${colors.bar} rounded-full`}
        />
      </div>
    </div>
  );
}

function QuickActionCard({
  href,
  icon,
  title,
  description,
  color,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  color: "blue" | "purple" | "green";
}) {
  const colorClasses = {
    blue: {
      bg: "from-blue-500 to-blue-600",
      hover: "hover:border-blue-300 hover:bg-blue-50/50",
    },
    purple: {
      bg: "from-purple-500 to-purple-600",
      hover: "hover:border-purple-300 hover:bg-purple-50/50",
    },
    green: {
      bg: "from-green-500 to-green-600",
      hover: "hover:border-green-300 hover:bg-green-50/50",
    },
  };

  const colors = colorClasses[color];

  return (
    <Link href={href}>
      <motion.div
        whileHover={{ y: -4 }}
        whileTap={{ scale: 0.98 }}
        className={`p-5 rounded-xl border-2 border-transparent bg-white/50 ${colors.hover} transition-all cursor-pointer group`}
      >
        <div
          className={`h-12 w-12 rounded-xl bg-gradient-to-r ${colors.bg} flex items-center justify-center text-white mb-3 group-hover:scale-110 transition-transform shadow-lg`}
        >
          {icon}
        </div>
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </motion.div>
    </Link>
  );
}
