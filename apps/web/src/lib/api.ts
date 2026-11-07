import type { Exploration, Job, Place, Source, Story } from "./types";

export class ApiFailure extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ message: "Unable to load this request." }));
    throw new ApiFailure(
      body.message ?? body.detail ?? "Unable to load this request.",
      response.status,
    );
  }
  return response.json() as Promise<T>;
}
export const api = {
  featured: () => getJson<Place[]>("/api/v1/places/featured"),
  story: (id: string, release?: string) =>
    getJson<Story>(
      `/api/v1/stories/${encodeURIComponent(id)}${release ? `?release=${encodeURIComponent(release)}` : ""}`,
    ),
  search: (q: string, locale: string, signal?: AbortSignal) =>
    getJson<{ results: Place[] }>(
      `/api/v1/places/search?q=${encodeURIComponent(q)}&locale=${locale}`,
      { signal },
    ),
  explore: (
    location:
      | { place_id: string }
      | { coordinates: { latitude: number; longitude: number } },
  ) =>
    getJson<Exploration>("/api/v1/explorations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(location),
    }),
  job: (id: string) => getJson<Job>(`/api/v1/jobs/${id}`),
  source: (id: string) => getJson<Source>(`/api/v1/sources/${id}`),
};
