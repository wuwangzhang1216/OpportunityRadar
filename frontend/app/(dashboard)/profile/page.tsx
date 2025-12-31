"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { User, Code, Target, Clock, Save, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api-client";

const techOptions = [
  "JavaScript", "TypeScript", "Python", "Go", "Rust", "Java", "C++",
  "React", "Vue", "Angular", "Next.js", "Node.js", "FastAPI", "Django",
  "PostgreSQL", "MongoDB", "Redis", "AWS", "GCP", "Azure", "Docker", "Kubernetes",
  "Machine Learning", "AI/LLM", "Blockchain", "Mobile", "AR/VR",
];

const industryOptions = [
  "FinTech", "HealthTech", "EdTech", "Climate", "Social Impact",
  "Developer Tools", "Web3", "Gaming", "E-commerce", "Enterprise",
];

const intentOptions = [
  { id: "prize", label: "Win Prizes" },
  { id: "learning", label: "Learn New Skills" },
  { id: "networking", label: "Network" },
  { id: "portfolio", label: "Build Portfolio" },
  { id: "funding", label: "Get Funding" },
  { id: "job", label: "Find Job Opportunities" },
];

const profileSchema = z.object({
  profile_type: z.string().min(1, "Profile type is required"),
  tech_stack: z.array(z.string()).min(1, "Select at least one technology"),
  industries: z.array(z.string()),
  intents: z.array(z.string()).min(1, "Select at least one goal"),
  available_hours_per_week: z.number().min(1).max(168),
  team_size_pref_min: z.number().min(1),
  team_size_pref_max: z.number().min(1),
  region: z.string().optional(),
});

type ProfileForm = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const queryClient = useQueryClient();

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiClient.getProfile(),
  });

  const updateMutation = useMutation({
    mutationFn: (data: ProfileForm) =>
      profile ? apiClient.updateProfile(data) : apiClient.createProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      profile_type: "developer",
      tech_stack: [],
      industries: [],
      intents: [],
      available_hours_per_week: 20,
      team_size_pref_min: 1,
      team_size_pref_max: 4,
      region: "global",
    },
  });

  // Load profile data when available
  useEffect(() => {
    if (profile) {
      reset({
        profile_type: profile.profile_type || "developer",
        tech_stack: profile.tech_stack || [],
        industries: profile.industries || [],
        intents: profile.intents || [],
        available_hours_per_week: profile.available_hours_per_week || 20,
        team_size_pref_min: profile.team_size_pref_min || 1,
        team_size_pref_max: profile.team_size_pref_max || 4,
        region: profile.region || "global",
      });
    }
  }, [profile, reset]);

  const techStack = watch("tech_stack");
  const industries = watch("industries");
  const intents = watch("intents");

  const toggleTech = (tech: string) => {
    const current = techStack || [];
    setValue(
      "tech_stack",
      current.includes(tech)
        ? current.filter((t) => t !== tech)
        : [...current, tech],
      { shouldDirty: true }
    );
  };

  const toggleIndustry = (industry: string) => {
    const current = industries || [];
    setValue(
      "industries",
      current.includes(industry)
        ? current.filter((i) => i !== industry)
        : [...current, industry],
      { shouldDirty: true }
    );
  };

  const toggleIntent = (intent: string) => {
    const current = intents || [];
    setValue(
      "intents",
      current.includes(intent)
        ? current.filter((i) => i !== intent)
        : [...current, intent],
      { shouldDirty: true }
    );
  };

  const onSubmit = (data: ProfileForm) => {
    updateMutation.mutate(data);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <User className="h-8 w-8 text-blue-600" />
            Your Profile
          </h1>
          <p className="text-gray-600 mt-1">
            Tell us about yourself to get better matches
          </p>
        </div>
        {profile && (
          <Badge variant="success">Profile Active</Badge>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Profile Type */}
        <Card>
          <CardHeader>
            <CardTitle>Profile Type</CardTitle>
            <CardDescription>What best describes you?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3 flex-wrap">
              {["developer", "student", "startup", "designer", "researcher"].map(
                (type) => (
                  <Button
                    key={type}
                    type="button"
                    variant={watch("profile_type") === type ? "default" : "outline"}
                    onClick={() => setValue("profile_type", type, { shouldDirty: true })}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Button>
                )
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tech Stack */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Tech Stack
            </CardTitle>
            <CardDescription>Select technologies you work with</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {techOptions.map((tech) => (
                <Badge
                  key={tech}
                  variant={techStack?.includes(tech) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleTech(tech)}
                >
                  {tech}
                </Badge>
              ))}
            </div>
            {errors.tech_stack && (
              <p className="text-red-500 text-sm mt-2">
                {errors.tech_stack.message}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Industries */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Industries of Interest
            </CardTitle>
            <CardDescription>What domains interest you?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {industryOptions.map((industry) => (
                <Badge
                  key={industry}
                  variant={industries?.includes(industry) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleIndustry(industry)}
                >
                  {industry}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Goals */}
        <Card>
          <CardHeader>
            <CardTitle>Your Goals</CardTitle>
            <CardDescription>What do you want to achieve?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {intentOptions.map((intent) => (
                <button
                  key={intent.id}
                  type="button"
                  onClick={() => toggleIntent(intent.id)}
                  className={`p-3 rounded-lg border-2 text-left transition ${
                    intents?.includes(intent.id)
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <span className="font-medium">{intent.label}</span>
                </button>
              ))}
            </div>
            {errors.intents && (
              <p className="text-red-500 text-sm mt-2">
                {errors.intents.message}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Availability */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Availability
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Hours available per week
                </label>
                <Input
                  type="number"
                  {...register("available_hours_per_week", { valueAsNumber: true })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Preferred team size (min)
                  </label>
                  <Input
                    type="number"
                    {...register("team_size_pref_min", { valueAsNumber: true })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Preferred team size (max)
                  </label>
                  <Input
                    type="number"
                    {...register("team_size_pref_max", { valueAsNumber: true })}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Submit */}
        <Button
          type="submit"
          className="w-full"
          disabled={updateMutation.isPending || !isDirty}
        >
          {updateMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              {profile ? "Update Profile" : "Create Profile"}
            </>
          )}
        </Button>

        {updateMutation.isSuccess && (
          <p className="text-green-600 text-center">Profile saved successfully!</p>
        )}
      </form>
    </div>
  );
}
