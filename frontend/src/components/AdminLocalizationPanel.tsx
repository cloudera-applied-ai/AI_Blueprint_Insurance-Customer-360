import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  fetchLocalizationAdmin,
  LocalizationAdminConfig,
  LocalizationOption,
  reseedWarehouse,
  TerritoryCatalogEntry,
  updateLocalizationAdmin,
} from "../api";
import { useTerritory } from "../territoryContext";

export default function AdminLocalizationPanel() {
  const { t } = useTranslation();
  const { refresh: refreshTerritoryContext } = useTerritory();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reseeding, setReseeding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [reseedNote, setReseedNote] = useState<string | null>(null);
  const [meta, setMeta] = useState<LocalizationAdminConfig | null>(null);
  const [territoryId, setTerritoryId] = useState<string>("");
  const [uiLocale, setUiLocale] = useState<string>("");
  const [useWarehouseTerritory, setUseWarehouseTerritory] = useState(true);
  const [reseedTerritoryId, setReseedTerritoryId] = useState("gb");
  const [reseedLanguage, setReseedLanguage] = useState("en");
  const [supportedLocales, setSupportedLocales] = useState<string[]>([
    "en",
    "fr",
    "es",
    "he",
    "ar",
  ]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cfg = await fetchLocalizationAdmin();
      setMeta(cfg);
      const adminTid = cfg.admin_territory_id ?? "";
      setUseWarehouseTerritory(!adminTid);
      setTerritoryId(adminTid || cfg.territory_id || "gb");
      setUiLocale(cfg.ui_locale ?? "");
      setSupportedLocales(
        cfg.supported_ui_locales?.length
          ? [...cfg.supported_ui_locales]
          : ["en", "fr", "es", "he", "ar"],
      );
      setReseedTerritoryId(cfg.warehouse_territory_id ?? cfg.territory_id ?? "gb");
      setReseedLanguage(
        cfg.warehouse_seed_language ??
          cfg.available_territories?.find(
            (r) => r.territory_id === (cfg.warehouse_territory_id ?? cfg.territory_id ?? "gb"),
          )?.default_seed_language ??
          "en",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : t("admin.localization.loadError"));
      setMeta(null);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedTerritory: TerritoryCatalogEntry | undefined = useMemo(
    () => meta?.available_territories?.find((row) => row.territory_id === territoryId),
    [meta, territoryId],
  );

  const localeOptions: LocalizationOption[] = useMemo(() => {
    const base =
      selectedTerritory?.localizations?.length
        ? selectedTerritory.localizations
        : (meta?.localizations ?? []);
    const allowed = new Set(supportedLocales);
    return base.filter((loc) => allowed.has(loc.code.split("-")[0] ?? loc.code));
  }, [selectedTerritory, meta, supportedLocales]);

  const toggleSupportedLocale = (code: string) => {
    setSupportedLocales((prev) => {
      const has = prev.includes(code);
      if (has && prev.length <= 1) {
        return prev;
      }
      if (has) {
        const next = prev.filter((c) => c !== code);
        if (uiLocale === code) {
          setUiLocale("");
        }
        return next;
      }
      return [...prev, code].sort(
        (a, b) =>
          (meta?.available_languages?.findIndex((l) => l.code === a) ?? 0) -
          (meta?.available_languages?.findIndex((l) => l.code === b) ?? 0),
      );
    });
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSavedNote(null);
    if (supportedLocales.length === 0) {
      setError(t("admin.localization.supportedLanguagesRequired"));
      setSaving(false);
      return;
    }
    try {
      const saved = await updateLocalizationAdmin({
        territory_id: useWarehouseTerritory ? null : territoryId,
        ui_locale: uiLocale.trim() ? uiLocale : null,
        supported_ui_locales: supportedLocales,
      });
      setMeta(saved);
      setSavedNote(t("admin.localization.saved"));
      await refreshTerritoryContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("admin.localization.saveError"));
    } finally {
      setSaving(false);
    }
  };

  const onReseed = async () => {
    const regionLabel =
      meta?.available_territories?.find((r) => r.territory_id === reseedTerritoryId)?.display_name ??
      reseedTerritoryId;
    const langLabel =
      meta?.available_languages?.find((l) => l.code === reseedLanguage)?.label ?? reseedLanguage;
    const ok = window.confirm(
      t("admin.localization.reseedConfirm", { region: regionLabel, language: langLabel }),
    );
    if (!ok) return;

    setReseeding(true);
    setError(null);
    setReseedNote(null);
    try {
      const result = await reseedWarehouse({
        territory_id: reseedTerritoryId,
        seed_language: reseedLanguage,
      });
      setReseedNote(
        t("admin.localization.reseedDone", {
          region: result.territory_id.toUpperCase(),
          language: result.seed_language,
          count: result.customer_count,
        }),
      );
      await load();
      await refreshTerritoryContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("admin.localization.reseedError"));
    } finally {
      setReseeding(false);
    }
  };

  if (loading) {
    return <p className="muted small">{t("admin.localization.loading")}</p>;
  }

  return (
    <form className="admin-localization" onSubmit={(e) => void onSubmit(e)}>
      {error && <p className="error">{error}</p>}
      {savedNote && <p className="success small">{savedNote}</p>}
      {reseedNote && <p className="success small">{reseedNote}</p>}

      {meta?.territory_mismatch && (
        <p className="admin-localization-warn" role="status">
          {t("admin.localization.mismatchWarning", {
            warehouse: meta.warehouse_territory_id ?? "—",
            admin: meta.admin_territory_id ?? territoryId,
          })}
        </p>
      )}

      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.localization.territoryLegend")}</legend>
        <p className="muted small">{t("admin.localization.territoryLede")}</p>
        <label className="admin-localization-check">
          <input
            type="checkbox"
            checked={useWarehouseTerritory}
            onChange={(e) => setUseWarehouseTerritory(e.target.checked)}
          />
          {t("admin.localization.useWarehouseTerritory", {
            id: meta?.warehouse_territory_id ?? t("common.emDash"),
          })}
        </label>
        {meta?.warehouse_seed_language && (
          <p className="muted small">
            {t("admin.localization.warehouseSeedLanguage", {
              language: meta.warehouse_seed_language,
            })}
          </p>
        )}
        <label className="admin-localization-field">
          <span>{t("admin.localization.territoryLabel")}</span>
          <select
            value={territoryId}
            disabled={useWarehouseTerritory}
            onChange={(e) => setTerritoryId(e.target.value)}
          >
            {(meta?.available_territories ?? []).map((row) => (
              <option key={row.territory_id} value={row.territory_id}>
                {row.display_name} ({row.territory_id.toUpperCase()}) · {row.currency}
              </option>
            ))}
          </select>
        </label>
      </fieldset>

      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.localization.supportedLanguagesLegend")}</legend>
        <p className="muted small">{t("admin.localization.supportedLanguagesLede")}</p>
        <div className="admin-localization-checks" role="group">
          {(meta?.available_languages ?? []).map((lang) => (
            <label key={lang.code} className="admin-localization-check">
              <input
                type="checkbox"
                checked={supportedLocales.includes(lang.code)}
                onChange={() => toggleSupportedLocale(lang.code)}
              />
              {lang.label} ({lang.code.toUpperCase()})
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.localization.localeLegend")}</legend>
        <p className="muted small">{t("admin.localization.localeLede")}</p>
        <label className="admin-localization-field">
          <span>{t("admin.localization.localeLabel")}</span>
          <select value={uiLocale} onChange={(e) => setUiLocale(e.target.value)}>
            <option value="">{t("admin.localization.localeDefault")}</option>
            {localeOptions.map((loc) => (
              <option key={loc.code} value={loc.code}>
                {loc.label} ({loc.bcp47})
              </option>
            ))}
          </select>
        </label>
      </fieldset>

      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.localization.reseedLegend")}</legend>
        <p className="muted small">{t("admin.localization.reseedLede")}</p>
        <label className="admin-localization-field">
          <span>{t("admin.localization.reseedRegionLabel")}</span>
          <select
            value={reseedTerritoryId}
            onChange={(e) => setReseedTerritoryId(e.target.value)}
          >
            {(meta?.available_territories ?? []).map((row) => (
              <option key={row.territory_id} value={row.territory_id}>
                {row.display_name} ({row.territory_id.toUpperCase()})
              </option>
            ))}
          </select>
        </label>
        <label className="admin-localization-field">
          <span>{t("admin.localization.reseedLanguageLabel")}</span>
          <select value={reseedLanguage} onChange={(e) => setReseedLanguage(e.target.value)}>
            {(meta?.available_languages ?? []).map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="btn secondary"
          disabled={reseeding}
          onClick={() => void onReseed()}
        >
          {reseeding ? t("admin.localization.reseeding") : t("admin.localization.reseedButton")}
        </button>
      </fieldset>

      {meta?.updated_at && (
        <p className="muted small">
          {t("admin.localization.lastUpdated", { date: meta.updated_at })}
        </p>
      )}

      <button type="submit" className="btn primary" disabled={saving}>
        {saving ? t("admin.localization.saving") : t("admin.localization.save")}
      </button>
    </form>
  );
}
