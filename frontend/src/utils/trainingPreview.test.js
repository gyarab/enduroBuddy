import { describe, expect, it } from "vitest";
import { parseTrainingPreview } from "@/utils/trainingPreview";
describe("parseTrainingPreview", () => {
    it("parses simple interval notation", () => {
        const preview = parseTrainingPreview("6x400m");
        expect(preview.totalKm).toBe(2.4);
        expect(preview.confidence).toBe("high");
        expect(preview.intervals).toHaveLength(1);
        expect(preview.intervals[0]).toMatchObject({
            reps: 6,
            distanceLabel: "400 m",
            estimatedKm: 2.4,
        });
    });
    it("parses parenthesized block notation", () => {
        const preview = parseTrainingPreview("3x(1 km)");
        expect(preview.totalKm).toBe(3);
        expect(preview.intervals).toHaveLength(1);
        expect(preview.intervals[0]).toMatchObject({
            reps: 3,
            distanceLabel: "1 km",
            estimatedKm: 3,
        });
    });
    it("parses R/V shorthand as kilometer repeats", () => {
        const preview = parseTrainingPreview("2R/2V");
        expect(preview.totalKm).toBe(4);
        expect(preview.confidence).toBe("high");
        expect(preview.intervals).toHaveLength(2);
    });
    it("adds heuristic warning for klus minutes", () => {
        const preview = parseTrainingPreview("20 min klus");
        expect(preview.totalKm).toBe(5);
        expect(preview.confidence).toBe("medium");
        expect(preview.warning).toContain("heuristicky");
    });
    it("treats rest day as zero distance with high confidence", () => {
        const preview = parseTrainingPreview("volno");
        expect(preview.totalKm).toBe(0);
        expect(preview.confidence).toBe("high");
        expect(preview.warning).toBe("");
    });
    it("returns warning for run hints without distance", () => {
        const preview = parseTrainingPreview("tempo run");
        expect(preview.totalKm).toBe(0);
        expect(preview.confidence).toBe("low");
        expect(preview.warning).not.toBe("");
        expect(preview.detectedTags).toContain("tempo");
    });
});
