import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  Globe2,
  MapPin,
  Satellite,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { number } from "../lib/format";
import {
  Eyebrow,
  ErrorState,
  PlaceCard,
  Spinner,
  useLocale,
} from "../components/shared";
import Landscape from "../components/Landscape";

export default function Home() {
  const { t } = useTranslation();
  const locale = useLocale();
  const places = useQuery({
    queryKey: ["featured"],
    queryFn: api.featured,
    staleTime: 300000,
  });
  return (
    <>
      <section className="hero section-width">
        <div className="hero-copy">
          <Eyebrow>{t("homeBadge")}</Eyebrow>
          <h1>{t("heroTitle")}</h1>
          <p className="hero-description">{t("heroDescription")}</p>
          <div className="hero-buttons">
            <Link className="button primary" to={`/${locale}/explore`}>
              <MapPin size={18} />
              {t("choosePlace")}
              <ArrowRight size={17} />
            </Link>
            <a className="quiet-link" href="#how-it-works">
              {t("howWorks")}
              <ArrowDown size={16} />
            </a>
          </div>
          <div className="nasa-attribution">
            <span className="orbit-mark">
              <Globe2 size={17} />
            </span>
            {t("nasaData")}
            <span className="tiny-dot" />
            POWER · Landsat · GISTEMP
          </div>
        </div>
        <div className="hero-art">
          <div className="art-note">
            <span className="tiny-dot" />
            {locale === "bn"
              ? "একটি জানালা, অনেক গল্প"
              : "ONE WINDOW. MANY STORIES."}
            <span className="art-note-number">01</span>
          </div>
          <Landscape />
          <div className="floating-note">
            <span className="note-icon">
              <Satellite size={21} />
            </span>
            <div>
              <strong>
                {locale === "bn" ? "সময়ের সঙ্গে দেখো" : "Look across time"}
              </strong>
              <span>
                {locale === "bn"
                  ? "আসল ছবি। নতুন প্রশ্ন।"
                  : "Real imagery. Fresh questions."}
              </span>
            </div>
            <Sparkles size={17} />
          </div>
        </div>
      </section>
      <section
        className="stats-strip section-width"
        aria-label={locale === "bn" ? "প্রকল্পের পরিসর" : "Project coverage"}
      >
        <div>
          <span className="stat-number">
            {number(12, locale)}
            <span className="stat-decoration">↗</span>
          </span>
          <span>{t("places")}</span>
        </div>
        <div>
          <span className="stat-number">
            {number(45, locale)}
            <span className="stat-decoration small">1981–2025</span>
          </span>
          <span>{t("years")}</span>
        </div>
        <div>
          <span className="stat-number">
            {number(2, locale)}
            <Globe2 className="stat-decoration" size={23} />
          </span>
          <span>{t("languages")}</span>
        </div>
      </section>
      <section className="featured-section section-width" id="stories">
        <div className="section-heading">
          <div>
            <Eyebrow>{t("featuredEyebrow")}</Eyebrow>
            <h2>{t("featuredTitle")}</h2>
            <p>{t("featuredDescription")}</p>
          </div>
          <Link className="quiet-link" to={`/${locale}/explore`}>
            {t("allPlaces")}
            <ArrowRight size={17} />
          </Link>
        </div>
        {places.isPending ? (
          <Spinner />
        ) : places.isError ? (
          <ErrorState retry={() => void places.refetch()} />
        ) : (
          <div className="places-grid">
            {places.data.slice(0, 6).map((place, index) => (
              <PlaceCard key={place.id} place={place} index={index} />
            ))}
          </div>
        )}
      </section>
      <section className="how-section" id="how-it-works">
        <div className="section-width">
          <Eyebrow>{t("stepsEyebrow")}</Eyebrow>
          <h2>{t("stepsTitle")}</h2>
          <div className="steps-grid">
            {[
              { icon: MapPin, title: "step1", text: "step1Text" },
              { icon: Satellite, title: "step2", text: "step2Text" },
              { icon: BookOpen, title: "step3", text: "step3Text" },
            ].map((step, index) => (
              <div className="step-card" key={step.title}>
                <span className="step-index">0{index + 1}</span>
                <step.icon size={30} strokeWidth={1.4} />
                <h3>{t(step.title)}</h3>
                <p>{t(step.text)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
