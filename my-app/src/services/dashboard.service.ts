export interface DashboardStats {
  campaigns: number;
  templates: number;
  leads: number;
  whatsappContacts: number;
}

interface DashboardStatsResponse {
  success: boolean;
  data?: DashboardStats;
  message?: string;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch("/api/dashboard");

  const result = (await response
    .json()
    .catch(() => null)) as DashboardStatsResponse | null;

  if (!response.ok || !result?.success || !result.data) {
    throw new Error(result?.message || "Failed to fetch dashboard stats");
  }

  return result.data;
}
