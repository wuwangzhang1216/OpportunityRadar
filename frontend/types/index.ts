export interface User {
  id: string;
  email: string;
  full_name: string;
  has_profile: boolean;
  created_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  profile_type: string;
  tech_stack: string[];
  industries: string[];
  intents: string[];
  available_hours_per_week: number;
  team_size_pref_min: number;
  team_size_pref_max: number;
  region: string;
  stage?: string;
  created_at: string;
  updated_at: string;
}

export interface Opportunity {
  id: string;
  title: string;
  description?: string;
  category: string;
  source: string;
  tags: string[];
  industry: string[];
  tech_stack: string[];
  url?: string;
  image_url?: string;
  host_name?: string;
  created_at: string;
}

export interface Batch {
  id: string;
  opportunity_id: string;
  year?: number;
  season?: string;
  remote_ok: boolean;
  regions: string[];
  team_min: number;
  team_max?: number;
  student_only: boolean;
  status: string;
}

export interface Timeline {
  id: string;
  batch_id: string;
  registration_start?: string;
  registration_end?: string;
  submission_start?: string;
  submission_end?: string;
  judging_start?: string;
  judging_end?: string;
  announcement?: string;
}

export interface Prize {
  id: string;
  batch_id: string;
  name: string;
  description?: string;
  amount?: number;
  currency: string;
  rank?: number;
}

export interface Match {
  id: string;
  profile_id: string;
  batch_id: string;
  score: number;
  reasons: string[];
  status: string;
  opportunity_title?: string;
  opportunity_category?: string;
  deadline?: string;
}

export interface Pipeline {
  id: string;
  user_id: string;
  batch_id: string;
  stage: string;
  eta_hours?: number;
  deadline_at?: string;
  notes?: string;
  opportunity_title?: string;
  opportunity_category?: string;
  created_at: string;
  updated_at: string;
}

export interface Material {
  id: string;
  user_id: string;
  batch_id?: string;
  material_type: string;
  content: string;
  version: number;
  metadata: Record<string, any>;
  created_at: string;
}

export type PipelineStage =
  | "discovered"
  | "preparing"
  | "submitted"
  | "pending"
  | "won"
  | "lost";

export type MaterialType =
  | "readme"
  | "pitch_1min"
  | "pitch_3min"
  | "pitch_5min"
  | "demo_script"
  | "qa_pred";
