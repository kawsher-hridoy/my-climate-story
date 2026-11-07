import type { ClimateComponent, Locale } from "./types";
export const number = (value: number, locale: Locale, digits = 0) =>
  new Intl.NumberFormat(locale === "bn" ? "bn-BD" : "en-GB", {
    useGrouping: false,
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
export const parseCoordinate = (value: string) =>
  value.trim()
    ? Number(
        value
          .trim()
          .replace(/[০-৯]/g, (char) => String(char.charCodeAt(0) - 0x09e6))
          .replaceAll("−", "-"),
      )
    : NaN;
export const date = (value: string, locale: Locale) =>
  new Intl.DateTimeFormat(locale === "bn" ? "bn-BD" : "en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value.length === 10 ? `${value}T12:00:00Z` : value));
export const size = (bytes: number) =>
  bytes < 1024 * 1024
    ? `${Math.ceil(bytes / 1024)} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
const divisions: Record<string, string> = {
  "Dhaka Division": "ঢাকা বিভাগ",
  "Chattogram Division": "চট্টগ্রাম বিভাগ",
  "Khulna Division": "খুলনা বিভাগ",
  "Rajshahi Division": "রাজশাহী বিভাগ",
  "Sylhet Division": "সিলেট বিভাগ",
  "Barishal Division": "বরিশাল বিভাগ",
  "Rangpur Division": "রংপুর বিভাগ",
  "Mymensingh Division": "ময়মনসিংহ বিভাগ",
};
export const division = (name: string, locale: Locale) =>
  locale === "bn" ? (divisions[name] ?? name) : name;
export function downloadCsv(component: ClimateComponent, release: string) {
  const rows = [
    [
      "period",
      "resolution",
      "value",
      "unit",
      "dataset",
      "release",
      "publication_state",
    ],
    ...component.annual!.map((x) => [
      x.year,
      "annual",
      x.value ?? "",
      component.source.unit,
      component.source.id,
      release,
      component.publication_state,
    ]),
    ...component.monthly!.map((x) => [
      x.date,
      "monthly",
      x.value ?? "",
      component.source.unit,
      component.source.id,
      release,
      component.publication_state,
    ]),
  ];
  const csv = rows
    .map((row) =>
      row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","),
    )
    .join("\r\n");
  const url = URL.createObjectURL(
    new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${component.series_id}.csv`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
