export interface User {
  id: string;
  email: string;
  full_name: string;
  has_profile: boolean;
  avatar_url?: string;
  oauth_connections?: OAuthConnection[];
  created_at: string;
  last_login_at?: string;
}

export interface OAuthConnection {
  provider: "github" | "google";
  provider_id: string;
  connected_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  display_name?: string;
  bio?: string;
  profile_type: string;
  tech_stack: string[];
  industries: string[];
  intents: string[];
  skills: string[];
  interests: string[];
  goals: string[];
  experience_level?: string;
  available_hours_per_week: number;
  preferred_team_size?: number;
  team_size_pref_min: number;
  team_size_pref_max: number;
  region: string;
  location?: string;
  timezone?: string;
  stage?: string;
  // Team/Company fields
  team_name?: string;
  team_size?: number;
  company_stage?: "idea" | "prototype" | "mvp" | "launched" | "revenue" | "funded";
  funding_stage?: "pre_seed" | "seed" | "series_a" | "series_b" | "series_c_plus" | "bootstrapped";
  seeking_funding?: boolean;
  funding_amount_seeking?: string;
  product_name?: string;
  product_description?: string;
  product_url?: string;
  product_stage?: "concept" | "development" | "beta" | "launched" | "scaling";
  team_members?: TeamMember[];
  previous_accelerators?: string[];
  previous_hackathon_wins?: number;
  notable_achievements?: string[];
  // Social links
  github_url?: string;
  linkedin_url?: string;
  twitter_url?: string;
  portfolio_url?: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  name: string;
  role: string;
  email?: string;
  linkedin_url?: string;
}

export interface Opportunity {
  id: string;
  title: string;
  slug?: string;
  description?: string;
  short_description?: string;
  category: string;
  opportunity_type: string;
  format?: "online" | "in-person" | "hybrid";
  source: string;
  tags: string[];
  themes: string[];
  industry: string[];
  tech_stack: string[];
  technologies: string[];
  url?: string;
  website_url?: string;
  registration_url?: string;
  image_url?: string;
  logo_url?: string;
  banner_url?: string;
  host_name?: string;
  // Location
  location_type?: string;
  location_city?: string;
  location_country?: string;
  location_region?: string;
  // Prizes
  total_prize_value?: number;
  currency: string;
  prizes?: Prize[];
  // Team
  team_size_min?: number;
  team_size_max?: number;
  participant_count?: number;
  // Dates
  application_deadline?: string;
  event_start_date?: string;
  event_end_date?: string;
  results_date?: string;
  // Enhanced details
  eligibility_criteria?: string[];
  submission_requirements?: string[];
  judging_criteria?: JudgingCriteria[];
  mentor_info?: MentorInfo[];
  resources?: Resource[];
  faq?: FAQ[];
  // Metadata
  difficulty_level?: "beginner" | "intermediate" | "advanced";
  expected_duration_hours?: number;
  is_student_only?: boolean;
  age_requirement?: string;
  geographic_restriction?: string;
  // Social
  social_links?: Record<string, string>;
  video_url?: string;
  // Status
  is_featured?: boolean;
  is_active?: boolean;
  is_open?: boolean;
  days_until_deadline?: number;
  created_at: string;
  updated_at?: string;
}

export interface JudgingCriteria {
  name: string;
  weight?: number;
  description?: string;
}

export interface MentorInfo {
  name: string;
  title?: string;
  company?: string;
  expertise?: string[];
}

export interface Resource {
  name: string;
  type: string;
  url?: string;
  description?: string;
}

export interface FAQ {
  question: string;
  answer: string;
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
  _id?: string;
  user_id: string;
  opportunity_id: string;
  batch_id?: string;  // Alias for opportunity_id (frontend compatibility)
  // Scores
  overall_score: number;
  score?: number;  // Alias for overall_score
  semantic_score?: number;
  score_breakdown?: Record<string, number>;
  // Eligibility
  eligibility_status?: "eligible" | "ineligible" | "partial";
  eligibility_issues?: string[];
  fix_suggestions?: string[];
  reasons?: string[];  // Legacy alias
  // User actions
  is_bookmarked: boolean;
  is_dismissed: boolean;
  // Enriched opportunity data
  opportunity_title?: string;
  opportunity_category?: string;
  opportunity_type?: string;
  opportunity_description?: string;
  opportunity_url?: string;
  opportunity_prize_pool?: number;
  deadline?: string;
  // Timestamps
  created_at?: string;
  updated_at?: string;
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

// Onboarding types
export type URLType = "website" | "github_repo";

export interface ExtractedField {
  value: string | string[] | number | null;
  confidence: number;
  source: string;
}

export interface ExtractedProfile {
  url_type: URLType;
  source_url: string;
  company_name?: ExtractedField;
  product_description?: ExtractedField;
  tech_stack?: ExtractedField;
  industries?: ExtractedField;
  team_size?: ExtractedField;
  profile_type?: ExtractedField;
  location?: ExtractedField;
  goals?: ExtractedField;
  raw_content_preview?: string;
}

export interface URLExtractRequest {
  url: string;
}

export interface URLExtractResponse {
  success: boolean;
  extracted_profile?: ExtractedProfile;
  error_message?: string;
}

export interface OnboardingConfirmRequest {
  display_name?: string;
  bio?: string;
  tech_stack: string[];
  industries: string[];
  goals: string[];
  interests: string[];
  experience_level?: string;
  team_size: number;
  profile_type: string;
  location_country?: string;
  location_region?: string;
  source_url?: string;
}

export interface OnboardingConfirmResponse {
  success: boolean;
  profile_id?: string;
  onboarding_completed: boolean;
  error_message?: string;
}

export interface OnboardingStatusResponse {
  has_profile: boolean;
  onboarding_completed: boolean;
  profile_id?: string;
}

export interface OnboardingSuggestions {
  tech_stacks: string[];
  goals: string[];
  industries: string[];
}

// ==================== Notifications ====================
export type NotificationType =
  | "deadline_reminder"
  | "new_match"
  | "match_update"
  | "team_invite"
  | "team_update"
  | "submission_status"
  | "system";

export interface Notification {
  id: string;
  user_id: string;
  notification_type: NotificationType;
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface NotificationPreferences {
  id: string;
  user_id: string;
  email_enabled: boolean;
  email_deadline_reminders: boolean;
  email_new_matches: boolean;
  email_team_updates: boolean;
  in_app_enabled: boolean;
  reminder_days: number[];
  created_at: string;
  updated_at: string;
}

// ==================== Teams ====================
export type TeamRole = "owner" | "admin" | "member";

export interface TeamMemberInfo {
  user_id: string;
  email: string;
  full_name?: string;
  role: TeamRole;
  joined_at: string;
}

export interface TeamInvite {
  id: string;
  email: string;
  role: TeamRole;
  invite_code: string;
  expires_at: string;
  created_at: string;
}

export interface SharedOpportunity {
  opportunity_id: string;
  shared_by: string;
  shared_by_name: string;
  note?: string;
  shared_at: string;
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  description?: string;
  owner_id: string;
  members: TeamMemberInfo[];
  pending_invites: TeamInvite[];
  shared_opportunities: SharedOpportunity[];
  created_at: string;
  updated_at: string;
}

// ==================== Submissions ====================
export type SubmissionStatus = "pending" | "approved" | "rejected" | "needs_info";

export interface ReviewNote {
  reviewer_id: string;
  note: string;
  status_change?: string;
  created_at: string;
}

export interface OpportunitySubmission {
  id: string;
  submitted_by: string;
  submitter_email: string;
  title: string;
  description: string;
  opportunity_type: string;
  format?: string;
  website_url: string;
  logo_url?: string;
  host_name: string;
  host_website?: string;
  location_type?: string;
  location_city?: string;
  location_country?: string;
  application_deadline?: string;
  event_start_date?: string;
  event_end_date?: string;
  themes: string[];
  technologies: string[];
  total_prize_value?: number;
  currency: string;
  team_size_min?: number;
  team_size_max?: number;
  eligibility_notes?: string;
  contact_email?: string;
  social_links: Record<string, string>;
  status: SubmissionStatus;
  review_notes: ReviewNote[];
  opportunity_id?: string;
  created_at: string;
  updated_at: string;
}

export interface SubmissionStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  needs_info: number;
}

// ==================== Community / Shared Lists ====================
export type ListVisibility = "private" | "unlisted" | "public";

export interface ListComment {
  user_id: string;
  user_name: string;
  content: string;
  created_at: string;
}

export interface OpportunityBrief {
  id: string;
  title: string;
  opportunity_type: string;
  website_url?: string;
  application_deadline?: string;
  total_prize_value?: number;
}

export interface SharedList {
  id: string;
  owner_id: string;
  owner_name: string;
  title: string;
  slug: string;
  description?: string;
  cover_image_url?: string;
  visibility: ListVisibility;
  opportunity_count: number;
  tags: string[];
  view_count: number;
  like_count: number;
  is_liked: boolean;
  comment_count: number;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface SharedListDetail extends SharedList {
  opportunities: OpportunityBrief[];
  comments: ListComment[];
}

export interface ShareLinks {
  url: string;
  embed_code?: string;
}

// ==================== Calendar ====================
export interface CalendarUrls {
  google_url?: string;
  outlook_url?: string;
  ical_url?: string;
}

// ==================== Export ====================
export type ExportFormat = "json" | "csv";
