import {
  ArrowRight,
  LoaderCircle,
  RefreshCw,
  MapPin,
  ArrowUpRight,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Locale, Place, Source } from "../lib/types";
import { division } from "../lib/format";

export function useLocale(): Locale {
  return useParams().locale === "en" ? "en" : "bn";
}
export function Spinner({ text }: { text?: string }) {
  const { t } = useTranslation();
  return (
    <div className="loading-state" role="status">
      <LoaderCircle className="spin" size={24} />
      <span>{text ?? t("loading")}</span>
    </div>
  );
}
export function ErrorState({
  retry,
  message,
}: {
  retry?: () => void;
  message?: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="error-state" role="alert">
      <h2>{t("errorTitle")}</h2>
      <p>{message ?? t("errorText")}</p>
      {retry && (
        <button className="button secondary" onClick={retry}>
          <RefreshCw size={16} />
          {t("retry")}
        </button>
      )}
    </div>
  );
}
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="eyebrow">
      <span />
      {children}
    </p>
  );
}
export function PlaceCard({
  place,
  index = 0,
}: {
  place: Place;
  index?: number;
}) {
  const locale = useLocale();
  const { t } = useTranslation();
  const preview = (place as Place & { preview_image_url?: string | null })
    .preview_image_url;
  return (
    <Link
      className={`place-card place-tone-${index % 4}`}
      to={`/${locale}/story/${place.id}`}
    >
      <div className="place-card-visual">
        {preview ? (
          <img src={preview} alt="" loading="lazy" />
        ) : (
          <MiniLandscape tone={index % 4} />
        )}
        <span className="place-card-coordinate">
          <MapPin size={11} />
          {place.coordinates.latitude.toFixed(2)}° N
        </span>
        <span className="place-arrow">
          <ArrowUpRight size={19} />
        </span>
      </div>
      <div className="place-card-copy">
        <span className="small-label">{division(place.division, locale)}</span>
        <h3>{place.name[locale]}</h3>
        <p>
          {t("openStory")} <ArrowRight size={14} />
        </p>
      </div>
    </Link>
  );
}
export function MiniLandscape({ tone = 0 }: { tone?: number }) {
  const greens = ["#ced9ab", "#b7d6c0", "#d7ce9f", "#c4d2b7"];
  return (
    <svg viewBox="0 0 360 180" aria-hidden="true">
      <rect width="360" height="180" fill={greens[tone]} />
      <path
        d="M-10 100C70 40 95 145 170 91S265 49 370 80"
        stroke="#84b7be"
        strokeWidth="38"
        fill="none"
      />
      <path
        d="M0 15 210 40 160 175M95 0 80 180M245 0 300 180"
        stroke="#f5efd8"
        strokeWidth="4"
        fill="none"
      />
      <g fill="#618b65">
        <circle cx="30" cy="40" r="15" />
        <circle cx="330" cy="120" r="23" />
        <circle cx="258" cy="28" r="17" />
      </g>
      <g fill="#f3e9d5" stroke="#ba7650" strokeWidth="2">
        <path d="M125 29h24v20h-24z" />
        <path d="m122 29 15-13 15 13" fill="#ba7650" />
        <path d="M217 130h26v21h-26z" />
        <path d="m214 130 16-14 16 14" fill="#ba7650" />
      </g>
    </svg>
  );
}
export function SourceDetails({ source }: { source: Source }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <details className="source-details">
      <summary>
        {t("source")}: {source.name}
        <ArrowUpRight size={14} />
      </summary>
      <div>
        <p>{source.notes[locale]}</p>
        <dl>
          <div>
            <dt>{t("coverage")}</dt>
            <dd>
              {source.start}–{source.end}
            </dd>
          </div>
          <div>
            <dt>{t("resolution")}</dt>
            <dd>{source.spatial_resolution}</dd>
          </div>
          <div>
            <dt>{t("unit")}</dt>
            <dd>{source.unit}</dd>
          </div>
        </dl>
        <p className="source-citation">{source.citation}</p>
        <a href={source.source_url} target="_blank" rel="noreferrer">
          {t("readSource")} <ArrowUpRight size={14} />
        </a>
      </div>
    </details>
  );
}
