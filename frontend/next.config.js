/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_MCP_SERVER_URL: process.env.REACT_APP_MCP_SERVER_URL || 'http://localhost:8000',
    NEXT_PUBLIC_ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT || 'development',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.REACT_APP_MCP_SERVER_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
}

module.exports = nextConfig 