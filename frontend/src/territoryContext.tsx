import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchAppContext, type AppContext } from "./api";
import i18n, { syncI18nWithTerritory } from "./i18n/index";
import { resetLocaleFormatters } from "./localeFormat";
import { setTerritoryFormatting } from "./territoryConfig";

const DEFAULT_CONTEXT: AppContext = {
  territory_id: "gb",
  display_name: "United Kingdom",
  currency: "GBP",
  intl_locale: "en-GB",
  primary_ui_locale: "en",
  supported_ui_locales: ["en", "fr", "es", "he", "ar"],
  localizations: [],
  seed_language: "en",
  cities: [],
  llm_market_context: "UK insurance and pensions",
  portal_sms_url_template: "https://portal.example.co.uk/m/{customer_id}",
  updated_at: null,
  warehouse_territory_id: null,
  admin_territory_id: null,
  preferred_ui_locale: null,
  territory_mismatch: false,
};

type TerritoryContextValue = {
  context: AppContext;
  loading: boolean;
  refresh: () => Promise<void>;
};

const TerritoryContext = createContext<TerritoryContextValue>({
  context: DEFAULT_CONTEXT,
  loading: true,
  refresh: async () => {},
});

export function TerritoryProvider({ children }: { children: ReactNode }) {
  const [context, setContext] = useState<AppContext>(DEFAULT_CONTEXT);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchAppContext();
      setTerritoryFormatting({
        currency: data.currency,
        intl_locale: data.intl_locale,
        territory_id: data.territory_id,
        supported_ui_locales: data.supported_ui_locales,
      });
      resetLocaleFormatters();
      syncI18nWithTerritory(data.supported_ui_locales, "en");
      setContext(data);
    } catch {
      setContext(DEFAULT_CONTEXT);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({ context, loading, refresh }),
    [context, loading, refresh],
  );

  return (
    <TerritoryContext.Provider value={value}>{children}</TerritoryContext.Provider>
  );
}

export function useTerritory() {
  return useContext(TerritoryContext);
}
