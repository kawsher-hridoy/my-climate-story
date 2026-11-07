import { lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Check,
  CloudRain,
  Globe2,
  Leaf,
  LoaderCircle,
  MapPin,
  Printer,
  Share2,
  Thermometer,
} from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getProgress,
  loadStoryWithOffline,
  savedStory,
  savePack,
  setProgress,
} from "../lib/offline";
import { date, division, number, size } from "../lib/format";
import {
  Eyebrow,
  ErrorState,
  SourceDetails,
  Spinner,
  useLocale,
} from "../components/shared";
import ImageComparison from "../components/ImageComparison";
import Quiz from "../components/Quiz";
import type { Story as StoryType } from "../lib/types";

const TemperatureChart = lazy(() =>
  import("../components/ClimateChart").then((module) => ({
    default: module.TemperatureChart,
  })),
);
const RainfallChart = lazy(() =>
  import("../components/ClimateChart").then((module) => ({
    default: module.RainfallChart,
  })),
);
const GlobalChart = lazy(() =>
  import("../components/ClimateChart").then((module) => ({
    default: module.GlobalChart,
  })),
);

export default function Story() {
  const { placeId } = useParams();
  const [search] = useSearchParams();
  const id = placeId ?? search.get("id") ?? "";
  const release = search.get("release") ?? undefined;
  const story = useQuery({
    queryKey: ["story", id, release],
    queryFn: () => loadStoryWithOffline(id, release),
    enabled: !!id,
    networkMode: "offlineFirst",
    retry: (failures) => navigator.onLine && failures < 1,
  });
  if (!id) return <ErrorState />;
  if (story.isPending) return <Spinner />;
  if (story.isError)
    return (
      <div className="section-width page-section">
        <ErrorState retry={() => void story.refetch()} />
      </div>
    );
  return <StoryContent key={story.data.place.id} story={story.data} />;
}

function StoryContent({ story }: { story: StoryType }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [packIncomplete, setPackIncomplete] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [copied, setCopied] = useState(false);
  const [done, setDone] = useState<string[]>([]);
  useEffect(() => {
    void savedStory(story.place.id)
      .then((pack) => {
        const matching = pack?.release === story.release.id;
        setIsSaved(matching && pack.mediaStatus === "complete");
        setPackIncomplete(matching && pack.mediaStatus !== "complete");
      })
      .catch(() => undefined);
    void getProgress(`actions-${story.place.id}`)
      .then((progress) => setDone(progress?.actions ?? []))
      .catch(() => undefined);
  }, [story.place.id, story.release.id]);
  async function save() {
    setSaving(true);
    setSaveError("");
    try {
      await savePack(story);
      setIsSaved(true);
      setPackIncomplete(false);
      await queryClient.invalidateQueries({ queryKey: ["saved"] });
    } catch {
      setSaveError(t("savingFailed"));
    } finally {
      setSaving(false);
    }
  }
  async function share() {
    const route = story.place.featured
      ? `/${locale}/story/${story.place.id}`
      : `/${locale}/explore/point?id=${story.place.id}`;
    const url =
      window.location.origin +
      route +
      (route.includes("?") ? "&" : "?") +
      `release=${story.release.id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setSaveError(
        locale === "bn"
          ? "ব্রাউজারের ঠিকানা কপি করে শেয়ার করো।"
          : "Copy the browser address to share this story.",
      );
    }
  }
  function toggleAction(id: string) {
    const next = done.includes(id)
      ? done.filter((x) => x !== id)
      : [...done, id];
    setDone(next);
    void setProgress(`actions-${story.place.id}`, { actions: next }).catch(
      () => undefined,
    );
  }
  const bytes =
    (story.imagery.before?.bytes ?? 0) +
    (story.imagery.after?.bytes ?? 0) +
    new TextEncoder().encode(JSON.stringify(story)).byteLength;
  const comparison = story.temperature.comparison;
  return (
    <article className="story-page">
      <header className="story-header section-width">
        <Link className="back-link" to={`/${locale}/explore`}>
          <ArrowLeft size={16} />
          {t("backExplore")}
        </Link>
        <div className="story-title-row">
          <div>
            <Eyebrow>{t("storyEyebrow")}</Eyebrow>
            <h1>{story.place.name[locale]}</h1>
            <p className="story-location">
              <MapPin size={15} />
              {division(story.place.division, locale)}
              <span>
                {" "}
                {story.place.coordinates.latitude.toFixed(4)},{" "}
                {story.place.coordinates.longitude.toFixed(4)}
              </span>
            </p>
          </div>
          <div className="story-actions">
            <button
              className={`button ${isSaved ? "saved-button" : "primary"}`}
              disabled={saving}
              onClick={() => void save()}
            >
              {saving ? (
                <LoaderCircle className="spin" size={16} />
              ) : isSaved ? (
                <Check size={16} />
              ) : (
                <Bookmark size={16} />
              )}{" "}
              {saving
                ? t("saving")
                : isSaved
                  ? t("savedOffline")
                  : t("saveOffline")}
            </button>
            <button
              className="icon-button"
              aria-label={t("share")}
              title={t("share")}
              onClick={() => void share()}
            >
              {copied ? <Check size={19} /> : <Share2 size={19} />}
            </button>
            <button
              className="icon-button"
              aria-label={t("print")}
              title={t("print")}
              onClick={() => window.print()}
            >
              <Printer size={19} />
            </button>
            <small>
              {t("downloadSize")} ≈ {size(bytes)}
            </small>
          </div>
        </div>
        <p className="story-introduction">{story.place.description[locale]}</p>
        {packIncomplete && (
          <p className="quality-note" role="status">
            {t("packIncomplete")}
          </p>
        )}
        {saveError && (
          <p className="inline-error" role="alert">
            {saveError}
          </p>
        )}
        {copied && (
          <span className="copy-feedback" role="status">
            {t("copied")}
          </span>
        )}
      </header>
      <div className="chapter-nav-wrap">
        <nav className="chapter-nav section-width" aria-label={t("chapter")}>
          {[
            "landscape",
            "temperature",
            "rainfall",
            "global",
            "quiz",
            "action",
          ].map((chapter, index) => (
            <a key={chapter} href={`#${chapter}`}>
              <span>0{index + 1}</span>
              {t(chapter)}
            </a>
          ))}
        </nav>
      </div>
      <div className="story-body section-width">
        <section id="landscape" className="story-section">
          <div className="story-section-heading">
            <span className="chapter-number">01</span>
            <div>
              <Eyebrow>{t("landscapeEyebrow")}</Eyebrow>
              <h2>{t("landscapeTitle")}</h2>
              <p>{t("landscapeText")}</p>
            </div>
          </div>
          <ImageComparison pair={story.imagery} />
        </section>
        <section id="temperature" className="story-section">
          <div className="story-section-heading">
            <span className="chapter-number">02</span>
            <div>
              <Eyebrow>{t("temperatureEyebrow")}</Eyebrow>
              <h2>{t("temperatureTitle")}</h2>
              <p>{t("temperatureText")}</p>
            </div>
          </div>
          <div className="data-card">
            <div className="data-card-heading">
              <span className="data-source-badge">
                <Thermometer size={16} />
                NASA POWER
              </span>
              <span className="small-label">
                {story.temperature.source.start}–{story.temperature.source.end}
              </span>
            </div>
            {story.temperature.publication_state === "provisional" && (
              <p className="quality-note">{t("provisional")}</p>
            )}
            <Suspense fallback={<Spinner />}>
              <TemperatureChart
                component={story.temperature}
                release={story.release.id}
              />
            </Suspense>
            <p className="regional-note">
              <MapPin size={13} />
              {t("regionalNote")}
            </p>
          </div>
          {comparison ? (
            <div className="decade-card">
              <div>
                <span className="small-label">{t("compareDecades")}</span>
                <h3>{comparison.explanation[locale]}</h3>
                <p>{t("descriptiveNote")}</p>
              </div>
              <div className="decade-values">
                <div>
                  <small>
                    {t("baselineMean")}
                    <span>{comparison.baseline_period}</span>
                  </small>
                  <strong>
                    {number(comparison.baseline_value, locale, 1)}
                    <em>°C</em>
                  </strong>
                </div>
                <ArrowRight size={22} />
                <div>
                  <small>
                    {t("recentMean")}
                    <span>{comparison.recent_period}</span>
                  </small>
                  <strong>
                    {number(comparison.recent_value, locale, 1)}
                    <em>°C</em>
                  </strong>
                </div>
              </div>
            </div>
          ) : (
            <p className="quality-note">{t("comparisonPending")}</p>
          )}
          {story.temperature.warning && (
            <p className="quality-note">{story.temperature.warning[locale]}</p>
          )}
          {(story.temperature.shared_series_with?.length ?? 0) > 0 && (
            <p className="quality-note">{t("sharedNote")}</p>
          )}
          <SourceDetails source={story.temperature.source} />
        </section>
        <section id="rainfall" className="story-section rain-section">
          <div className="story-section-heading">
            <span className="chapter-number">03</span>
            <div>
              <Eyebrow>{t("rainfallEyebrow")}</Eyebrow>
              <h2>{t("rainfallTitle")}</h2>
            </div>
          </div>
          {story.rainfall.publication_state === "unavailable" ? (
            <div className="rain-pending">
              <div className="rain-illustration">
                <CloudRain size={76} strokeWidth={1} />
                <span />
                <span />
                <span />
              </div>
              <div>
                <span className="pending-pill">
                  NASA IMERG · {t("pending")}
                </span>
                <h3>{t("rainfallPendingTitle")}</h3>
                <p>{t("rainfallPendingText")}</p>
                <details>
                  <summary>{t("rainfallExplain")}</summary>
                  <p>{t("rainfallWhy")}</p>
                </details>
              </div>
            </div>
          ) : (
            <div className="data-card">
              <Suspense fallback={<Spinner />}>
                <RainfallChart component={story.rainfall} />
              </Suspense>
            </div>
          )}
          <div className="thought-note">
            <Leaf size={21} />
            <div>
              <strong>{t("rainfallLearning")}</strong>
              <p>{t("rainfallPrompt")}</p>
            </div>
          </div>
          <SourceDetails source={story.rainfall.source} />
        </section>
        <section id="global" className="story-section">
          <div className="story-section-heading">
            <span className="chapter-number">04</span>
            <div>
              <Eyebrow>{t("globalEyebrow")}</Eyebrow>
              <h2>{t("globalTitle")}</h2>
              <p>{t("globalText")}</p>
            </div>
          </div>
          <div className="data-card">
            <div className="data-card-heading">
              <span className="data-source-badge">
                <Globe2 size={17} />
                NASA GISTEMP
              </span>
              <span className="small-label">
                {story.global_context.source.start}–
                {story.global_context.source.end}
              </span>
            </div>
            <Suspense fallback={<Spinner />}>
              <GlobalChart context={story.global_context} />
            </Suspense>
            <p className="regional-note">{t("globalNote")}</p>
          </div>
          <SourceDetails source={story.global_context.source} />
        </section>
        <section id="quiz" className="story-section">
          <div className="story-section-heading">
            <span className="chapter-number">05</span>
            <div>
              <Eyebrow>{t("quizEyebrow")}</Eyebrow>
              <h2>{t("quizTitle")}</h2>
              <p>{t("quizText")}</p>
            </div>
          </div>
          <Quiz story={story} />
        </section>
        <section id="action" className="story-section">
          <div className="story-section-heading">
            <span className="chapter-number">06</span>
            <div>
              <Eyebrow>{t("actionEyebrow")}</Eyebrow>
              <h2>{t("actionTitle")}</h2>
              <p>{t("actionText")}</p>
            </div>
          </div>
          <div className="action-grid">
            {story.actions.map((action) => (
              <div
                className={`action-card ${done.includes(action.id) ? "chosen" : ""}`}
                key={action.id}
              >
                <span className="action-audience">
                  <Leaf size={15} />
                  {t(action.audience)}
                </span>
                <h3>{action.title[locale]}</h3>
                <p>{action.description[locale]}</p>
                <label>
                  <input
                    type="checkbox"
                    checked={done.includes(action.id)}
                    onChange={() => toggleAction(action.id)}
                  />
                  {t("actionDone")}
                </label>
                <a href={action.source_url} target="_blank" rel="noreferrer">
                  {t("source")} ↗
                </a>
              </div>
            ))}
          </div>
        </section>
        <div className="story-end">
          <div>
            <strong>
              {locale === "bn"
                ? "গল্প এখানেই শেষ নয়।"
                : "The story keeps going."}
            </strong>
            <p>
              {locale === "bn"
                ? "আরেকটি জায়গা দেখো, বা এই গল্পটি কাছে রাখো।"
                : "Explore another place, or keep this story close."}
            </p>
          </div>
          <Link className="button secondary" to={`/${locale}/explore`}>
            {t("explore")}
            <ArrowRight size={17} />
          </Link>
        </div>
        <p className="release-label">
          {t("dataRelease")}: {story.release.id} ·{" "}
          {date(story.release.created_at, locale)}
        </p>
      </div>
    </article>
  );
}
