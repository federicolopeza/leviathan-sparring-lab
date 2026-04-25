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
  /* V-T1-004: source maps intentionally exposed in production — threat model in README.md */
  productionBrowserSourceMaps: true
};

export default nextConfig;
