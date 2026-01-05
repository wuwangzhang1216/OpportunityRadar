import axios, { AxiosError, AxiosInstance } from "axios";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "") + "/api/v1";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Don't auto-redirect on 401 - let the auth store handle it
        // This prevents redirect loops and allows proper error handling
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("auth_token");
  }

  setToken(token: string): void {
    localStorage.setItem("auth_token", token);
  }

  clearToken(): void {
    localStorage.removeItem("auth_token");
  }

  // Auth
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await this.client.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  }

  async signup(email: string, password: string, fullName: string) {
    const response = await this.client.post("/auth/signup", {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async getMe() {
    const response = await this.client.get("/auth/me");
    return response.data;
  }

  // Opportunities
  async getOpportunities(params?: {
    category?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) {
    const response = await this.client.get("/opportunities", { params });
    return response.data;
  }

  async getOpportunity(id: string) {
    const response = await this.client.get(`/opportunities/${id}`);
    return response.data;
  }

  // Profile
  async getProfile() {
    const response = await this.client.get("/profiles/me");
    return response.data;
  }

  async createProfile(data: any) {
    const response = await this.client.post("/profiles", data);
    return response.data;
  }

  async updateProfile(data: any) {
    const response = await this.client.put("/profiles/me", data);
    return response.data;
  }

  // Matches
  async getTopMatches(limit: number = 10) {
    const response = await this.client.get("/matches/top", { params: { limit } });
    return response.data;
  }

  async getMatches(params?: { status?: string; skip?: number; limit?: number }) {
    const response = await this.client.get("/matches", { params });
    return response.data;
  }

  async dismissMatch(batchId: string) {
    const response = await this.client.post(`/matches/${batchId}/dismiss`);
    return response.data;
  }

  async markInterested(batchId: string) {
    const response = await this.client.post(`/matches/${batchId}/interested`);
    return response.data;
  }

  // Pipeline
  async getPipelines(params?: { stage?: string; skip?: number; limit?: number }) {
    const response = await this.client.get("/pipelines", { params });
    return response.data;
  }

  async getPipelineStats() {
    const response = await this.client.get("/pipelines/stats");
    return response.data;
  }

  async addToPipeline(batchId: string, stage: string = "discovered") {
    const response = await this.client.post("/pipelines", {
      batch_id: batchId,
      stage,
    });
    return response.data;
  }

  async updatePipeline(pipelineId: string, data: { stage?: string; notes?: string }) {
    const response = await this.client.patch(`/pipelines/${pipelineId}`, data);
    return response.data;
  }

  async movePipelineStage(pipelineId: string, stage: string) {
    const response = await this.client.post(
      `/pipelines/${pipelineId}/stage/${stage}`
    );
    return response.data;
  }

  // Materials
  async generateMaterials(data: {
    opportunity_id?: string;
    targets: string[];
    project_info: {
      name: string;
      problem: string;
      solution: string;
      tech_stack: string[];
    };
  }) {
    const response = await this.client.post("/materials/generate", data);
    return response.data;
  }

  async getMaterials(params?: { opportunity_id?: string; material_type?: string }) {
    const response = await this.client.get("/materials", { params });
    return response.data;
  }

  async getMaterial(materialId: string) {
    const response = await this.client.get(`/materials/${materialId}`);
    return response.data;
  }

  // Onboarding
  async extractProfileFromUrl(url: string) {
    const response = await this.client.post("/onboarding/extract", { url });
    return response.data;
  }

  async confirmOnboarding(data: {
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
  }) {
    const response = await this.client.post("/onboarding/confirm", data);
    return response.data;
  }

  async getOnboardingStatus() {
    const response = await this.client.get("/onboarding/status");
    return response.data;
  }

  async getOnboardingSuggestions() {
    const response = await this.client.get("/onboarding/suggestions");
    return response.data;
  }

  // Admin - Analytics
  async getAdminAnalytics() {
    const response = await this.client.get("/admin/analytics/overview");
    return response.data;
  }

  // Admin - Opportunities
  async getAdminOpportunities(params?: {
    search?: string;
    category?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) {
    const response = await this.client.get("/admin/opportunities", { params });
    return response.data;
  }

  async getAdminOpportunity(id: string) {
    const response = await this.client.get(`/admin/opportunities/${id}`);
    return response.data;
  }

  async createAdminOpportunity(data: any) {
    const response = await this.client.post("/admin/opportunities", data);
    return response.data;
  }

  async updateAdminOpportunity(id: string, data: any) {
    const response = await this.client.patch(`/admin/opportunities/${id}`, data);
    return response.data;
  }

  async deleteAdminOpportunity(id: string, hard: boolean = false) {
    const response = await this.client.delete(`/admin/opportunities/${id}`, {
      params: hard ? { hard: true } : undefined,
    });
    return response.data;
  }

  async bulkActionOpportunities(action: "activate" | "deactivate" | "delete", ids: string[]) {
    const response = await this.client.post("/admin/opportunities/bulk-action", {
      action,
      ids,
    });
    return response.data;
  }

  async importOpportunities(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await this.client.post("/admin/opportunities/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  }

  // ==================== OAuth ====================
  async getOAuthUrl(provider: "github" | "google") {
    const response = await this.client.get(`/auth/oauth/${provider}/authorize`);
    return response.data;
  }

  async handleOAuthCallback(provider: "github" | "google", code: string, state?: string) {
    const response = await this.client.post(`/auth/oauth/${provider}/callback`, {
      code,
      state,
    });
    return response.data;
  }

  async getOAuthConnections() {
    const response = await this.client.get("/auth/oauth/connections");
    return response.data;
  }

  async disconnectOAuth(provider: "github" | "google") {
    const response = await this.client.delete(`/auth/oauth/${provider}/disconnect`);
    return response.data;
  }

  // ==================== Notifications ====================
  async getNotifications(params?: { unread_only?: boolean; skip?: number; limit?: number }) {
    const response = await this.client.get("/notifications", { params });
    return response.data;
  }

  async getUnreadCount() {
    const response = await this.client.get("/notifications/unread-count");
    return response.data;
  }

  async markNotificationRead(notificationId: string) {
    const response = await this.client.post(`/notifications/${notificationId}/read`);
    return response.data;
  }

  async markAllNotificationsRead() {
    const response = await this.client.post("/notifications/read-all");
    return response.data;
  }

  async getNotificationPreferences() {
    const response = await this.client.get("/notifications/preferences");
    return response.data;
  }

  async updateNotificationPreferences(data: {
    email_enabled?: boolean;
    email_deadline_reminders?: boolean;
    email_new_matches?: boolean;
    email_team_updates?: boolean;
    in_app_enabled?: boolean;
    reminder_days?: number[];
  }) {
    const response = await this.client.put("/notifications/preferences", data);
    return response.data;
  }

  // ==================== Teams ====================
  async getMyTeams() {
    const response = await this.client.get("/teams");
    return response.data;
  }

  async createTeam(data: { name: string; description?: string }) {
    const response = await this.client.post("/teams", data);
    return response.data;
  }

  async getTeam(teamId: string) {
    const response = await this.client.get(`/teams/${teamId}`);
    return response.data;
  }

  async updateTeam(teamId: string, data: { name?: string; description?: string }) {
    const response = await this.client.patch(`/teams/${teamId}`, data);
    return response.data;
  }

  async deleteTeam(teamId: string) {
    const response = await this.client.delete(`/teams/${teamId}`);
    return response.data;
  }

  async inviteToTeam(teamId: string, email: string, role: string = "member") {
    const response = await this.client.post(`/teams/${teamId}/invite`, { email, role });
    return response.data;
  }

  async joinTeam(inviteCode: string) {
    const response = await this.client.post(`/teams/join/${inviteCode}`);
    return response.data;
  }

  async leaveTeam(teamId: string) {
    const response = await this.client.post(`/teams/${teamId}/leave`);
    return response.data;
  }

  async removeTeamMember(teamId: string, userId: string) {
    const response = await this.client.delete(`/teams/${teamId}/members/${userId}`);
    return response.data;
  }

  async shareOpportunityWithTeam(teamId: string, opportunityId: string, note?: string) {
    const response = await this.client.post(`/teams/${teamId}/share`, {
      opportunity_id: opportunityId,
      note,
    });
    return response.data;
  }

  async getTeamSharedOpportunities(teamId: string) {
    const response = await this.client.get(`/teams/${teamId}/shared`);
    return response.data;
  }

  // ==================== Submissions ====================
  async createSubmission(data: {
    title: string;
    description: string;
    website_url: string;
    host_name: string;
    opportunity_type?: string;
    format?: string;
    themes?: string[];
    technologies?: string[];
    application_deadline?: string;
    event_start_date?: string;
    event_end_date?: string;
    total_prize_value?: number;
    currency?: string;
    team_size_min?: number;
    team_size_max?: number;
    eligibility_notes?: string;
  }) {
    const response = await this.client.post("/submissions", data);
    return response.data;
  }

  async getMySubmissions(params?: { skip?: number; limit?: number }) {
    const response = await this.client.get("/submissions", { params });
    return response.data;
  }

  async getSubmission(submissionId: string) {
    const response = await this.client.get(`/submissions/${submissionId}`);
    return response.data;
  }

  async updateSubmission(submissionId: string, data: any) {
    const response = await this.client.patch(`/submissions/${submissionId}`, data);
    return response.data;
  }

  async deleteSubmission(submissionId: string) {
    const response = await this.client.delete(`/submissions/${submissionId}`);
    return response.data;
  }

  async enhanceSubmission(submissionId: string) {
    const response = await this.client.post(`/submissions/${submissionId}/enhance`);
    return response.data;
  }

  // Admin submissions
  async getAdminSubmissions(params?: { status?: string; skip?: number; limit?: number }) {
    const response = await this.client.get("/submissions/admin/all", { params });
    return response.data;
  }

  async getAdminPendingSubmissions(params?: { skip?: number; limit?: number }) {
    const response = await this.client.get("/submissions/admin/pending", { params });
    return response.data;
  }

  async getAdminSubmissionStats() {
    const response = await this.client.get("/submissions/admin/stats");
    return response.data;
  }

  async reviewSubmission(submissionId: string, data: { status: string; note: string }) {
    const response = await this.client.post(`/submissions/admin/${submissionId}/review`, data);
    return response.data;
  }

  // ==================== Calendar ====================
  async getOpportunityIcalUrl(opportunityId: string) {
    return `${API_BASE_URL}/calendar/opportunity/${opportunityId}/ical`;
  }

  async getOpportunityGoogleCalendarUrl(opportunityId: string, eventType: string = "deadline") {
    const response = await this.client.get(`/calendar/opportunity/${opportunityId}/google`, {
      params: { event_type: eventType },
    });
    return response.data;
  }

  async getOpportunityOutlookCalendarUrl(opportunityId: string, eventType: string = "deadline") {
    const response = await this.client.get(`/calendar/opportunity/${opportunityId}/outlook`, {
      params: { event_type: eventType },
    });
    return response.data;
  }

  async getPipelineIcalUrl(pipelineId: string) {
    return `${API_BASE_URL}/calendar/pipeline/${pipelineId}/ical`;
  }

  async getUpcomingIcalUrl(daysAhead: number = 90) {
    return `${API_BASE_URL}/calendar/upcoming/ical?days_ahead=${daysAhead}`;
  }

  async getCalendarSubscriptionUrls() {
    const response = await this.client.get("/calendar/subscribe-url");
    return response.data;
  }

  // ==================== Export ====================
  async exportUserData(format: "json" | "csv" = "json", options?: {
    include_profile?: boolean;
    include_matches?: boolean;
    include_pipelines?: boolean;
    include_materials?: boolean;
  }) {
    const params = { format, ...options };
    const response = await this.client.get("/export/user-data", {
      params,
      responseType: "blob",
    });
    return response.data;
  }

  async exportOpportunities(opportunityIds: string[], format: "json" | "csv" = "json") {
    const response = await this.client.get("/export/opportunities", {
      params: { opportunity_ids: opportunityIds.join(","), format },
      responseType: "blob",
    });
    return response.data;
  }

  async exportPipelineOpportunities(pipelineId: string, format: "json" | "csv" = "json") {
    const response = await this.client.get(`/export/pipeline/${pipelineId}`, {
      params: { format },
      responseType: "blob",
    });
    return response.data;
  }

  async exportMatches(format: "json" | "csv" = "json") {
    const response = await this.client.get("/export/matches", {
      params: { format },
      responseType: "blob",
    });
    return response.data;
  }

  // ==================== Community / Shared Lists ====================
  async getPublicLists(params?: { skip?: number; limit?: number; tags?: string[]; sort_by?: string }) {
    const response = await this.client.get("/community/lists", { params });
    return response.data;
  }

  async getFeaturedLists(limit: number = 10) {
    const response = await this.client.get("/community/lists/featured", { params: { limit } });
    return response.data;
  }

  async getPublicList(slug: string) {
    const response = await this.client.get(`/community/lists/${slug}`);
    return response.data;
  }

  async createSharedList(data: {
    title: string;
    description?: string;
    visibility?: "private" | "unlisted" | "public";
    tags?: string[];
    opportunity_ids?: string[];
  }) {
    const response = await this.client.post("/community/lists", data);
    return response.data;
  }

  async getMyLists(params?: { skip?: number; limit?: number }) {
    const response = await this.client.get("/community/my-lists", { params });
    return response.data;
  }

  async getMyList(listId: string) {
    const response = await this.client.get(`/community/my-lists/${listId}`);
    return response.data;
  }

  async updateSharedList(listId: string, data: {
    title?: string;
    description?: string;
    visibility?: "private" | "unlisted" | "public";
    tags?: string[];
  }) {
    const response = await this.client.patch(`/community/my-lists/${listId}`, data);
    return response.data;
  }

  async deleteSharedList(listId: string) {
    const response = await this.client.delete(`/community/my-lists/${listId}`);
    return response.data;
  }

  async addOpportunityToList(listId: string, opportunityId: string) {
    const response = await this.client.post(`/community/my-lists/${listId}/opportunities/${opportunityId}`);
    return response.data;
  }

  async removeOpportunityFromList(listId: string, opportunityId: string) {
    const response = await this.client.delete(`/community/my-lists/${listId}/opportunities/${opportunityId}`);
    return response.data;
  }

  async toggleListLike(listId: string) {
    const response = await this.client.post(`/community/lists/${listId}/like`);
    return response.data;
  }

  async addListComment(listId: string, content: string) {
    const response = await this.client.post(`/community/lists/${listId}/comments`, { content });
    return response.data;
  }

  async getListShareLinks(listId: string) {
    const response = await this.client.get(`/community/lists/${listId}/share`);
    return response.data;
  }

  async generateListDescription(listId: string) {
    const response = await this.client.post(`/community/lists/${listId}/generate-description`);
    return response.data;
  }

  async getSimilarLists(listId: string, limit: number = 5) {
    const response = await this.client.get(`/community/lists/${listId}/similar`, { params: { limit } });
    return response.data;
  }
}

export const apiClient = new ApiClient();
