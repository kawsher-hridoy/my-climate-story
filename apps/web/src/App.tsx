import { lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  Bookmark,
  Globe2,
  Leaf,
  Menu,
  WifiOff,
  X,
} from "lucide-react";
import {
  Link,
  NavLink,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useRegisterSW } from "virtual:pwa-register/react";
import i18n from "./lib/i18n";
import { Spinner, useLocale } from "./components/shared";
import Home from "./pages/Home";
const Explore = lazy(() => import("./pages/Explore"));
const Story = lazy(() => import("./pages/Story"));
const Saved = lazy(() => import("./pages/Saved"));
const Info = lazy(() => import("./pages/Info"));

function Layout() {
  const params = useParams();
  const locale = useLocale();
  const location = useLocation();
  const { t } = useTranslation();
  const [menu, setMenu] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const {
    needRefresh: [refresh, setRefresh],
    updateServiceWorker,
  } = useRegisterSW({ immediate: true });
  useEffect(() => {
    void import("./lib/offline")
      .then(({ migrateSavedPacks }) => migrateSavedPacks())
      .catch(() => undefined);
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
    void i18n.changeLanguage(locale);
    try {
      localStorage.setItem("climate-locale", locale);
    } catch {
      /* Storage can be disabled. */
    }
  }, [locale]);
  useEffect(() => {
    setMenu(false);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  if (params.locale !== "bn" && params.locale !== "en")
    return <Navigate to="/bn/" replace />;
  function langPath(language: string) {
    return (
      location.pathname.replace(/^\/(bn|en)(?=\/|$)/, `/${language}`) +
      location.search +
      location.hash
    );
  }
  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("skip")}
      </a>
      <header className="site-header">
        <div className="header-inner">
          <Link className="brand" to={`/${locale}/`} aria-label={t("brand")}>
            <span className="brand-icon">
              <Leaf size={26} strokeWidth={1.6} />
            </span>
            <span>
              <strong>{t("brand")}</strong>
              <small>{t("brandSmall")}</small>
            </span>
          </Link>
          <nav
            className={menu ? "main-nav open" : "main-nav"}
            aria-label={locale === "bn" ? "প্রধান মেনু" : "Main navigation"}
          >
            <NavLink to={`/${locale}/explore`}>{t("explore")}</NavLink>
            <NavLink to={`/${locale}/learn`}>{t("learn")}</NavLink>
            <NavLink to={`/${locale}/teachers`}>{t("teachers")}</NavLink>
            <NavLink className="saved-nav" to={`/${locale}/saved`}>
              <Bookmark size={16} />
              {t("saved")}
            </NavLink>
          </nav>
          <div className="header-actions">
            <div className="language-switch" aria-label={t("language")}>
              <Link
                aria-current={locale === "bn" ? "true" : undefined}
                to={langPath("bn")}
              >
                বাংলা
              </Link>
              <Link
                aria-current={locale === "en" ? "true" : undefined}
                to={langPath("en")}
              >
                EN
              </Link>
            </div>
            <button
              className="mobile-menu"
              aria-label={menu ? t("close") : t("menu")}
              aria-expanded={menu}
              onClick={() => setMenu(!menu)}
            >
              {menu ? <X size={23} /> : <Menu size={23} />}
            </button>
          </div>
        </div>
      </header>
      {!online && (
        <div className="offline-banner" role="status">
          <WifiOff size={15} />
          {t("offline")}
        </div>
      )}
      {refresh && (
        <div className="update-banner" role="status">
          {t("refreshAvailable")}
          <button onClick={() => void updateServiceWorker(true)}>
            {t("refresh")}
          </button>
          <button onClick={() => setRefresh(false)}>{t("dismiss")}</button>
        </div>
      )}
      <main id="main-content">
        <Suspense fallback={<Spinner />}>
          <Outlet />
        </Suspense>
      </main>
      <footer className="site-footer">
        <div className="section-width footer-top">
          <div>
            <Link className="footer-brand" to={`/${locale}/`}>
              <Leaf size={25} />
              {t("brand")}
            </Link>
            <p>{t("footerText")}</p>
          </div>
          <div className="footer-links">
            <Link to={`/${locale}/sources`}>
              {t("sources")}
              <ArrowUpRight size={14} />
            </Link>
            <Link to={`/${locale}/teachers`}>
              <BookOpen size={15} />
              {t("teachers")}
            </Link>
            <Link to={`/${locale}/about`}>{t("about")}</Link>
          </div>
          <div className="footer-planet">
            <Globe2 size={48} strokeWidth={1} />
            <span>
              {locale === "bn"
                ? "এক পৃথিবী। অনেক গল্প।"
                : "ONE EARTH. MANY STORIES."}
            </span>
          </div>
        </div>
        <div className="section-width footer-bottom">
          <span>{t("footerNote")}</span>
          <span>© 2026 My Climate Story</span>
        </div>
      </footer>
    </>
  );
}
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/bn/" replace />} />
      <Route path="/:locale" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="explore" element={<Explore />} />
        <Route path="explore/point" element={<Story />} />
        <Route path="story/:placeId" element={<Story />} />
        <Route path="saved" element={<Saved />} />
        <Route path="learn" element={<Info kind="learn" />} />
        <Route path="teachers" element={<Info kind="teachers" />} />
        <Route path="sources" element={<Info kind="sources" />} />
        <Route path="about" element={<Info kind="about" />} />
        <Route path="*" element={<Info kind="missing" />} />
      </Route>
    </Routes>
  );
}
