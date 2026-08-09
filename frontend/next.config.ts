import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Playwright drives the dev server via 127.0.0.1; Next 16 blocks
  // cross-origin dev asset requests by default. Dev-only, no effect on
  // `next build`/`next start`.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
