import { useState } from "react";
import {
  Bookmark,
  Download,
  ArrowRight,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { savedPacks, removePack, savePack, repairPack } from "../lib/offline";
import { useOnlineStatus } from "../lib/online";
import { api } from "../lib/api";
import { date, size } from "../lib/format";
import { Eyebrow, ErrorState, Spinner, useLocale } from "../components/shared";

export default function Saved() {
  const { t } = useTranslation();
  const locale = useLocale();
  const client = useQueryClient();
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const online = useOnlineStatus();
  const packs = useQuery({
    queryKey: ["saved"],
    queryFn: savedPacks,
    networkMode: "always",
  });
  async function update(id: string, repair = false) {
    setBusy(id);
    setError("");
    try {
      if (repair) await repairPack(id);
      else await savePack(await api.story(id));
      await client.invalidateQueries({ queryKey: ["saved"] });
    } catch {
      setError(t("savingFailed"));
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="section-width page-section">
      <Eyebrow>{t("savedEyebrow")}</Eyebrow>
      <h1 className="page-title">{t("savedTitle")}</h1>
      <p className="page-intro">{t("savedText")}</p>
      {error && (
        <p role="alert" className="inline-error">
          {error}
        </p>
      )}
      {packs.isPending ? (
        <Spinner />
      ) : packs.isError ? (
        <ErrorState />
      ) : packs.data.length === 0 ? (
        <div className="empty-saved">
          <Bookmark size={46} strokeWidth={1} />
          <h2>{t("noSaved")}</h2>
          <p>{t("noSavedText")}</p>
          <Link className="button primary" to={`/${locale}/explore`}>
            {t("browseStories")}
            <ArrowRight size={17} />
          </Link>
        </div>
      ) : (
        <div className="saved-grid">
          {packs.data.map((pack) => {
            const story = pack.story;
            const href = story.place.featured
              ? `/${locale}/story/${pack.id}?release=${pack.release}`
              : `/${locale}/explore/point?id=${pack.id}&release=${pack.release}`;
            return (
              <div className="saved-card" key={pack.id}>
                {story.imagery.after ? (
                  <img src={story.imagery.after.thumbnail_url} alt="" />
                ) : (
                  <div className="saved-icon">
                    <Bookmark size={32} />
                  </div>
                )}
                <div>
                  <span className="small-label">
                    {t("savedOn")} · {date(pack.savedAt, locale)}
                  </span>
                  <h2>{story.place.name[locale]}</h2>
                  <p>
                    <Download size={14} />
                    {size(pack.bytes)} · বাংলা / English
                  </p>
                  {pack.mediaStatus !== "complete" && (
                    <p className="pack-warning" role="status">
                      {t("packIncomplete")}
                    </p>
                  )}
                  <Link className="quiet-link" to={href}>
                    {t("openStory")}
                    <ArrowRight size={16} />
                  </Link>
                </div>
                <div className="saved-card-actions">
                  <button
                    disabled={busy === pack.id || !online}
                    onClick={() =>
                      void update(pack.id, pack.mediaStatus !== "complete")
                    }
                    title={
                      pack.mediaStatus !== "complete"
                        ? t("repairPack")
                        : t("update")
                    }
                    aria-label={`${pack.mediaStatus !== "complete" ? t("repairPack") : t("update")} ${story.place.name[locale]}`}
                  >
                    <RefreshCw
                      className={busy === pack.id ? "spin" : ""}
                      size={17}
                    />
                  </button>
                  <button
                    onClick={() =>
                      void removePack(pack.id).then(() =>
                        client.invalidateQueries({ queryKey: ["saved"] }),
                      )
                    }
                    aria-label={`${t("remove")} ${story.place.name[locale]}`}
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
      <p className="saved-limit">{t("packLimit")}</p>
    </div>
  );
}
