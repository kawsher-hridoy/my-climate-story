import { lazy, Suspense, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  LocateFixed,
  MapPin,
  Search,
  Satellite,
  Layers,
  LoaderCircle,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Job, Place } from "../lib/types";
import { division, parseCoordinate } from "../lib/format";
import {
  Eyebrow,
  ErrorState,
  PlaceCard,
  Spinner,
  useLocale,
} from "../components/shared";

const ExplorerMap = lazy(() => import("../components/ExplorerMap"));
export default function Explore() {
  const { t } = useTranslation();
  const locale = useLocale();
  const navigate = useNavigate();
  const featured = useQuery({ queryKey: ["featured"], queryFn: api.featured });
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selected, setSelected] = useState<Place | null>(null);
  const [point, setPoint] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [latitude, setLatitude] = useState("23.8103");
  const [longitude, setLongitude] = useState("90.4125");
  const [layer, setLayer] = useState("street");
  const [satelliteDate, setSatelliteDate] = useState("2025-02-08");
  const [tileError, setTileError] = useState(false);
  const [error, setError] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }
    const abort = new AbortController();
    const timer = setTimeout(() => {
      setSearching(true);
      setSearched(true);
      void api
        .search(query, locale, abort.signal)
        .then((result) => setResults(result.results))
        .catch(() => {
          if (!abort.signal.aborted)
            setResults(
              (featured.data ?? []).filter((place) =>
                [place.name.en, place.name.bn, ...(place.aliases ?? [])].some(
                  (name) => name.toLowerCase().includes(query.toLowerCase()),
                ),
              ),
            );
        })
        .finally(() => {
          if (!abort.signal.aborted) setSearching(false);
        });
    }, 300);
    return () => {
      clearTimeout(timer);
      abort.abort();
    };
  }, [query, locale, featured.data]);
  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const timer = setTimeout(
      () => {
        void api
          .job(job.id)
          .then((value) => {
            if (!mounted.current) return;
            setJob(value);
            if (value.status === "completed" && value.story_id)
              navigate(`/${locale}/explore/point?id=${value.story_id}`);
            if (value.status === "failed") {
              setError(value.message);
              setBusy(false);
            }
          })
          .catch(() => {
            setBusy(false);
            setError(t("errorText"));
          });
      },
      Math.max(2, job.retry_after ?? 5) * 1000,
    );
    return () => clearTimeout(timer);
  }, [job, locale, navigate, t]);
  function pickPoint(lat: number, lon: number) {
    setPoint({ latitude: lat, longitude: lon });
    setSelected(null);
    setLatitude(String(lat));
    setLongitude(String(lon));
    setError("");
  }
  function pickPlace(place: Place) {
    setSelected(place);
    setPoint(place.coordinates);
    setLatitude(String(place.coordinates.latitude));
    setLongitude(String(place.coordinates.longitude));
    setQuery("");
    setResults([]);
    setError("");
  }
  async function start() {
    if (selected?.featured) {
      navigate(`/${locale}/story/${selected.id}`);
      return;
    }
    if (!point) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.explore(
        selected ? { place_id: selected.id } : { coordinates: point },
      );
      if (!mounted.current) return;
      if (result.story)
        navigate(`/${locale}/explore/point?id=${result.story.place.id}`);
      else if (result.job) setJob(result.job);
    } catch {
      if (mounted.current) {
        setError(t("errorText"));
        setBusy(false);
      }
    }
  }
  function useCoordinates(event: React.FormEvent) {
    event.preventDefault();
    const lat = parseCoordinate(latitude),
      lon = parseCoordinate(longitude);
    if (
      !Number.isFinite(lat) ||
      !Number.isFinite(lon) ||
      Math.abs(lat) > 90 ||
      Math.abs(lon) > 180
    ) {
      setError(t("coordinatesInvalid"));
      return;
    }
    pickPoint(lat, lon);
  }
  return (
    <div className="section-width page-section">
      <Eyebrow>{t("exploreEyebrow")}</Eyebrow>
      <h1 className="page-title">{t("exploreTitle")}</h1>
      <p className="page-intro">{t("exploreText")}</p>
      <div className="explore-workspace">
        <div className="explore-controls">
          <label className="search-box">
            <Search size={19} />
            <input
              aria-label={t("searchLabel")}
              placeholder={t("searchPlaceholder")}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            {searching && <LoaderCircle className="spin" size={16} />}
          </label>
          {results.length > 0 && (
            <ul className="search-results">
              {results.map((place) => (
                <li key={place.id}>
                  <button onClick={() => pickPlace(place)}>
                    <MapPin size={17} />
                    <span>
                      <strong>{place.name[locale]}</strong>
                      <small>
                        {division(place.division, locale)} · {place.country} ·{" "}
                        {place.feature_type}
                      </small>
                    </span>
                    <ArrowRight size={15} />
                  </button>
                </li>
              ))}
            </ul>
          )}
          {searched && !searching && !results.length && (
            <p className="muted small-text">{t("searchNoResults")}</p>
          )}
          <p className="small-text muted">{t("searchNote")}</p>
          <button
            className="quiet-link location-button"
            onClick={() => {
              if (!navigator.geolocation) {
                setError(t("locationDenied"));
                return;
              }
              navigator.geolocation.getCurrentPosition(
                (position) =>
                  pickPoint(
                    position.coords.latitude,
                    position.coords.longitude,
                  ),
                () => setError(t("locationDenied")),
                { timeout: 10000, maximumAge: 60000 },
              );
            }}
          >
            <LocateFixed size={17} />
            {t("myLocation")}
          </button>
          <div className="selected-place">
            <span className="small-label">{t("selectedPlace")}</span>
            <h2>
              {selected
                ? selected.name[locale]
                : point
                  ? t("mapPin")
                  : t("choosePlace")}
            </h2>
            {point && (
              <p className="coordinates-label">
                {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}
              </p>
            )}
            <button
              className="button primary full-width"
              disabled={!point || busy}
              onClick={() => void start()}
            >
              {busy ? (
                <LoaderCircle className="spin" size={18} />
              ) : (
                <ArrowRight size={18} />
              )}{" "}
              {busy ? t("preparing") : t("viewStory")}
            </button>
          </div>
          {busy && (
            <p role="status" className="small-text muted">
              {t("preparingText")}
            </p>
          )}
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          <details className="coordinate-details">
            <summary>{t("coordinateSubmit")}</summary>
            <form onSubmit={useCoordinates}>
              <label>
                {t("latitude")}
                <input
                  value={latitude}
                  onChange={(event) => setLatitude(event.target.value)}
                  inputMode="decimal"
                />
              </label>
              <label>
                {t("longitude")}
                <input
                  value={longitude}
                  onChange={(event) => setLongitude(event.target.value)}
                  inputMode="decimal"
                />
              </label>
              <button className="button secondary" type="submit">
                {t("coordinateSubmit")}
              </button>
            </form>
          </details>
        </div>
        <div className="map-panel">
          <div className="map-toolbar">
            <div className="segmented">
              <button
                aria-pressed={layer === "street"}
                onClick={() => {
                  setLayer("street");
                  setTileError(false);
                }}
              >
                <Layers size={15} />
                {t("streetMap")}
              </button>
              <button
                aria-pressed={layer === "satellite"}
                onClick={() => {
                  setLayer("satellite");
                  setTileError(false);
                }}
              >
                <Satellite size={15} />
                {t("satelliteMap")}
              </button>
            </div>
            {layer === "satellite" && (
              <label className="date-input">
                {t("satelliteDate")}
                <input
                  type="date"
                  min="2000-02-24"
                  max="2025-12-31"
                  value={satelliteDate}
                  onChange={(event) => {
                    setSatelliteDate(event.target.value);
                    setTileError(false);
                  }}
                />
              </label>
            )}
          </div>
          {navigator.onLine ? (
            <Suspense fallback={<Spinner text={t("mapLoading")} />}>
              <ExplorerMap
                places={featured.data ?? []}
                selected={point}
                onSelect={pickPoint}
                onPlace={pickPlace}
                layer={layer}
                date={satelliteDate}
                onTileError={() => setTileError(true)}
              />
            </Suspense>
          ) : (
            <div className="offline-map">
              <img src="/world-overview.svg" alt="" />
              <p>{t("offlineMapNote")}</p>
              <Link className="button secondary" to={`/${locale}/saved`}>
                {t("saved")}
              </Link>
            </div>
          )}
          <p className="map-caption">
            {layer === "satellite" ? t("satelliteNote") : t("mapNote")}
            {tileError && (
              <span className="tile-warning">
                {" "}
                {locale === "bn"
                  ? "এই দৃশ্যের কিছু টাইল নেই।"
                  : "Some tiles are unavailable for this view."}
              </span>
            )}
          </p>
        </div>
      </div>
      <section className="explore-featured">
        <div className="section-heading">
          <h2>{t("featuredTitle")}</h2>
          <span className="small-label">{t("allPlaces")}</span>
        </div>
        {featured.isPending ? (
          <Spinner />
        ) : featured.isError ? (
          <ErrorState retry={() => void featured.refetch()} />
        ) : (
          <div className="places-grid">
            {featured.data.map((place, index) => (
              <PlaceCard key={place.id} place={place} index={index} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
