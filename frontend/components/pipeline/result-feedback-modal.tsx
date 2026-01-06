"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Trophy,
  X,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  Target,
  Clock,
  FileText,
  Users,
  TrendingUp,
  Star,
  MessageSquare,
  ChevronRight,
  Sparkles,
  Award,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface ResultFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: {
    id: string;
    title: string;
    category?: string;
    deadline?: string;
  };
  onSubmit: (result: ResultFeedback) => void;
}

interface ResultFeedback {
  outcome: "won" | "lost" | "withdrew";
  placement?: string; // e.g., "1st place", "finalist", "honorable mention"
  prizeWon?: number;
  lessonsLearned?: string;
  whatWorked?: string[];
  whatDidntWork?: string[];
  wouldApplyAgain: boolean;
  difficultyRating?: number; // 1-5
  timeSpent?: number; // hours
  teamSize?: number;
  feedback?: string; // any additional notes
}

const successFactors = [
  { id: "strong_pitch", label: "Strong pitch/presentation" },
  { id: "innovative_idea", label: "Innovative idea" },
  { id: "technical_execution", label: "Technical execution" },
  { id: "team_collaboration", label: "Team collaboration" },
  { id: "demo_quality", label: "Demo quality" },
  { id: "user_research", label: "User research" },
  { id: "time_management", label: "Time management" },
  { id: "networking", label: "Networking/judging interaction" },
];

const challengeFactors = [
  { id: "time_pressure", label: "Time pressure" },
  { id: "technical_issues", label: "Technical issues" },
  { id: "scope_creep", label: "Scope creep" },
  { id: "team_coordination", label: "Team coordination" },
  { id: "unclear_requirements", label: "Unclear requirements" },
  { id: "demo_problems", label: "Demo problems" },
  { id: "burnout", label: "Burnout/fatigue" },
  { id: "competition", label: "Strong competition" },
];

export function ResultFeedbackModal({
  isOpen,
  onClose,
  opportunity,
  onSubmit,
}: ResultFeedbackModalProps) {
  const [step, setStep] = useState(1);
  const [outcome, setOutcome] = useState<"won" | "lost" | "withdrew" | null>(null);
  const [placement, setPlacement] = useState("");
  const [prizeWon, setPrizeWon] = useState("");
  const [whatWorked, setWhatWorked] = useState<string[]>([]);
  const [whatDidntWork, setWhatDidntWork] = useState<string[]>([]);
  const [wouldApplyAgain, setWouldApplyAgain] = useState<boolean | null>(null);
  const [difficultyRating, setDifficultyRating] = useState<number>(3);
  const [timeSpent, setTimeSpent] = useState("");
  const [feedback, setFeedback] = useState("");

  const handleSubmit = () => {
    if (!outcome) return;

    onSubmit({
      outcome,
      placement: placement || undefined,
      prizeWon: prizeWon ? parseInt(prizeWon) : undefined,
      whatWorked,
      whatDidntWork,
      wouldApplyAgain: wouldApplyAgain ?? true,
      difficultyRating,
      timeSpent: timeSpent ? parseInt(timeSpent) : undefined,
      feedback: feedback || undefined,
    });

    onClose();
  };

  const toggleFactor = (factorId: string, type: "worked" | "didntWork") => {
    if (type === "worked") {
      setWhatWorked((prev) =>
        prev.includes(factorId)
          ? prev.filter((f) => f !== factorId)
          : [...prev, factorId]
      );
    } else {
      setWhatDidntWork((prev) =>
        prev.includes(factorId)
          ? prev.filter((f) => f !== factorId)
          : [...prev, factorId]
      );
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="fixed inset-4 md:inset-10 lg:inset-y-10 lg:inset-x-[20%] bg-card border border-border rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-secondary/30">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold">Log Your Result</h2>
              <p className="text-xs text-muted-foreground">{opportunity.title}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Progress indicator */}
        <div className="px-6 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step >= s
                      ? "bg-primary text-white"
                      : "bg-secondary text-muted-foreground"
                  }`}
                >
                  {s}
                </div>
                {s < 3 && (
                  <div
                    className={`w-12 h-1 rounded-full ${
                      step > s ? "bg-primary" : "bg-secondary"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            <span>Outcome</span>
            <span>Reflection</span>
            <span>Details</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            {/* Step 1: Outcome */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold mb-2">How did it go?</h3>
                  <p className="text-muted-foreground">
                    Select the outcome of your submission
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <button
                    onClick={() => setOutcome("won")}
                    className={`p-6 rounded-xl border-2 text-center transition-all ${
                      outcome === "won"
                        ? "border-green-500 bg-green-500/10"
                        : "border-border hover:border-green-500/50"
                    }`}
                  >
                    <Trophy className={`h-12 w-12 mx-auto mb-3 ${
                      outcome === "won" ? "text-green-500" : "text-muted-foreground"
                    }`} />
                    <p className="font-semibold text-lg">Won!</p>
                    <p className="text-sm text-muted-foreground">
                      Placed or received recognition
                    </p>
                  </button>

                  <button
                    onClick={() => setOutcome("lost")}
                    className={`p-6 rounded-xl border-2 text-center transition-all ${
                      outcome === "lost"
                        ? "border-orange-500 bg-orange-500/10"
                        : "border-border hover:border-orange-500/50"
                    }`}
                  >
                    <Target className={`h-12 w-12 mx-auto mb-3 ${
                      outcome === "lost" ? "text-orange-500" : "text-muted-foreground"
                    }`} />
                    <p className="font-semibold text-lg">Didn't Win</p>
                    <p className="text-sm text-muted-foreground">
                      Submitted but didn't place
                    </p>
                  </button>

                  <button
                    onClick={() => setOutcome("withdrew")}
                    className={`p-6 rounded-xl border-2 text-center transition-all ${
                      outcome === "withdrew"
                        ? "border-gray-500 bg-gray-500/10"
                        : "border-border hover:border-gray-500/50"
                    }`}
                  >
                    <X className={`h-12 w-12 mx-auto mb-3 ${
                      outcome === "withdrew" ? "text-gray-500" : "text-muted-foreground"
                    }`} />
                    <p className="font-semibold text-lg">Withdrew</p>
                    <p className="text-sm text-muted-foreground">
                      Decided not to continue
                    </p>
                  </button>
                </div>

                {outcome === "won" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="space-y-4 pt-4"
                  >
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        Placement/Recognition
                      </label>
                      <Input
                        placeholder="e.g., 1st place, Best UI, Finalist"
                        value={placement}
                        onChange={(e) => setPlacement(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        Prize Won ($)
                      </label>
                      <Input
                        type="number"
                        placeholder="0"
                        value={prizeWon}
                        onChange={(e) => setPrizeWon(e.target.value)}
                      />
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Step 2: Reflection */}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold mb-2">
                    {outcome === "won" ? "What contributed to your success?" : "What can you learn from this?"}
                  </h3>
                  <p className="text-muted-foreground">
                    This helps improve future recommendations
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-3 flex items-center gap-2">
                    <ThumbsUp className="h-4 w-4 text-green-500" />
                    What worked well?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {successFactors.map((factor) => (
                      <button
                        key={factor.id}
                        onClick={() => toggleFactor(factor.id, "worked")}
                        className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                          whatWorked.includes(factor.id)
                            ? "bg-green-500 text-white"
                            : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                        }`}
                      >
                        {whatWorked.includes(factor.id) && "✓ "}
                        {factor.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-3 flex items-center gap-2">
                    <ThumbsDown className="h-4 w-4 text-orange-500" />
                    What were the challenges?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {challengeFactors.map((factor) => (
                      <button
                        key={factor.id}
                        onClick={() => toggleFactor(factor.id, "didntWork")}
                        className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                          whatDidntWork.includes(factor.id)
                            ? "bg-orange-500 text-white"
                            : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                        }`}
                      >
                        {whatDidntWork.includes(factor.id) && "✓ "}
                        {factor.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-3 block">
                    Would you apply to similar opportunities again?
                  </label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setWouldApplyAgain(true)}
                      className={`flex-1 p-4 rounded-xl border-2 text-center transition-all ${
                        wouldApplyAgain === true
                          ? "border-green-500 bg-green-500/10"
                          : "border-border hover:border-green-500/50"
                      }`}
                    >
                      <ThumbsUp className={`h-6 w-6 mx-auto mb-2 ${
                        wouldApplyAgain === true ? "text-green-500" : "text-muted-foreground"
                      }`} />
                      <p className="font-medium">Yes</p>
                    </button>
                    <button
                      onClick={() => setWouldApplyAgain(false)}
                      className={`flex-1 p-4 rounded-xl border-2 text-center transition-all ${
                        wouldApplyAgain === false
                          ? "border-red-500 bg-red-500/10"
                          : "border-border hover:border-red-500/50"
                      }`}
                    >
                      <ThumbsDown className={`h-6 w-6 mx-auto mb-2 ${
                        wouldApplyAgain === false ? "text-red-500" : "text-muted-foreground"
                      }`} />
                      <p className="font-medium">No</p>
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 3: Details */}
            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold mb-2">Final details</h3>
                  <p className="text-muted-foreground">
                    Optional info to help track your progress
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-3 block">
                    How difficult was this? (1 = Easy, 5 = Very Hard)
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => setDifficultyRating(rating)}
                        className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all ${
                          difficultyRating === rating
                            ? "border-primary bg-primary text-white"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-2">
                    <span>Easy</span>
                    <span>Very Hard</span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Approximate time spent (hours)
                  </label>
                  <Input
                    type="number"
                    placeholder="e.g., 48"
                    value={timeSpent}
                    onChange={(e) => setTimeSpent(e.target.value)}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Any additional notes or lessons?
                  </label>
                  <textarea
                    className="w-full min-h-[100px] p-3 rounded-xl border border-border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="What would you do differently next time?"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                  />
                </div>

                {/* Summary */}
                <Card className="bg-secondary/30">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Summary</span>
                    </div>
                    <div className="grid gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Outcome:</span>
                        <span className="font-medium capitalize">{outcome}</span>
                      </div>
                      {placement && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Placement:</span>
                          <span className="font-medium">{placement}</span>
                        </div>
                      )}
                      {prizeWon && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Prize:</span>
                          <span className="font-medium text-green-600">${prizeWon}</span>
                        </div>
                      )}
                      {whatWorked.length > 0 && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Strengths:</span>
                          <span className="font-medium">{whatWorked.length} factors</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-secondary/20">
          <Button
            variant="ghost"
            onClick={() => (step > 1 ? setStep(step - 1) : onClose())}
          >
            {step > 1 ? "Back" : "Cancel"}
          </Button>
          <Button
            onClick={() => (step < 3 ? setStep(step + 1) : handleSubmit())}
            disabled={step === 1 && !outcome}
          >
            {step < 3 ? (
              <>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Save & Learn
              </>
            )}
          </Button>
        </div>
      </motion.div>
    </>
  );
}
