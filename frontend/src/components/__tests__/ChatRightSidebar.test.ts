import { describe, expect, it } from "vitest";

import { analyticsModelLabel } from "@/components/ChatRightSidebar";

describe("analyticsModelLabel", () => {
  it("labels a zero-cost UUID analytics bucket as cache activity", () => {
    expect(analyticsModelLabel("2cc8b48d-696e-483a-a41e-f6396abd7ffc", 0)).toBe("Cache");
  });

  it("preserves actual model names and paid UUID buckets", () => {
    expect(analyticsModelLabel("gpt-5.6-terra", 0)).toBe("gpt-5.6-terra");
    expect(analyticsModelLabel("2cc8b48d-696e-483a-a41e-f6396abd7ffc", 0.01)).toBe("2cc8b48d-696e-483a-a41e-f6396abd7ffc");
  });
});
