/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  reactStrictMode: true,
  images: {
    unoptimized: true
  },
  /* V-T1-004: source maps intentionally exposed in production — threat model in README.md */
  productionBrowserSourceMaps: true
};

export default nextConfig;
