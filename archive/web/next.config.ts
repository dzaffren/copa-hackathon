import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root to web/ so Turbopack doesn't walk up into the
  // Python repo root (which has no lockfile) looking for one.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
