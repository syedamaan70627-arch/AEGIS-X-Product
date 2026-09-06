import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: "/analysis", destination: "/reliability", permanent: true },
      { source: "/stress-lab", destination: "/stress", permanent: true },
      { source: "/fault-lab", destination: "/faults", permanent: true },
      { source: "/failure-explorer", destination: "/failures", permanent: true },
      { source: "/early-warning", destination: "/warnings", permanent: true },
      { source: "/data-setup", destination: "/data", permanent: true },
    ];
  },
};

export default nextConfig;
