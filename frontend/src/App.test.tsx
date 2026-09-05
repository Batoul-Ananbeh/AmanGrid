import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const demoDecision = {
  contract_version: "1.0",
  analysis_id: "analysis-restricted-001",
  classification: {
    level: "Restricted",
    confidence: 96,
    explanation: "Masked OT configuration and credential-like content.",
  },
  sensitive_findings: [
    { type: "SCADA_OT", count: 1 },
    { type: "INTERNAL_IP", count: 1 },
    { type: "CREDENTIAL", count: 1 },
  ],
  energy_context: {
    scada_ot_relevant: true,
    summary: "Synthetic PLC maintenance and OT network context.",
  },
  risk: { final_score: 92, level: "Critical" },
  policy: {
    recommendations: [
      {
        action: "QUARANTINE",
        execution_mode: "SIMULATED",
        is_primary: true,
        reason: "Critical restricted OT data requires review.",
      },
      {
        action: "HUMAN_REVIEW",
        execution_mode: "RECOMMENDED",
        is_primary: false,
        reason: "An authorized human decision is required.",
      },
    ],
    human_review_required: true,
  },
};

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the connected application and contract-validated demo result", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = String(input);

        if (url.endsWith("/api/v1/health")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              status: "ok",
              service: "amangrid-api",
              version: "0.1.0",
            }),
          });
        }

        return Promise.resolve({
          ok: true,
          json: async () => demoDecision,
        });
      }),
    );

    render(<App />);

    expect(screen.getAllByText("جاري التحقق")).toHaveLength(2);
    expect(await screen.findAllByText("الخدمات متصلة")).toHaveLength(2);
    expect(await screen.findByText("مقيّد")).toBeInTheDocument();
    expect(screen.getByText("حرج")).toBeInTheDocument();
    expect(screen.getByText("بانتظار المراجعة")).toBeInTheDocument();
    expect(screen.getByText("عزل المستند")).toBeInTheDocument();
  });

  it("keeps the recommendation-only boundary visible", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));

    render(<App />);

    expect(
      screen.getByText(/التطبيق يعرض توصيات ومحاكاة فقط/),
    ).toBeInTheDocument();
  });
});
