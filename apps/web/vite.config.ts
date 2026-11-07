import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { preferSavedMedia } from "./src/lib/pack-cache";

const apiProxy = process.env.CLIMATE_API_PROXY ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["favicon.svg", "offline-world.geojson"],
      manifest: {
        name: "My Climate Story · আমার জলবায়ুর গল্প",
        short_name: "Climate Story",
        description:
          "Discover climate and landscape around your own backyard with NASA data.",
        theme_color: "#173f35",
        background_color: "#f8f5ed",
        display: "standalone",
        start_url: "/bn/",
        scope: "/",
        lang: "bn",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        clientsClaim: true,
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api/, /^\/media/],
        maximumFileSizeToCacheInBytes: 3_000_000,
        globPatterns: ["**/*.{js,css,html,svg,png,woff2,geojson}"],
        runtimeCaching: [
          {
            urlPattern:
              /\/api\/v1\/(config|places\/featured|stories\/|sources\/)/,
            handler: "NetworkFirst",
            options: {
              cacheName: "climate-api-v1",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 50, maxAgeSeconds: 86400 },
            },
          },
          {
            urlPattern: /\/media\//,
            handler: "CacheFirst",
            options: {
              cacheName: "climate-media-v2",
              expiration: { maxEntries: 80, maxAgeSeconds: 31536000 },
              // Keep this after expiration: saved packs have their own lifetime.
              plugins: [{ cachedResponseWillBeUsed: preferSavedMedia }],
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": apiProxy,
      "/media": apiProxy,
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["chart.js", "react-chartjs-2"],
          maps: ["leaflet", "react-leaflet"],
        },
      },
    },
  },
});
