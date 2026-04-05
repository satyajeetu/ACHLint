import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://satyajeetu.github.io/ACHLint/",
      lastModified: new Date("2026-04-05"),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
