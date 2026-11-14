import type { NextConfig } from "next";

// A static export: every route is prerendered to HTML and navigation between routes happens in
// the browser (next/link). Nothing needs a server, so the site never has a cold start.
// (Cache Components and Partial Prefetching need a server and cannot be combined with an export.)
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
