import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ImageComparison from "../components/ImageComparison";
import Quiz from "../components/Quiz";
import { number } from "../lib/format";
import i18n from "../lib/i18n";
import type { ImageryPair, Story } from "../lib/types";

vi.mock("../lib/offline", () => ({
  getProgress: vi.fn(async () => undefined),
  setProgress: vi.fn(async () => undefined),
}));
const text = { bn: "পরীক্ষা", en: "Test" };
const asset = {
  url: "/media/test.webp",
  thumbnail_url: "/media/test-thumb.webp",
  date: "1990-01-07",
  sensor: "Landsat 5",
  product_id: "test-scene",
  source_url: "https://example.com/source",
  sha256: "test",
  width: 667,
  height: 667,
  bytes: 100,
  valid_pixel_fraction: 0.99,
  scene_cloud_percent: 0,
  alt: text,
};
const pair: ImageryPair = {
  id: "test",
  status: "approved",
  before: asset,
  after: {
    ...asset,
    date: "2025-02-08",
    product_id: "test-scene-recent",
    sensor: "Landsat 8",
  },
  bounds: [],
  crs: "EPSG:32646",
  resolution_m: 30,
  caption: text,
  attribution: "NASA / USGS",
  processing_version: "v1",
  review: { reviewer: "test" },
};
function mount(element: React.ReactNode) {
  return render(
    <MemoryRouter initialEntries={["/en/"]}>
      <Routes>
        <Route path="/:locale" element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("student interactions", () => {
  it("formats Bengali numbers without changing their values", () => {
    expect(number(2025, "bn")).toBe("২০২৫");
    expect(number(25.2, "en", 1)).toBe("25.2");
  });
  it("keeps both language dictionaries complete", () => {
    expect(
      Object.keys(i18n.getResourceBundle("bn", "translation")).sort(),
    ).toEqual(Object.keys(i18n.getResourceBundle("en", "translation")).sort());
  });
  it("operates image slider and offers a side-by-side equivalent", async () => {
    await i18n.changeLanguage("en");
    mount(<ImageComparison pair={pair} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "70" } });
    expect(slider).toHaveValue("70");
    expect(slider).toHaveAttribute("aria-valuetext", "70% Historical");
    fireEvent.click(screen.getByRole("button", { name: "Side by side" }));
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    expect(
      screen.getByText(/7 Jan 1990/, { selector: "figcaption" }),
    ).toBeInTheDocument();
  });
  it("does not display an unapproved image pair", async () => {
    await i18n.changeLanguage("en");
    mount(<ImageComparison pair={{ ...pair, status: "needs_review" }} />);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    expect(
      screen.getByText("The image story is being prepared."),
    ).toBeInTheDocument();
  });
  it("checks the actual answer index and teaches before advancing", async () => {
    await i18n.changeLanguage("en");
    const question = {
      id: "q1",
      category: "concept",
      question: {
        en: "Which answer has evidence?",
        bn: "কোন উত্তরে প্রমাণ আছে?",
      },
      options: [
        { en: "An unsupported claim", bn: "অসমর্থিত দাবি" },
        { en: "A measured observation", bn: "মাপা পর্যবেক্ষণ" },
      ],
      correct_index: 1,
      explanation: {
        en: "Observations need sources.",
        bn: "পর্যবেক্ষণের উৎস দরকার।",
      },
      source_url: "https://example.com",
      image_question: false,
    };
    const story = {
      place: { id: "test" },
      release: { content_version: "test" },
      quiz: [question, question, question, question, question],
      imagery: pair,
    } as unknown as Story;
    mount(<Quiz story={story} />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Check answer" }),
      ).toBeDisabled(),
    );
    fireEvent.click(
      screen.getByRole("radio", { name: /A measured observation/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));
    expect(screen.getByText("You spotted it.")).toBeInTheDocument();
    expect(screen.getByText("Observations need sources.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next question" }));
    expect(screen.getByText("Question 2 / 5")).toBeInTheDocument();
  });
});
