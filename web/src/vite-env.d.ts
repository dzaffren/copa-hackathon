/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Rulebook Radar engine read API (uvicorn engine.api:app). */
  readonly VITE_ENGINE_BASE_URL: string;
}
