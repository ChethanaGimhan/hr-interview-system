/** @type {import('next').NextConfig} */
const nextConfig = {
  // Works out which files the app actually imports and copies just those into
  // .next/standalone, together with the few node_modules files that are really
  // needed. That folder is all the Docker image has to carry, instead of the
  // 400MB of node_modules sitting in this directory.
  output: "standalone",
};

export default nextConfig;
