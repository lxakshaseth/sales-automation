function getAuthHeaders() {
  const token = sessionStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function getContacts(
  page: number = 1,
  limit: number = 11,
  search?: string,
) {
  const searchParam = search ? `&search=${encodeURIComponent(search)}` : "";
  const response = await fetch(
    `/api/leads?limit=${limit}&page=${page}${searchParam}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to fetch contacts");
  return data;
}

export async function createContact(payload: {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  company: string;
  state: string;
  country: string;
}) {
  const response = await fetch("/api/leads", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to create contact");
  return data;
}

export async function updateContact(
  contactId: string,
  payload: {
    firstName: string;
    lastName: string;
    phone: string;
    email: string;
    company: string;
    state: string;
    country: string;
  },
) {
  const response = await fetch(`/api/leads/${contactId}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to update contact");
  return data;
}

export async function deleteContact(contactId: string) {
  const response = await fetch(`/api/leads/${contactId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to delete contact");
  return data;
}

export async function bulkDeleteContacts(ids: string[]) {
  const response = await fetch("/api/leads/bulk-delete", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ ids }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.message || "Failed to delete contacts");
  return data;
}

export async function getCampaigns(params?: { status?: string }) {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);

  const response = await fetch(`/api/campaigns?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.message || "Failed to fetch campaigns");
  return data;
}

export async function assignLead(leadId: string, campaignId: string) {
  const response = await fetch("/api/automation/assign-lead", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ leadId, campaignId }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to assign lead");
  return data;
}

export async function assignMultipleLeads(
  leadIds: string[],
  campaignId: string,
) {
  const response = await fetch("/api/automation/assign-multiple-leads", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ leadIds, campaignId }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Failed to assign leads");
  return data;
}

export async function bulkUploadContacts(file: File) {
  const token = sessionStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/leads/bulk-upload", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.message || "Failed to upload contacts");
  return data;
}
