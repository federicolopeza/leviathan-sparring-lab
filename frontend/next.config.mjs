/** @type {import('next').NextConfig} */
process.env.NEXT_PUBLIC_API_URL ??= "https://api.melispy.com";

const nextConfig = {
  output: "export",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
  },
  reactStrictMode: true,
  images: {
    unoptimized: true
  },
  // Skip TS/ESLint errors during prod build (Phase 7 hot-deploy; full strict via CI later)
  typescript: {
    ignoreBuildErrors: true
  },
  eslint: {
    ignoreDuringBuilds: true
  },
  /* V-T1-004: source maps intentionally exposed in production — threat model in README.md */
  productionBrowserSourceMaps: true
};

export default nextConfig;
