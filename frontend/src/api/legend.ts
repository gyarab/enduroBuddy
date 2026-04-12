import { apiClient } from "@/api/client";

export type LegendZone = {
  from: string;
  to: string;
};

export type LegendPR = {
  distance: string;
  time: string;
};

export type LegendState = {
  zones: {
    z1: LegendZone;
    z2: LegendZone;
    z3: LegendZone;
    z4: LegendZone;
    z5: LegendZone;
  };
  aerobic_threshold: string;
  anaerobic_threshold: string;
  prs: LegendPR[];
};

export const PR_DISTANCES = [
  "800m",
  "1000m",
  "1 mile",
  "1500m",
  "2 miles",
  "3000m",
  "3k",
  "5000m",
  "5k",
  "10000m",
  "10k",
  "Půlmaraton",
  "Maraton",
] as const;

export async function fetchLegend() {
  const response = await apiClient.get<{ ok: boolean; state: LegendState }>("/legend/");
  return response.data;
}

export async function saveLegend(state: LegendState) {
  const response = await apiClient.post<{ ok: boolean; state: LegendState }>("/legend/", { state });
  return response.data;
}
