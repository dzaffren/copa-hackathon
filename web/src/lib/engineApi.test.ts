// Tests for the typed engine client (spec-drafter-workspace.md, Tests 3–6 +
// the config-error guard). No network: `globalThis.fetch` is mocked and
// `import.meta.env.VITE_ENGINE_BASE_URL` is set with `vi.stubEnv`.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Clause } from "../types";
import {
  EngineConfigError,
  EngineNotFound,
  EngineRequestError,
  findConnections,
  getClause,
  getGraph,
  getNode,
} from "./engineApi";

const BASE_URL = "http://engine.test";

const fetchMock = vi.fn();

/**
 * A minimal `Response` stand-in — the client only touches `ok`, `status`,
 * `statusText`, and `json()`, so we avoid depending on a global `Response`
 * constructor across environments.
 */
function mockResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: `status ${status}`,
    json: async () => body,
  } as unknown as Response;
}

/** The URL passed to the mocked `fetch` on its Nth (default first) call. */
function requestedUrl(call = 0): string {
  return fetchMock.mock.calls[call][0] as string;
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
  vi.stubEnv("VITE_ENGINE_BASE_URL", BASE_URL);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("getClause", () => {
  const OUTSOURCING_12_1_TEXT =
    "A financial institution must obtain the Bank's written approval before " +
    "entering into a new material outsourcing arrangement.";

  it("Test 3: encodes the space in 'Outsourcing 12.1' and returns the verbatim clause", async () => {
    const clause: Clause = {
      clause_number: "Outsourcing 12.1",
      text: OUTSOURCING_12_1_TEXT,
      policy_id: "outsourcing",
      document_id: "outsourcing-v1-2019",
      source: "published",
      heading: "Application for approval",
      parent: "Outsourcing 12",
      children: [],
      superseded_versions: [],
    };
    fetchMock.mockResolvedValueOnce(mockResponse(clause));

    const result = await getClause("Outsourcing 12.1");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(requestedUrl()).toBe(`${BASE_URL}/clauses/Outsourcing%2012.1`);
    expect(result.clause_number).toBe("Outsourcing 12.1");
    expect(result.text).toBe(OUTSOURCING_12_1_TEXT);
  });

  it("Test 4: encodes 'Operational Resilience 1.1' and returns its clause", async () => {
    const clause: Clause = {
      clause_number: "Operational Resilience 1.1",
      text: "A financial institution must ensure the continuity of its critical financial services.",
      policy_id: "opres",
      document_id: "opres-v1-2025-draft",
      source: "published",
    };
    fetchMock.mockResolvedValueOnce(mockResponse(clause));

    const result = await getClause("Operational Resilience 1.1");

    expect(requestedUrl()).toBe(
      `${BASE_URL}/clauses/Operational%20Resilience%201.1`,
    );
    expect(result.clause_number).toBe("Operational Resilience 1.1");
  });

  it("passes an optional version as a query param", async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({
        clause_number: "RMiT 17.1",
        text: "…",
        policy_id: "rmit",
        document_id: "rmit-v1-2020",
        source: "published",
      }),
    );

    await getClause("RMiT 17.1", "rmit-v1-2020");

    expect(requestedUrl()).toBe(
      `${BASE_URL}/clauses/RMiT%2017.1?version=rmit-v1-2020`,
    );
  });

  it("Test 5: 404 CLAUSE_NOT_FOUND throws EngineNotFound carrying the error code", async () => {
    fetchMock.mockResolvedValue(
      mockResponse(
        {
          error: "CLAUSE_NOT_FOUND",
          message: "No matching clause found for 'RMiT 99.9'",
        },
        404,
      ),
    );

    const error = await getClause("RMiT 99.9")
      .then(() => null)
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(EngineNotFound);
    expect((error as EngineNotFound).code).toBe("CLAUSE_NOT_FOUND");
    expect((error as EngineNotFound).message).toContain(
      "No matching clause found",
    );
  });
});

describe("getNode", () => {
  it("Test 6: 404 NODE_NOT_FOUND throws EngineNotFound and URL-encodes the id", async () => {
    fetchMock.mockResolvedValue(
      mockResponse(
        {
          error: "NODE_NOT_FOUND",
          message: "No node with id 'does-not-exist'",
        },
        404,
      ),
    );

    const error = await getNode("does-not-exist")
      .then(() => null)
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(EngineNotFound);
    expect((error as EngineNotFound).code).toBe("NODE_NOT_FOUND");
    expect(requestedUrl()).toBe(`${BASE_URL}/nodes/does-not-exist`);
  });

  it("returns node detail on success", async () => {
    const detail = {
      id: "rmit-v2-2026-draft",
      title: "Risk Management in Technology (RMiT)",
      status: "In progress",
      edges: [
        {
          target: "outsourcing-v1-2019",
          type: "overlaps",
          reason: "…",
        },
      ],
    };
    fetchMock.mockResolvedValueOnce(mockResponse(detail));

    const result = await getNode("rmit-v2-2026-draft");

    expect(result.id).toBe("rmit-v2-2026-draft");
    expect(result.edges[0].target).toBe("outsourcing-v1-2019");
  });
});

describe("getGraph", () => {
  it("fetches the graph and returns nodes + edges", async () => {
    const graph = { nodes: [{ id: "rmit-v2-2026-draft" }], edges: [] };
    fetchMock.mockResolvedValueOnce(mockResponse(graph));

    const result = await getGraph();

    expect(requestedUrl()).toBe(`${BASE_URL}/graph`);
    expect(result.nodes[0].id).toBe("rmit-v2-2026-draft");
  });

  it("throws EngineConfigError (and never fetches) when VITE_ENGINE_BASE_URL is missing", async () => {
    vi.stubEnv("VITE_ENGINE_BASE_URL", "");

    const error = await getGraph()
      .then(() => null)
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(EngineConfigError);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("error mapping", () => {
  it("maps a non-404 error body to a generic EngineRequestError", async () => {
    fetchMock.mockResolvedValue(
      mockResponse({ error: "INTERNAL", message: "boom" }, 500),
    );

    const error = await getGraph()
      .then(() => null)
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(EngineRequestError);
    expect((error as EngineRequestError).status).toBe(500);
  });
});

describe("findConnections", () => {
  it("POSTs the two document ids and returns the result", async () => {
    const body = { connections: [], unsupported: [] };
    fetchMock.mockResolvedValueOnce(mockResponse(body));

    const result = await findConnections(
      "rmit-v2-2026-draft",
      "outsourcing-v1-2019",
    );

    expect(requestedUrl()).toBe(`${BASE_URL}/connections/find`);
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      document_ids: ["rmit-v2-2026-draft", "outsourcing-v1-2019"],
    });
    expect(result.connections).toEqual([]);
  });
});
