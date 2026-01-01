"use client";

import { useState } from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOnboardingStore } from "@/stores/onboarding-store";

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
      onChange([...tags, suggestion]);
    }
  };

  const filteredSuggestions = suggestions
    .filter((s) => !tags.includes(s))
    .filter((s) => s.toLowerCase().includes(input.toLowerCase()))
    .slice(0, 5);

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
      {filteredSuggestions.length > 0 && input && (
        <div className="flex flex-wrap gap-1">
          {filteredSuggestions.map((s) => (
            <button
              key={s}
              onClick={() => addSuggestion(s)}
              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
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

  const startEdit = (field: string, currentValue: any) => {
    setEditingField(field);
    setTempValue(currentValue);
  };

  const saveEdit = (field: string) => {
    updateField(field as any, tempValue);
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

  return (
    <div className="space-y-4">
      {extractedProfile && (
        <div className="text-sm text-gray-500 mb-4 text-center">
          We extracted this information from{" "}
          <span className="font-medium">{extractedProfile.source_url}</span>.
          Click to edit any field.
        </div>
      )}

      <div className="space-y-3">
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
