import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  QueryClient,
  QueryClientProvider,
  onlineManager,
} from "@tanstack/react-query";
import { MemoryRouter, Route, Routes, Link } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Saved from "../pages/Saved";
import StoryPage from "../pages/Story";
import i18n from "../lib/i18n";
import type { Story } from "../lib/types";

const offline = vi.hoisted(() => ({
  savedPacks: vi.fn(),
  loadStoryWithOffline: vi.fn(),
  savedStory: vi.fn(async () => undefined),
  getProgress: vi.fn(async () => undefined),
  setProgress: vi.fn(),
  removePack: vi.fn(),
  savePack: vi.fn(),
  repairPack: vi.fn(),
}));
vi.mock("../lib/offline", () => offline);
vi.mock("../components/ClimateChart", () => ({
  TemperatureChart: () => <p>Temperature record</p>,
  RainfallChart: () => null,
  GlobalChart: () => <p>Global record</p>,
}));
vi.mock("../components/Quiz", () => ({ default: () => <p>Saved quiz</p> }));

const name = { en: "Dhaka", bn: "ঢাকা" };
const source = {
  id: "source",
  name: "NASA source",
  unit: "°C",
  start: "1981",
  end: "2025",
  notes: name,
};
const story = {
  place: {
    id: "dhaka",
    name,
    featured: true,
    coordinates: { latitude: 23.8, longitude: 90.4 },
    division: "Dhaka Division",
    description: name,
  },
  release: {
    id: "mcs-saved-version",
    content_version: "content",
    created_at: "2026-01-01T00:00:00Z",
  },
  temperature: {
    source,
    annual: [],
    monthly: [],
    publication_state: "descriptive_only",
  },
  rainfall: {
    source,
    annual: [],
    monthly: [],
    publication_state: "unavailable",
  },
  global_context: { source, annual: [], baseline: "1951–1980" },
  imagery: { id: "dhaka", status: "pending", caption: name },
  quiz: [],
  actions: [],
} as unknown as Story;
const pack = {
  id: "dhaka",
  story,
  release: story.release.id,
  bytes: 100,
  savedAt: "2026-01-01T00:00:00Z",
  assets: [],
  mediaStatus: "complete",
};
let clients: QueryClient[] = [];

function mount(initial: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: 1, gcTime: 0 } },
  });
  clients.push(client);
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initial]}>
        <Routes>
          <Route
            path="/en/"
            element={<Link to="/en/saved">Open saved list</Link>}
          />
          <Route path="/:locale/saved" element={<Saved />} />
          <Route path="/:locale/story/:placeId" element={<StoryPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
beforeEach(async () => {
  onlineManager.setOnline(true);
  Object.defineProperty(navigator, "onLine", {
    configurable: true,
    value: true,
  });
  vi.clearAllMocks();
  offline.savedPacks.mockResolvedValue([pack]);
  offline.loadStoryWithOffline.mockResolvedValue(story);
  await i18n.changeLanguage("en");
});
afterEach(() => {
  onlineManager.setOnline(true);
  Object.defineProperty(navigator, "onLine", {
    configurable: true,
    value: true,
  });
  clients.forEach((client) => client.clear());
  clients = [];
});
function disconnect() {
  act(() => {
    Object.defineProperty(navigator, "onLine", {
      configurable: true,
      value: false,
    });
    onlineManager.setOnline(false);
    window.dispatchEvent(new Event("offline"));
  });
}

describe("offline SPA navigation", () => {
  it("executes the local saved-pack query after the connection goes away", async () => {
    mount("/en/");
    disconnect();
    fireEvent.click(screen.getByRole("link", { name: "Open saved list" }));
    expect(
      await screen.findByRole("heading", { name: "Dhaka" }),
    ).toBeInTheDocument();
    expect(offline.savedPacks).toHaveBeenCalledOnce();
  });

  it("opens a fresh release-pinned story query after an offline transition", async () => {
    mount("/en/saved");
    const link = await screen.findByRole("link", { name: /Open story/ });
    disconnect();
    fireEvent.click(link);
    expect(
      await screen.findByRole("heading", { name: "Dhaka", level: 1 }),
    ).toBeInTheDocument();
    expect(offline.loadStoryWithOffline).toHaveBeenCalledWith(
      "dhaka",
      "mcs-saved-version",
    );
  });

  it("shows an unavailable result instead of pausing retries forever offline", async () => {
    offline.loadStoryWithOffline.mockRejectedValue(new Error("Not saved"));
    disconnect();
    mount("/en/story/unknown?release=mcs-saved-version");
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    await waitFor(() =>
      expect(offline.loadStoryWithOffline).toHaveBeenCalledOnce(),
    );
  });

  it("labels incomplete migrated packs and offers a repair action", async () => {
    offline.savedPacks.mockResolvedValue([
      {
        ...pack,
        mediaStatus: "incomplete",
        missingAssets: ["/media/missing.webp"],
      },
    ]);
    mount("/en/saved");
    expect(
      await screen.findByText(/Some saved images are missing/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Repair saved images Dhaka" }),
    ).toBeEnabled();
  });
});
