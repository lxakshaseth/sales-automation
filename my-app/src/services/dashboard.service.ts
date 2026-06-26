export interface DashboardStats {
  campaigns: number;
  templates: number;
  leads: number;
  whatsappContacts: number;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch("/api/dashboard");

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message || "Failed to fetch dashboard stats");
  }

  return result.data;
}