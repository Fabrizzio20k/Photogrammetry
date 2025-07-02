import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/photo/**',
      },
    ],
  },
  output: 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,

};

export default nextConfig;
