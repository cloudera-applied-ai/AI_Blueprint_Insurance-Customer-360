/** Mutable territory formatting state (hydrated from /api/app-context). */

export type TerritoryFormatting = {
  currency: string;
  intl_locale: string;
  territory_id: string;
  supported_ui_locales: string[];
};

let state: TerritoryFormatting = {
  currency: "GBP",
  intl_locale: "en-GB",
  territory_id: "gb",
  supported_ui_locales: ["en", "fr", "es", "he", "ar"],
};

export function setTerritoryFormatting(next: Partial<TerritoryFormatting>): void {
  state = { ...state, ...next };
}

export function getTerritoryFormatting(): TerritoryFormatting {
  return state;
}
