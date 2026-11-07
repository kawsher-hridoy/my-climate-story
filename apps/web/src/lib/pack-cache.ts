export const PACK_MEDIA_CACHE = "climate-pack-media-v1";
export const LEGACY_MEDIA_CACHES = ["climate-media-v2", "climate-media-v1"];

/**
 * Workbox serializes this callback into sw.js. Keep the cache name literal and
 * avoid module references in its body. It runs after the browsing expiration
 * plugin so that an old saved response cannot be discarded by browsing policy.
 */
export async function preferSavedMedia({
  request,
  cachedResponse,
}: {
  request: Request;
  cachedResponse?: Response;
}): Promise<Response | undefined> {
  // A repair download must reach the server even if either cache is corrupt.
  if (request.cache === "reload") return undefined;
  const saved = await caches.match(request, {
    cacheName: "climate-pack-media-v1",
  });
  return saved ?? cachedResponse;
}
