import Dexie, { type EntityTable } from "dexie";
import type { Story } from "./types";
import { LEGACY_MEDIA_CACHES, PACK_MEDIA_CACHE } from "./pack-cache";

export type SavedPack = {
  id: string;
  story: Story;
  release: string;
  bytes: number;
  savedAt: string;
  assets: string[];
  mediaStatus?: "complete" | "incomplete";
  missingAssets?: string[];
  mediaStorageVersion?: 1;
};
export type Progress = {
  id: string;
  answers: number[];
  questionIndex: number;
  finished: boolean;
  actions: string[];
};
const db = new Dexie("my-climate-story-v1") as Dexie & {
  packs: EntityTable<SavedPack, "id">;
  progress: EntityTable<Progress, "id">;
};
db.version(1).stores({ packs: "id,release,savedAt", progress: "id" });

// Serialize cache/reference changes, including across tabs where Web Locks is
// available. No Cache Storage write can be part of an IndexedDB transaction.
let packOperation: Promise<unknown> = Promise.resolve();
function withPackLock<T>(operation: () => Promise<T>): Promise<T> {
  const run = async (): Promise<T> => {
    if (navigator.locks?.request)
      return await navigator.locks.request("climate-saved-packs", operation);
    return operation();
  };
  const result = packOperation.then(run, run);
  packOperation = result.then(
    () => undefined,
    () => undefined,
  );
  return result;
}

const absoluteUrl = (url: string) => new URL(url, location.href).href;
const hex = (buffer: ArrayBuffer) =>
  [...new Uint8Array(buffer)]
    .map((x) => x.toString(16).padStart(2, "0"))
    .join("");

function requestedAssets(story: Story): Map<string, string | undefined> {
  const requests = new Map<string, string | undefined>();
  for (const asset of [story.imagery.before, story.imagery.after]) {
    if (!asset) continue;
    requests.set(absoluteUrl(asset.url), asset.sha256);
    const thumbnail = absoluteUrl(asset.thumbnail_url);
    if (!requests.has(thumbnail)) requests.set(thumbnail, undefined);
  }
  return requests;
}

async function validAsset(
  response: Response,
  checksum?: string,
): Promise<boolean> {
  if (
    !response.ok ||
    !response.headers.get("Content-Type")?.startsWith("image/")
  )
    return false;
  if (!checksum) return true;
  const body = await response.clone().arrayBuffer();
  return hex(await crypto.subtle.digest("SHA-256", body)) === checksum;
}

async function cachedAsset(
  url: string,
  checksum?: string,
): Promise<Response | undefined> {
  for (const cacheName of [PACK_MEDIA_CACHE, ...LEGACY_MEDIA_CACHES]) {
    const response = await caches.match(url, { cacheName });
    if (response && (await validAsset(response, checksum))) return response;
  }
  return undefined;
}

async function deleteUnreferenced(urls: string[]): Promise<void> {
  const remaining = await db.packs.toArray();
  const referenced = new Set(
    remaining.flatMap((pack) => pack.assets.map(absoluteUrl)),
  );
  const cache = await caches.open(PACK_MEDIA_CACHE);
  for (const url of urls) {
    if (!referenced.has(absoluteUrl(url))) await cache.delete(absoluteUrl(url));
  }
}

async function inspectAndMigrate(pack: SavedPack): Promise<SavedPack> {
  const expected = requestedAssets(pack.story);
  const missingAssets: string[] = [];
  let cache: Cache | undefined;
  try {
    cache = await caches.open(PACK_MEDIA_CACHE);
  } catch {
    /* Report an incomplete pack below. */
  }
  for (const [url, checksum] of expected) {
    try {
      const response = cache && (await cachedAsset(url, checksum));
      if (!response || !cache) missingAssets.push(url);
      else await cache.put(url, response);
    } catch {
      missingAssets.push(url);
    }
  }
  const updated: SavedPack = {
    ...pack,
    assets: [...expected.keys()],
    mediaStatus: missingAssets.length ? "incomplete" : "complete",
    missingAssets,
    mediaStorageVersion: 1,
  };
  await db.packs.put(updated);
  return updated;
}

/** Preserve legacy pack media before ordinary browsing can evict it. */
export function migrateSavedPacks(): Promise<SavedPack[]> {
  return withPackLock(async () => {
    const packs = await db.packs.orderBy("savedAt").reverse().toArray();
    const result: SavedPack[] = [];
    for (const pack of packs) result.push(await inspectAndMigrate(pack));
    return result;
  });
}
export const savedPacks = migrateSavedPacks;
export const savedStory = (id: string) =>
  withPackLock(async () => {
    const pack = await db.packs.get(id);
    return pack ? inspectAndMigrate(pack) : undefined;
  });
export const getProgress = (id: string) => db.progress.get(id);
export async function setProgress(id: string, change: Partial<Progress>) {
  const previous = await db.progress.get(id);
  await db.progress.put({
    id,
    answers: [],
    questionIndex: 0,
    finished: false,
    actions: [],
    ...previous,
    ...change,
  });
}

async function waitForOfflineShell(signal?: AbortSignal): Promise<void> {
  if (!("serviceWorker" in navigator)) throw new Error("offline_unavailable");
  signal?.throwIfAborted();
  await new Promise<void>((resolve, reject) => {
    const abort = () => finish(signal?.reason ?? new Error("aborted"));
    const timeout = setTimeout(
      () => finish(new Error("offline_not_ready")),
      30000,
    );
    function finish(error?: unknown) {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", abort);
      if (error) reject(error);
      else resolve();
    }
    signal?.addEventListener("abort", abort, { once: true });
    navigator.serviceWorker.ready.then(() => finish(), finish);
  });
}

export async function savePack(
  story: Story,
  signal?: AbortSignal,
): Promise<SavedPack> {
  await waitForOfflineShell(signal);
  return withPackLock(async () => {
    signal?.throwIfAborted();
    const previous = await db.packs.get(story.place.id);
    const packs = await db.packs.toArray();
    if (!previous && packs.length >= 20) throw new Error("pack_limit");
    const requests = requestedAssets(story);
    const ready: Array<{ url: string; response: Response }> = [];
    let bytes = new TextEncoder().encode(JSON.stringify(story)).byteLength;
    for (const [url, checksum] of requests) {
      signal?.throwIfAborted();
      // Reuse only a response that passes the current manifest's checksum.
      // reload bypasses both service-worker caches when an asset needs repair.
      const response =
        (await cachedAsset(url, checksum)) ??
        (await fetch(url, { signal, cache: "reload" }));
      if (!(await validAsset(response, checksum)))
        throw new Error("asset_unavailable_or_changed");
      bytes += (await response.clone().arrayBuffer()).byteLength;
      ready.push({ url, response });
    }
    const currentBytes = packs.reduce(
      (sum, pack) => sum + (pack.id === story.place.id ? 0 : pack.bytes),
      0,
    );
    if (currentBytes + bytes > 100 * 1024 * 1024)
      throw new Error("storage_limit");
    const estimate = await navigator.storage?.estimate();
    if (
      estimate?.quota != null &&
      estimate.usage != null &&
      estimate.quota - estimate.usage < bytes * 1.2
    ) {
      throw new Error("storage_limit");
    }
    const cache = await caches.open(PACK_MEDIA_CACHE);
    const allAssets = ready.map((x) => x.url);
    const pack: SavedPack = {
      id: story.place.id,
      story,
      release: story.release.id,
      bytes,
      savedAt: new Date().toISOString(),
      assets: allAssets,
      mediaStatus: "complete",
      missingAssets: [],
      mediaStorageVersion: 1,
    };
    try {
      for (const item of ready) {
        signal?.throwIfAborted();
        await cache.put(item.url, item.response);
      }
      signal?.throwIfAborted();
      // Commit the complete manifest only after every persistent cache write.
      await db.packs.put(pack);
    } catch (error) {
      await deleteUnreferenced(allAssets).catch(() => undefined);
      throw error;
    }
    if (previous)
      await deleteUnreferenced(
        previous.assets.filter((url) => !allAssets.includes(absoluteUrl(url))),
      );
    return pack;
  });
}

export async function removePack(id: string) {
  return withPackLock(async () => {
    const pack = await db.packs.get(id);
    await db.packs.delete(id);
    await deleteUnreferenced(pack?.assets ?? []);
  });
}

/** Repair the saved release, rather than silently replacing it with a newer one. */
export async function repairPack(id: string): Promise<SavedPack> {
  const pack = await db.packs.get(id);
  if (!pack) throw new Error("pack_not_found");
  return savePack(pack.story);
}

export async function loadStoryWithOffline(id: string, release?: string) {
  // In a known-offline state do not wait for a network timeout before local I/O.
  if (!navigator.onLine) {
    const saved = await savedStory(id).catch(() => undefined);
    if (saved && (!release || release === saved.release)) return saved.story;
  }
  const { api } = await import("./api");
  try {
    return await api.story(id, release);
  } catch (error) {
    const saved = await savedStory(id).catch(() => undefined);
    if (saved && (!release || release === saved.release)) return saved.story;
    throw error;
  }
}
