function getAuthHeaders() {
  const token = sessionStorage.getItem("token");

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export const createCampaign = async (
  payload: any,
  token: string
) => {
  const response = await fetch("/api/campaigns", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to create campaign");
  }

  return data;
};

export const getCampaigns = async (params?: {
  page?: number;
  limit?: number;
  name?: string;
  status?: string;
}) => {
  const query = new URLSearchParams();
  if (params?.page) query.set("page", String(params.page));
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.name) query.set("name", params.name);
  if (params?.status) query.set("status", params.status);

  const response = await fetch(`/api/campaigns?${query.toString()}`, {
    headers: getAuthHeaders(),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch campaigns");
  }

  return data;
};

export const updateCampaign = async (id: string, payload: any) => {
  const response = await fetch(`/api/campaigns/${id}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to update campaign");
  }

  return data;
};

export const deleteCampaign = async (id: string) => {
  const response = await fetch(`/api/campaigns/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to delete campaign");
  }

  return data;
};