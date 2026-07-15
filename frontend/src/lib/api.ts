import type { Connection, TaskResponse } from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ApiError {
  code: string;
  message: string;
}

class HttpError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let code = "INTERNAL_ERROR";
    let message = `Request failed with status ${res.status}`;
    try {
      const body = (await res.json()) as Partial<ApiError>;
      if (body.code) code = body.code;
      if (body.message) message = body.message;
    } catch {
      // non-JSON error body — keep defaults
    }
    throw new HttpError(res.status, code, message);
  }
  return (await res.json()) as T;
}

export function fetchTask(
  workstreamId: string,
  nodeId: string,
): Promise<TaskResponse> {
  return getJson<TaskResponse>(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}`,
  );
}

export function fetchEdgeFindings(
  workstreamId: string,
  edgeId: string,
): Promise<Connection[]> {
  return getJson<Connection[]>(
    `${API_BASE}/api/workstreams/${workstreamId}/edges/${edgeId}/findings`,
  );
}

export { HttpError };
