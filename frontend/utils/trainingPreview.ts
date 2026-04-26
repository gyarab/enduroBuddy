export type PreviewInterval = {
  label: string;
  reps: number;
  distanceLabel: string;
  estimatedKm: number;
};

export type ParsedTrainingPreview = {
  totalKm: number;
  kmText: string;
  confidence: "high" | "medium" | "low";
  warning: string;
  intervals: PreviewInterval[];
  hasStructuredPreview: boolean;
  detectedTags: string[];
};

function formatKmText(totalKm: number) {
  return `~ ${totalKm.toFixed(1)} km`;
}

function toNum(value: string) {
  const parsed = Number.parseFloat(value.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

function toKm(value: number, unit: string) {
  return unit.toLowerCase() === "km" ? value : value / 1000;
}

function sumDistinctDistances(text: string) {
  let totalKm = 0;
  const directDistance = /(^|[\s,+;])(\d+(?:[.,]\d+)?)\s*(km|m)\b/gi;
  let match = directDistance.exec(text);
  while (match) {
    const value = toNum(match[2]);
    if (value) {
      totalKm += toKm(value, match[3]);
    }
    match = directDistance.exec(text);
  }
  return totalKm;
}

function detectTags(text: string) {
  const tags: string[] = [];
  const normalized = text.toLowerCase();
  if (/\btempo\b/.test(normalized)) tags.push("tempo");
  if (/\bfartlek\b/.test(normalized)) tags.push("fartlek");
  if (/\b(kopec|kopce)\b/.test(normalized)) tags.push("hill");
  if (/\bklus\b/.test(normalized)) tags.push("easy");
  if (/\bvolno|rest\b/.test(normalized)) tags.push("rest");
  if (/\binterval\b/.test(normalized)) tags.push("interval");
  return tags;
}

function detectIntervals(text: string): PreviewInterval[] {
  const normalized = text.trim();
  if (!normalized) {
    return [];
  }

  const previews: PreviewInterval[] = [];

  const directPattern = /(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)\s*(km|m)\b/gi;
  let match = directPattern.exec(normalized);
  while (match) {
    const reps = toNum(match[1]);
    const distance = toNum(match[2]);
    if (reps && distance) {
      previews.push({
        label: `Interval ${previews.length + 1}`,
        reps,
        distanceLabel: `${distance} ${match[3].toLowerCase()}`,
        estimatedKm: reps * toKm(distance, match[3]),
      });
    }
    match = directPattern.exec(normalized);
  }

  const parenPattern = /(\d+(?:[.,]\d+)?)\s*[xX]\s*\(([^)]+)\)/gi;
  match = parenPattern.exec(normalized);
  while (match) {
    const reps = toNum(match[1]);
    const innerDistanceMatch = /(\d+(?:[.,]\d+)?)\s*(km|m)\b/i.exec(match[2]);
    const innerDistance = innerDistanceMatch ? toNum(innerDistanceMatch[1]) : null;
    if (reps && innerDistance && innerDistanceMatch) {
      previews.push({
        label: `Block ${previews.length + 1}`,
        reps,
        distanceLabel: `${innerDistance} ${innerDistanceMatch[2].toLowerCase()}`,
        estimatedKm: reps * toKm(innerDistance, innerDistanceMatch[2]),
      });
    }
    match = parenPattern.exec(normalized);
  }

  const seriesPattern = /(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)\s*(km|m)\b/gi;
  match = seriesPattern.exec(normalized);
  while (match) {
    const reps = Math.max(toNum(match[1]) || 0, toNum(match[2]) || 0);
    const distance = toNum(match[3]);
    if (reps && distance) {
      previews.push({
        label: `Series ${previews.length + 1}`,
        reps,
        distanceLabel: `${distance} ${match[4].toLowerCase()}`,
        estimatedKm: reps * toKm(distance, match[4]),
      });
    }
    match = seriesPattern.exec(normalized);
  }

  const rvPattern = /(\d+(?:[.,]\d+)?)\s*[RrVv]\b/g;
  match = rvPattern.exec(normalized);
  while (match) {
    const distance = toNum(match[1]);
    if (distance) {
      previews.push({
        label: `Run ${previews.length + 1}`,
        reps: 1,
        distanceLabel: `${distance} km`,
        estimatedKm: distance,
      });
    }
    match = rvPattern.exec(normalized);
  }

  return previews;
}

function estimateTotalKm(text: string, intervals: PreviewInterval[]) {
  const normalized = text.trim().toLowerCase();
  if (!normalized) {
    return { totalKm: 0, confidence: "low" as const, warning: "" };
  }

  if (["volno", "rest", "rest day"].includes(normalized)) {
    return { totalKm: 0, confidence: "high" as const, warning: "" };
  }

  if (intervals.length > 0) {
    return {
      totalKm: intervals.reduce((sum, interval) => sum + interval.estimatedKm, 0),
      confidence: "high" as const,
      warning: "",
    };
  }

  const explicitDistances = sumDistinctDistances(normalized);
  const klusMinutes = [...normalized.matchAll(/(\d+(?:[.,]\d+)?)\s*(?:min|m(?:in)?)\s*klus/gi)].reduce((sum, match) => {
    const minutes = toNum(match[1]);
    return sum + (minutes ? minutes * 0.25 : 0);
  }, 0);
  const pauseMinutes = [...normalized.matchAll(/\bp\s*=\s*(\d+(?:[.,]\d+)?)/gi)].reduce((sum, match) => {
    const minutes = toNum(match[1]);
    return sum + (minutes ? minutes * 0.15 : 0);
  }, 0);
  const heuristicKm = explicitDistances + klusMinutes + pauseMinutes;

  if (heuristicKm > 0) {
    return {
      totalKm: heuristicKm,
      confidence: heuristicKm >= 2 ? "medium" as const : "low" as const,
      warning:
        klusMinutes > 0 || pauseMinutes > 0
          ? "Preview obsahuje heuristicky odhad z klusu nebo pauz."
          : heuristicKm >= 2
            ? ""
            : "Preview je zalozeny jen na jednom nalezenem distance tokenu.",
    };
  }

  if (/\b(tempo|interval|fartlek|run|beh|b\u011bh|klus|kopec)\b/i.test(normalized)) {
    return {
      totalKm: 0,
      confidence: "low" as const,
      warning: "Nejasny zapis, dopln konkretni vzdalenost nebo interval pattern pro presnejsi preview.",
    };
  }

  return { totalKm: 0, confidence: "low" as const, warning: "" };
}

export function parseTrainingPreview(text: string): ParsedTrainingPreview {
  const intervals = detectIntervals(text);
  const estimate = estimateTotalKm(text, intervals);
  const detectedTags = detectTags(text);
  const roundedKm = Math.round(estimate.totalKm * 10) / 10;
  return {
    totalKm: roundedKm,
    kmText: formatKmText(roundedKm),
    confidence: estimate.confidence,
    warning: estimate.warning,
    intervals,
    hasStructuredPreview: intervals.length > 0 || roundedKm > 0 || Boolean(estimate.warning) || detectedTags.length > 0,
    detectedTags,
  };
}
