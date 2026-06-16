export interface Template {
  _id: string;
  name: string;
  type: "email" | "sms" | "ai_call";
  subject: string;
  body: string;
  createdAt: string;
  updatedAt: string;
}

const BASE_URL = "/api/templates";

function getAuthHeaders() {
  const token = sessionStorage.getItem("token");

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function getTemplates() {
  const response = await fetch(BASE_URL, {
    headers: getAuthHeaders(),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch templates");
  }

  return data;
}

export async function getTemplateById(id: string) {
  const response = await fetch(`${BASE_URL}/${id}`, {
    headers: getAuthHeaders(),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch template");
  }

  return data;
}

export async function createTemplate(template: {
  name: string;
  type: string;
  subject: string;
  body: string;
}) {
  const response = await fetch(BASE_URL, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(template),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to create template");
  }

  return data;
}

export async function updateTemplate(id: string, template: Partial<Template>) {
  const response = await fetch(`${BASE_URL}/${id}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(template),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to update template");
  }

  return data;
}

export async function deleteTemplate(id: string) {
  const response = await fetch(`${BASE_URL}/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to delete template");
  }

  return data;
}
