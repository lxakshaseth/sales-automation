export interface FunnelItem {
  status: string;
  count: number;
}

export interface FunnelResponse {
  data: FunnelItem[];
  date_range: {
    from: string;
    to: string;
  };
}

export async function fetchLeadFunnel(
  days: "7" | "30",
): Promise<FunnelResponse> {
  const res = await fetch(`/api/leads/funnel/by-status?days=${days}`);

  if (res.status === 503) {
    return {
      data: [
        { status: "new", count: 0 },
        { status: "contacted", count: 0 },
      ],
      date_range: {
        from: new Date().toISOString().split("T")[0],
        to: new Date().toISOString().split("T")[0],
      },
    };
  }

  if (!res.ok) {
    throw new Error("Failed to fetch lead funnel data");
  }

  return res.json();
}
export function formatDateRangeLabel(from: string, to: string): string {
  const pad = (n: number) => String(n).padStart(2, "0");

  const fromDate = new Date(from);
  const toDate = new Date(to);

  const fromStr = `${pad(fromDate.getDate())}/${pad(fromDate.getMonth() + 1)}/${fromDate.getFullYear()}`;
  const toStr = `${pad(toDate.getDate())}/${pad(toDate.getMonth() + 1)}/${toDate.getFullYear()}`;

  return `${fromStr} - ${toStr}`;
}
