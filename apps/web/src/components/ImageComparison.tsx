import { useState } from "react";
import { Columns2, GripVertical, Image as ImageIcon } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { ImageryPair } from "../lib/types";
import { date, number } from "../lib/format";
import { useLocale } from "./shared";

export default function ImageComparison({ pair }: { pair: ImageryPair }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [position, setPosition] = useState(50);
  const [side, setSide] = useState(false);
  if (pair.status !== "approved" || !pair.before || !pair.after)
    return (
      <div className="image-pending">
        <ImageIcon size={38} strokeWidth={1} />
        <h3>{t("imagePending")}</h3>
        <p>{pair.caption[locale]}</p>
      </div>
    );
  const before = pair.before,
    after = pair.after;
  return (
    <>
      <div className="comparison-toolbar">
        <span>{number(pair.resolution_m ?? 30, locale)} m · Landsat</span>
        <button onClick={() => setSide(!side)}>
          <Columns2 size={16} />
          {side ? t("sliderView") : t("sideBySide")}
        </button>
      </div>
      {side ? (
        <div className="comparison-side">
          <figure>
            <img src={before.url} alt={before.alt[locale]} loading="lazy" />
            <figcaption>
              {t("before")} · {date(before.date, locale)}
            </figcaption>
          </figure>
          <figure>
            <img src={after.url} alt={after.alt[locale]} loading="lazy" />
            <figcaption>
              {t("after")} · {date(after.date, locale)}
            </figcaption>
          </figure>
        </div>
      ) : (
        <div className="comparison-slider">
          <img
            className="comparison-base"
            src={after.url}
            alt={after.alt[locale]}
            loading="lazy"
          />
          <div
            className="comparison-overlay"
            style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
          >
            <img src={before.url} alt={before.alt[locale]} loading="lazy" />
          </div>
          <span className="image-date old">
            {t("before")}
            <strong>{date(before.date, locale)}</strong>
          </span>
          <span className="image-date recent">
            {t("after")}
            <strong>{date(after.date, locale)}</strong>
          </span>
          <div className="slider-line" style={{ left: `${position}%` }}>
            <span>
              <GripVertical size={24} />
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={position}
            onChange={(event) => setPosition(Number(event.target.value))}
            aria-label={t("sliderLabel")}
            aria-valuetext={`${number(position, locale)}% ${t("before")}`}
            className="comparison-input"
          />
        </div>
      )}
      <p className="image-observation">{pair.caption[locale]}</p>
      <details className="source-details">
        <summary>{t("sourceDetails")}</summary>
        <div>
          <p>{pair.attribution}</p>
          <p>
            {t("sourceResolution")}: {number(pair.resolution_m ?? 30, locale)} m
            · {pair.crs}
          </p>
          <div className="image-sources-grid">
            {[before, after].map((asset) => (
              <div key={asset.product_id}>
                <strong>
                  {asset.sensor} · {date(asset.date, locale)}
                </strong>
                <p>
                  {t("validPixels")}:{" "}
                  {number(asset.valid_pixel_fraction * 100, locale, 1)}%
                </p>
                <a href={asset.source_url} target="_blank" rel="noreferrer">
                  {t("readSource")}
                </a>
                <code>{asset.product_id}</code>
              </div>
            ))}
          </div>
        </div>
      </details>
    </>
  );
}
