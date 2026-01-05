"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  FileText,
  Mic,
  PlayCircle,
  HelpCircle,
  Copy,
  Check,
  Loader2,
  Wand2,
  Zap,
  Bot,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";

const materialTypes = [
  {
    id: "readme",
    label: "README",
    icon: FileText,
    description: "Project documentation",
    color: "primary",
  },
  {
    id: "pitch_3min",
    label: "3-min Pitch",
    icon: Mic,
    description: "Elevator pitch script",
    color: "purple",
  },
  {
    id: "demo_script",
    label: "Demo Script",
    icon: PlayCircle,
    description: "Live demo guide",
    color: "green",
  },
  {
    id: "qa_pred",
    label: "Q&A Prep",
    icon: HelpCircle,
    description: "Judge question prep",
    color: "orange",
  },
];

const colorClasses: Record<string, { bg: string; border: string; text: string }> = {
  primary: {
    bg: "bg-primary",
    border: "border-primary",
    text: "text-primary",
  },
  purple: {
    bg: "bg-purple-500",
    border: "border-purple-500",
    text: "text-purple-600",
  },
  green: {
    bg: "bg-green-500",
    border: "border-green-500",
    text: "text-green-600",
  },
  orange: {
    bg: "bg-orange-500",
    border: "border-orange-500",
    text: "text-orange-600",
  },
};

const formSchema = z.object({
  projectName: z.string().min(1, "Project name is required"),
  problem: z.string().min(10, "Describe the problem (at least 10 chars)"),
  solution: z.string().min(10, "Describe your solution (at least 10 chars)"),
  techStack: z.string().min(1, "List your tech stack"),
});

type FormData = z.infer<typeof formSchema>;

export default function GeneratorPage() {
  const searchParams = useSearchParams();
  // Support both batch_id and opportunity_id for backwards compatibility
  const opportunityId = searchParams.get("batch_id") || searchParams.get("opportunity_id");

  const [selectedTypes, setSelectedTypes] = useState<string[]>(["readme"]);
  const [generatedContent, setGeneratedContent] = useState<Record<string, string>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const { data: opportunity } = useQuery({
    queryKey: ["opportunity", opportunityId],
    queryFn: () => apiClient.getOpportunity(opportunityId!),
    enabled: !!opportunityId,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      projectName: "",
      problem: "",
      solution: "",
      techStack: "",
    },
  });

  const generateMutation = useMutation({
    mutationFn: (data: FormData) =>
      apiClient.generateMaterials({
        opportunity_id: opportunityId || undefined,
        targets: selectedTypes,
        project_info: {
          name: data.projectName,
          problem: data.problem,
          solution: data.solution,
          tech_stack: data.techStack.split(",").map((t) => t.trim()),
        },
      }),
    onSuccess: (data) => {
      const content: Record<string, string> = {};
      if (data.readme_md) content.readme = data.readme_md;
      if (data.pitch_md) content.pitch_3min = data.pitch_md;
      if (data.demo_script_md) content.demo_script = data.demo_script_md;
      if (data.qa_pred_md) content.qa_pred = data.qa_pred_md;
      setGeneratedContent(content);
      setIsGenerating(false);
    },
    onError: () => {
      setIsGenerating(false);
    },
  });

  const toggleType = (typeId: string) => {
    setSelectedTypes((prev) =>
      prev.includes(typeId)
        ? prev.filter((t) => t !== typeId)
        : [...prev, typeId]
    );
  };

  const copyToClipboard = async (id: string, content: string) => {
    await navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const onSubmit = (data: FormData) => {
    if (selectedTypes.length === 0) {
      alert("Please select at least one material type");
      return;
    }
    setIsGenerating(true);
    generateMutation.mutate(data);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-4xl mx-auto space-y-6"
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 bg-primary rounded-2xl flex items-center justify-center">
            <Sparkles className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              AI Material Generator
            </h1>
            <p className="text-muted-foreground mt-1">
              Generate winning hackathon materials with AI
            </p>
          </div>
        </div>
        {opportunity && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-4"
          >
            <Badge className="bg-sky-100 text-primary border-sky-200">
              <Zap className="h-3 w-3 mr-1" />
              For: {opportunity.title}
            </Badge>
          </motion.div>
        )}
      </motion.div>

      {/* Material Type Selection */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card variant="elevated" className="overflow-hidden">
          <CardHeader className="border-b border-border bg-secondary/30">
            <div className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">What do you need?</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid gap-4 md:grid-cols-4">
              {materialTypes.map((type, index) => {
                const isSelected = selectedTypes.includes(type.id);
                const colors = colorClasses[type.color];
                return (
                  <motion.button
                    key={type.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ y: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => toggleType(type.id)}
                    className={`relative p-5 rounded-xl border-2 text-left transition-all ${
                      isSelected
                        ? `${colors.border} bg-card shadow-sm`
                        : "border-border hover:border-muted-foreground/30 hover:shadow-sm bg-card"
                    }`}
                  >
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute top-2 right-2"
                      >
                        <div className={`h-5 w-5 rounded-full ${colors.bg} flex items-center justify-center`}>
                          <Check className="h-3 w-3 text-white" />
                        </div>
                      </motion.div>
                    )}
                    <div
                      className={`h-12 w-12 rounded-xl ${colors.bg} flex items-center justify-center mb-3`}
                    >
                      <type.icon className="h-6 w-6 text-white" />
                    </div>
                    <p className="font-semibold text-foreground">{type.label}</p>
                    <p className="text-xs text-muted-foreground mt-1">{type.description}</p>
                  </motion.button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Project Info Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card variant="elevated" className="overflow-hidden">
          <CardHeader className="border-b border-border bg-secondary/30">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">Tell us about your project</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Project Name
                </label>
                <Input
                  placeholder="e.g., TaskMaster AI"
                  className="h-12 rounded-xl border-border focus:border-primary focus:ring-primary/20"
                  {...register("projectName")}
                />
                {errors.projectName && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-sm mt-2"
                  >
                    {errors.projectName.message}
                  </motion.p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Problem Statement
                </label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-xl border border-border bg-background px-4 py-3 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 resize-none"
                  placeholder="What problem does your project solve?"
                  {...register("problem")}
                />
                {errors.problem && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-sm mt-2"
                  >
                    {errors.problem.message}
                  </motion.p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Your Solution
                </label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-xl border border-border bg-background px-4 py-3 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 resize-none"
                  placeholder="How does your project solve this problem?"
                  {...register("solution")}
                />
                {errors.solution && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-sm mt-2"
                  >
                    {errors.solution.message}
                  </motion.p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Tech Stack (comma-separated)
                </label>
                <Input
                  placeholder="e.g., React, Node.js, PostgreSQL, OpenAI"
                  className="h-12 rounded-xl border-border focus:border-primary focus:ring-primary/20"
                  {...register("techStack")}
                />
                {errors.techStack && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-sm mt-2"
                  >
                    {errors.techStack.message}
                  </motion.p>
                )}
              </div>

              <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                <Button
                  type="submit"
                  size="lg"
                  className="w-full"
                  disabled={isGenerating || selectedTypes.length === 0}
                >
                  {isGenerating ? (
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <div className="absolute inset-0 h-5 w-5 animate-ping opacity-50">
                          <Sparkles className="h-5 w-5" />
                        </div>
                      </div>
                      <span>AI is generating your materials...</span>
                    </div>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5 mr-2" />
                      Generate Materials
                    </>
                  )}
                </Button>
              </motion.div>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Generating Animation */}
      <AnimatePresence>
        {isGenerating && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card variant="feature" className="overflow-hidden">
              <CardContent className="p-8">
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-6">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                      className="h-20 w-20 rounded-full bg-primary flex items-center justify-center"
                    >
                      <Bot className="h-10 w-10 text-white" />
                    </motion.div>
                  </div>
                  <h3 className="text-xl font-bold text-foreground">
                    AI is working its magic...
                  </h3>
                  <p className="text-muted-foreground mt-2 max-w-md">
                    Our AI is analyzing your project and generating professional
                    hackathon materials. This may take a moment.
                  </p>
                  <div className="flex items-center gap-2 mt-6">
                    {selectedTypes.map((typeId, index) => {
                      const type = materialTypes.find((t) => t.id === typeId);
                      return (
                        <motion.div
                          key={typeId}
                          initial={{ opacity: 0, scale: 0 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          <Badge variant="secondary" className="gap-1">
                            {type?.icon && <type.icon className="h-3 w-3" />}
                            {type?.label}
                          </Badge>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Generated Content */}
      <AnimatePresence>
        {Object.keys(generatedContent).length > 0 && !isGenerating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-green-500 flex items-center justify-center">
                <Check className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-foreground">Generated Materials</h2>
            </div>

            {Object.entries(generatedContent).map(([id, content], index) => {
              const type = materialTypes.find((t) => t.id === id);
              const colors = type ? colorClasses[type.color] : colorClasses.primary;

              return (
                <motion.div
                  key={id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card variant="elevated" className="overflow-hidden">
                    <CardHeader className="flex flex-row items-center justify-between border-b border-border bg-secondary/30">
                      <div className="flex items-center gap-3">
                        <div className={`h-10 w-10 rounded-xl ${colors.bg} flex items-center justify-center`}>
                          {type?.icon && <type.icon className="h-5 w-5 text-white" />}
                        </div>
                        <CardTitle className="text-lg">{type?.label || id}</CardTitle>
                      </div>
                      <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(id, content)}
                          className="gap-2"
                        >
                          <AnimatePresence mode="wait">
                            {copiedId === id ? (
                              <motion.div
                                key="check"
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0 }}
                                className="flex items-center gap-1 text-green-600"
                              >
                                <Check className="h-4 w-4" />
                                Copied!
                              </motion.div>
                            ) : (
                              <motion.div
                                key="copy"
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0 }}
                                className="flex items-center gap-1"
                              >
                                <Copy className="h-4 w-4" />
                                Copy
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </Button>
                      </motion.div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="relative">
                        <pre className="whitespace-pre-wrap text-sm p-6 overflow-x-auto max-h-[400px] bg-secondary/20 scrollbar-modern">
                          {content}
                        </pre>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
