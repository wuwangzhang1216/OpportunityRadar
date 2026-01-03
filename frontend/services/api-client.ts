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
    batch_id: string;
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

  async getMaterials(params?: { batch_id?: string; material_type?: string }) {
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
}

export const apiClient = new ApiClient();
