/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export so FastAPI can serve the built frontend
  // The 'out' directory will contain static HTML/JS/CSS files
  output: 'export',
  typescript: {
    ignoreBuildErrors: true,
  }
}

export default nextConfig
