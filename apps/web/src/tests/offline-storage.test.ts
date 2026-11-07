// @vitest-environment node
import "fake-indexeddb/auto";
import Dexie from "dexie";
import { beforeEach, afterAll, describe, expect, it, vi } from "vitest";
import {
  migrateSavedPacks,
  removePack,
  repairPack,
  savePack,
  savedPacks,
  type SavedPack,
} from "../lib/offline";
import { PACK_MEDIA_CACHE, preferSavedMedia } from "../lib/pack-cache";
import type { Story } from "../lib/types";

const origin = "http://localhost:5274";
const webcrypto = globalThis.crypto;
const normalize = (input: RequestInfo | URL) =>
  new URL(input instanceof Request ? input.url : String(input), origin).href;

class MemoryCache {
  entries = new Map<string, Response>();
  failPut: string | null = null;
  async match(input: RequestInfo | URL) {
    return this.entries.get(normalize(input))?.clone();
  }
  async put(input: RequestInfo | URL, response: Response) {
    const key = normalize(input);
    if (this.failPut && key.includes(this.failPut))
      throw new Error("simulated cache write failure");
    this.entries.set(key, response.clone());
  }
  async delete(input: RequestInfo | URL) {
    return this.entries.delete(normalize(input));
  }
  async keys() {
    return [...this.entries.keys()].map((key) => new Request(key));
  }
}
class MemoryCacheStorage {
  stores = new Map<string, MemoryCache>();
  async open(name: string) {
    let cache = this.stores.get(name);
    if (!cache) {
      cache = new MemoryCache();
      this.stores.set(name, cache);
    }
    return cache;
  }
  async match(input: RequestInfo | URL, options?: { cacheName?: string }) {
    const stores = options?.cacheName
      ? [this.stores.get(options.cacheName)]
      : [...this.stores.values()];
    for (const cache of stores) {
      const response = await cache?.match(input);
      if (response) return response;
    }
    return undefined;
  }
  async delete(name: string) {
    return this.stores.delete(name);
  }
}
const database = new Dexie("my-climate-story-v1");
database.version(1).stores({ packs: "id,release,savedAt", progress: "id" });
let storage: MemoryCacheStorage;
const bytes = new TextEncoder().encode("controlled scientific image fixture");
const response = (body = bytes) =>
  new Response(body, {
    headers: {
      "Content-Type": "image/webp",
      Date: "Thu, 01 Jan 1970 00:00:00 GMT",
    },
  });

async function story(id = "dhaka"): Promise<Story> {
  const hash = [
    ...new Uint8Array(await webcrypto.subtle.digest("SHA-256", bytes)),
  ]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
  const asset = {
    url: "/media/before.webp",
    thumbnail_url: "/media/before-thumb.webp",
    sha256: hash,
  };
  return {
    place: { id },
    release: { id: "mcs-pinned-original" },
    imagery: {
      status: "approved",
      before: asset,
      after: {
        ...asset,
        url: "/media/after.webp",
        thumbnail_url: "/media/after-thumb.webp",
      },
    },
  } as unknown as Story;
}
async function legacyPack(value: Story) {
  const assets = [
    value.imagery.before!.url,
    value.imagery.before!.thumbnail_url,
    value.imagery.after!.url,
    value.imagery.after!.thumbnail_url,
  ];
  const pack: SavedPack = {
    id: value.place.id,
    story: value,
    release: value.release.id,
    bytes: 232000,
    savedAt: "2026-01-01T00:00:00Z",
    assets,
  };
  await database.table("packs").put(pack);
  const cache = await storage.open("climate-media-v2");
  for (const url of assets) await cache.put(url, response());
  return pack;
}

beforeEach(async () => {
  storage = new MemoryCacheStorage();
  vi.stubGlobal("caches", storage);
  vi.stubGlobal("location", { href: origin + "/en/" });
  vi.stubGlobal("crypto", webcrypto);
  vi.stubGlobal("navigator", {
    onLine: true,
    serviceWorker: { ready: Promise.resolve({}) },
    storage: { estimate: async () => ({ quota: 200_000_000, usage: 0 }) },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => response()),
  );
  await database.table("packs").clear();
  await database.table("progress").clear();
});
afterAll(() => {
  database.close();
  vi.unstubAllGlobals();
});

describe("persistent saved media", () => {
  it("migrates legacy media and survives loss of the expiring browsing cache", async () => {
    const value = await story();
    await legacyPack(value);
    const [pack] = await migrateSavedPacks();
    expect(pack.mediaStatus).toBe("complete");
    expect(pack.mediaStorageVersion).toBe(1);
    expect(pack.savedAt).toBe("2026-01-01T00:00:00Z");
    await storage.delete("climate-media-v2");
    const hit = await preferSavedMedia({
      request: new Request(origin + value.imagery.before!.url),
    });
    expect(await hit?.text()).toBe(new TextDecoder().decode(bytes));
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
    expect((await savedPacks())[0].mediaStatus).toBe("complete");
  });

  it("does not mark a partial migration complete", async () => {
    const value = await story();
    await legacyPack(value);
    await (
      await storage.open("climate-media-v2")
    ).delete(value.imagery.after!.url);
    const [pack] = await migrateSavedPacks();
    expect(pack.mediaStatus).toBe("incomplete");
    expect(pack.missingAssets).toEqual([origin + value.imagery.after!.url]);
    expect((await database.table("packs").get(pack.id)).mediaStatus).toBe(
      "incomplete",
    );
  });

  it("does not promote a legacy main image whose checksum differs", async () => {
    const value = await story();
    await legacyPack(value);
    await (
      await storage.open("climate-media-v2")
    ).put(
      value.imagery.before!.url,
      response(new TextEncoder().encode("wrong image")),
    );
    const [pack] = await migrateSavedPacks();
    expect(pack.mediaStatus).toBe("incomplete");
    expect(pack.missingAssets).toContain(origin + value.imagery.before!.url);
    expect(
      await storage.match(value.imagery.before!.url, {
        cacheName: PACK_MEDIA_CACHE,
      }),
    ).toBeUndefined();
  });

  it("writes new saves only to the persistent pack cache", async () => {
    const value = await story();
    const pack = await savePack(value);
    expect(pack.mediaStatus).toBe("complete");
    expect((await storage.open(PACK_MEDIA_CACHE)).entries.size).toBe(4);
    expect(storage.stores.get("climate-media-v2")).toBeUndefined();
  });

  it("deletes shared media only after the final referring pack is removed", async () => {
    await savePack(await story("one"));
    await savePack(await story("two"));
    await removePack("one");
    expect((await storage.open(PACK_MEDIA_CACHE)).entries.size).toBe(4);
    await removePack("two");
    expect((await storage.open(PACK_MEDIA_CACHE)).entries.size).toBe(0);
  });

  it("rolls back partial cache writes while preserving an existing shared pack", async () => {
    await savePack(await story("one"));
    const next = await story("two");
    next.imagery.after = {
      ...next.imagery.after!,
      url: "/media/new-after.webp",
      thumbnail_url: "/media/new-thumb.webp",
    };
    const cache = await storage.open(PACK_MEDIA_CACHE);
    cache.failPut = "new-thumb";
    await expect(savePack(next)).rejects.toThrow(
      "simulated cache write failure",
    );
    expect(await database.table("packs").get("two")).toBeUndefined();
    expect(cache.entries.size).toBe(4);
    expect(await cache.match("/media/before.webp")).toBeDefined();
    expect(await cache.match("/media/new-after.webp")).toBeUndefined();
  });

  it("repairs the original saved release rather than replacing its data", async () => {
    const value = await story();
    await legacyPack(value);
    await (
      await storage.open("climate-media-v2")
    ).delete(value.imagery.after!.url);
    await migrateSavedPacks();
    const repaired = await repairPack(value.place.id);
    expect(repaired.release).toBe("mcs-pinned-original");
    expect(repaired.mediaStatus).toBe("complete");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      origin + value.imagery.after!.url,
      expect.objectContaining({ cache: "reload" }),
    );
  });

  it("lets explicit repair downloads bypass both saved and browsing responses", async () => {
    await savePack(await story());
    const hit = await preferSavedMedia({
      request: new Request(origin + "/media/before.webp", { cache: "reload" }),
      cachedResponse: response(),
    });
    expect(hit).toBeUndefined();
  });
});
