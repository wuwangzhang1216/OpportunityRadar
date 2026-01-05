"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  FileText,
  Code2,
  Briefcase,
  Target,
  Users,
  MapPin,
  Loader2,
  ArrowRight,
  ArrowLeft,
  Check,
  X,
  Pencil,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { ProfileQualityScore } from "@/components/onboarding/profile-quality-score";
import { AIInsightBanner } from "@/components/onboarding/ai-insight-banner";

interface FieldCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | string[] | number;
  confidence?: number;
  onEdit: () => void;
  isEditing: boolean;
  editComponent: React.ReactNode;
  onSave: () => void;
  onCancel: () => void;
}

function FieldCard({
  icon,
  label,
  value,
  confidence,
  onEdit,
  isEditing,
  editComponent,
  onSave,
  onCancel,
}: FieldCardProps) {
  const getConfidenceBadge = () => {
    if (confidence === undefined) return null;
    if (confidence >= 0.8) {
      return <Badge variant="success" size="sm">High confidence</Badge>;
    } else if (confidence >= 0.5) {
      return <Badge variant="warning" size="sm">Medium</Badge>;
    } else {
      return <Badge variant="secondary" size="sm">Low</Badge>;
    }
  };

  const displayValue = () => {
    if (Array.isArray(value)) {
      return value.length > 0 ? value.join(", ") : "(Not set)";
    }
    return value || "(Not set)";
  };

  return (
    <Card variant="outline" className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 flex-1">
            <div className="text-blue-600">{icon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-gray-600">{label}</span>
                {getConfidenceBadge()}
              </div>
              {isEditing ? (
                <div className="space-y-2">
                  {editComponent}
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={onSave}>
                      <Check className="h-3 w-3 mr-1" />
                      Save
                    </Button>
                    <Button size="sm" variant="ghost" onClick={onCancel}>
                      <X className="h-3 w-3 mr-1" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-gray-900 truncate">{displayValue()}</p>
              )}
            </div>
          </div>
          {!isEditing && (
            <button
              onClick={onEdit}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
}

function TagInput({ tags, onChange, suggestions = [], placeholder }: TagInputProps) {
  const [input, setInput] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && input.trim()) {
      e.preventDefault();
      if (!tags.includes(input.trim())) {
        onChange([...tags, input.trim()]);
      }
      setInput("");
    } else if (e.key === "Backspace" && !input && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  const removeTag = (tagToRemove: string) => {
    onChange(tags.filter((t) => t !== tagToRemove));
  };

  const addSuggestion = (suggestion: string) => {
    if (!tags.includes(suggestion)) {
      const newTags = [...tags, suggestion];
      console.log("addSuggestion:", { suggestion, tags, newTags });
      onChange(newTags);
    }
  };

  // Filter suggestions based on input, or show all if no input
  const filteredSuggestions = suggestions
    .filter((s) => !tags.includes(s))
    .filter((s) => !input || s.toLowerCase().includes(input.toLowerCase()))
    .slice(0, input ? 5 : 8); // Show more suggestions when no input

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1 p-2 border rounded-lg bg-white min-h-[40px]">
        {tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="gap-1">
            {tag}
            <button onClick={() => removeTag(tag)} className="hover:text-red-500">
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={tags.length === 0 ? placeholder : "Add more..."}
          className="flex-1 min-w-[100px] outline-none text-sm"
        />
      </div>
      {filteredSuggestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-primary/20 bg-primary/5 p-3"
        >
          <div className="flex items-center gap-1.5 mb-2">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="text-xs font-medium text-primary">AI Suggestions</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {filteredSuggestions.map((s) => (
              <button
                key={s}
                onClick={() => addSuggestion(s)}
                className="text-xs px-2.5 py-1.5 bg-white hover:bg-primary hover:text-white border border-primary/30 rounded-full transition-colors flex items-center gap-1 group"
              >
                <span className="text-primary group-hover:text-white transition-colors">+</span>
                {s}
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

// Accordion Section Component
interface AccordionSectionProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  fieldCount?: number;
  filledCount?: number;
}

function AccordionSection({
  title,
  description,
  icon,
  isOpen,
  onToggle,
  children,
  fieldCount,
  filledCount,
}: AccordionSectionProps) {
  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-secondary/30 hover:bg-secondary/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="text-primary">{icon}</div>
          <div className="text-left">
            <h3 className="font-medium text-sm">{title}</h3>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {fieldCount !== undefined && filledCount !== undefined && (
            <Badge variant={filledCount === fieldCount ? "success" : "secondary"} size="sm">
              {filledCount}/{fieldCount}
            </Badge>
          )}
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          </motion.div>
        </div>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="p-4 space-y-3 border-t border-border">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Step2Confirm() {
  const {
    extractedProfile,
    confirmedData,
    updateField,
    confirmProfile,
    isConfirming,
    confirmError,
    goToStep,
    suggestions,
  } = useOnboardingStore();

  const [editingField, setEditingField] = useState<string | null>(null);
  const [tempValue, setTempValue] = useState<any>(null);
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(["basic"]));

  const toggleSection = (section: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const startEdit = (field: string, currentValue: any) => {
    console.log("startEdit:", { field, currentValue, suggestions });
    setEditingField(field);
    setTempValue(currentValue);
  };

  const saveEdit = (field: string) => {
    console.log("saveEdit called:", { field, tempValue });
    if (tempValue !== null && tempValue !== undefined) {
      updateField(field as any, tempValue);
    }
    setEditingField(null);
    setTempValue(null);
  };

  const cancelEdit = () => {
    setEditingField(null);
    setTempValue(null);
  };

  const handleSubmit = async () => {
    await confirmProfile();
  };

  const getConfidence = (field: string): number | undefined => {
    if (!extractedProfile) return undefined;
    const extracted = (extractedProfile as any)[field];
    return extracted?.confidence;
  };

  // Calculate section completion
  const basicFilled = [
    confirmedData.display_name,
    confirmedData.bio && confirmedData.bio.length > 10,
  ].filter(Boolean).length;

  const techFilled = [
    confirmedData.tech_stack?.length > 0,
    confirmedData.industries?.length > 0,
  ].filter(Boolean).length;

  const goalsFilled = [
    confirmedData.goals?.length > 0,
    confirmedData.team_size,
    confirmedData.location_country,
  ].filter(Boolean).length;

  // Prepare profile data for quality score
  const profileForScore = {
    product_name: confirmedData.display_name,
    description: confirmedData.bio,
    tech_stack: confirmedData.tech_stack,
    industries: confirmedData.industries,
    goals: confirmedData.goals,
    team_size: confirmedData.team_size?.toString(),
    location: confirmedData.location_country,
  };

  return (
    <div className="space-y-6">
      {/* AI Insight Banner */}
      {(confirmedData.tech_stack?.length > 0 || confirmedData.industries?.length > 0) && (
        <AIInsightBanner
          profile={profileForScore}
          urlType={extractedProfile?.source_url?.includes("github") ? "github" : "website"}
        />
      )}

      {/* Profile Quality Score */}
      <ProfileQualityScore profile={profileForScore} />

      {extractedProfile && (
        <div className="text-sm text-muted-foreground text-center flex items-center justify-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span>
            AI extracted from{" "}
            <span className="font-medium text-foreground">{extractedProfile.source_url}</span>
          </span>
        </div>
      )}

      <div className="space-y-3">
        {/* Basic Information - Always expanded by default */}
        <AccordionSection
          title="Basic Information"
          description="Your project or company identity"
          icon={<Building2 className="h-5 w-5" />}
          isOpen={openSections.has("basic")}
          onToggle={() => toggleSection("basic")}
          fieldCount={2}
          filledCount={basicFilled}
        >
          {/* Company/Project Name */}
          <FieldCard
            icon={<Building2 className="h-5 w-5" />}
            label="Name"
            value={confirmedData.display_name}
            confidence={getConfidence("company_name")}
            onEdit={() => startEdit("display_name", confirmedData.display_name)}
            isEditing={editingField === "display_name"}
            editComponent={
              <Input
                value={tempValue || ""}
                onChange={(e) => setTempValue(e.target.value)}
                placeholder="Your company or project name"
              />
            }
            onSave={() => saveEdit("display_name")}
            onCancel={cancelEdit}
          />

          {/* Bio/Description */}
          <FieldCard
            icon={<FileText className="h-5 w-5" />}
            label="Description"
            value={confirmedData.bio}
            confidence={getConfidence("product_description")}
            onEdit={() => startEdit("bio", confirmedData.bio)}
            isEditing={editingField === "bio"}
            editComponent={
              <textarea
                value={tempValue || ""}
                onChange={(e) => setTempValue(e.target.value)}
                placeholder="Brief description of what you do"
                className="w-full p-2 border rounded-lg text-sm min-h-[80px]"
              />
            }
            onSave={() => saveEdit("bio")}
            onCancel={cancelEdit}
          />
        </AccordionSection>

        {/* Tech DNA */}
        <AccordionSection
          title="Tech DNA"
          description="Technologies and industries you work with"
          icon={<Code2 className="h-5 w-5" />}
          isOpen={openSections.has("tech")}
          onToggle={() => toggleSection("tech")}
          fieldCount={2}
          filledCount={techFilled}
        >
          {/* Tech Stack */}
          <FieldCard
            icon={<Code2 className="h-5 w-5" />}
            label="Tech Stack"
            value={confirmedData.tech_stack}
            confidence={getConfidence("tech_stack")}
            onEdit={() => startEdit("tech_stack", confirmedData.tech_stack)}
            isEditing={editingField === "tech_stack"}
            editComponent={
              <TagInput
                tags={tempValue || []}
                onChange={setTempValue}
                suggestions={suggestions?.tech_stacks}
                placeholder="Add technologies..."
              />
            }
            onSave={() => saveEdit("tech_stack")}
            onCancel={cancelEdit}
          />

          {/* Industries */}
          <FieldCard
            icon={<Briefcase className="h-5 w-5" />}
            label="Industries"
            value={confirmedData.industries}
            confidence={getConfidence("industries")}
            onEdit={() => startEdit("industries", confirmedData.industries)}
            isEditing={editingField === "industries"}
            editComponent={
              <TagInput
                tags={tempValue || []}
                onChange={setTempValue}
                suggestions={suggestions?.industries}
                placeholder="Add industries..."
              />
            }
            onSave={() => saveEdit("industries")}
            onCancel={cancelEdit}
          />
        </AccordionSection>

        {/* Goals & Context */}
        <AccordionSection
          title="Goals & Context"
          description="What you're looking to achieve"
          icon={<Target className="h-5 w-5" />}
          isOpen={openSections.has("goals")}
          onToggle={() => toggleSection("goals")}
          fieldCount={3}
          filledCount={goalsFilled}
        >
          {/* Goals */}
          <FieldCard
            icon={<Target className="h-5 w-5" />}
            label="Goals"
            value={confirmedData.goals}
            confidence={getConfidence("goals")}
            onEdit={() => startEdit("goals", confirmedData.goals)}
            isEditing={editingField === "goals"}
            editComponent={
              <TagInput
                tags={tempValue || []}
                onChange={setTempValue}
                suggestions={suggestions?.goals}
                placeholder="What are you looking to achieve?"
              />
            }
            onSave={() => saveEdit("goals")}
            onCancel={cancelEdit}
          />

          {/* Team Size */}
          <FieldCard
            icon={<Users className="h-5 w-5" />}
            label="Team Size"
            value={confirmedData.team_size}
            confidence={getConfidence("team_size")}
            onEdit={() => startEdit("team_size", confirmedData.team_size)}
            isEditing={editingField === "team_size"}
            editComponent={
              <Input
                type="number"
                min={1}
                max={100}
                value={tempValue || 1}
                onChange={(e) => setTempValue(parseInt(e.target.value) || 1)}
              />
            }
            onSave={() => saveEdit("team_size")}
            onCancel={cancelEdit}
          />

          {/* Location */}
          <FieldCard
            icon={<MapPin className="h-5 w-5" />}
            label="Location"
            value={confirmedData.location_country}
            confidence={getConfidence("location")}
            onEdit={() => startEdit("location_country", confirmedData.location_country)}
            isEditing={editingField === "location_country"}
            editComponent={
              <Input
                value={tempValue || ""}
                onChange={(e) => setTempValue(e.target.value)}
                placeholder="Country or region"
              />
            }
            onSave={() => saveEdit("location_country")}
            onCancel={cancelEdit}
          />
        </AccordionSection>
      </div>

      {confirmError && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
          {confirmError}
        </div>
      )}

      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          onClick={() => goToStep(1)}
          disabled={isConfirming}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button
          className="flex-1"
          onClick={handleSubmit}
          disabled={isConfirming}
        >
          {isConfirming ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating profile...
            </>
          ) : (
            <>
              Continue
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
