import { readJsonResponse } from "@/services/api";

export interface DashboardStats {
  campaigns: number;
  templates: number;
  leads: number;
  whatsappContacts: number;
}

const emptyDashboardStats: DashboardStats = {
  campaigns: 0,
  templates: 0,
  leads: 0,
  whatsappContacts: 0,
};

interface DashboardStatsResponse {
  success: boolean;
  data?: DashboardStats;
  message?: string;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  try {
    const response = await fetch("/api/dashboard");
    const result = await readJsonResponse<DashboardStatsResponse>(response);

    if (!response.ok || !result?.success || !result.data) {
      return emptyDashboardStats;
    }

    return result.data;
  } catch {
    return emptyDashboardStats;
  }
}
