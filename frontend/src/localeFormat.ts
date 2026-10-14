import { appIntlLocale } from "./i18n";
import { getTerritoryFormatting } from "./territoryConfig";

export function intlLocale(): string {
  return appIntlLocale();
}

export function territoryCurrencyCode(): string {
  return getTerritoryFormatting().currency || "USD";
}

function territoryCurrency(): string {
  return territoryCurrencyCode();
}

/** Locale-formatted zero amount (for copy such as "lapse to {{zeroAmount}}"). */
export function formatMoneyZero(): string {
  return formatMoney(0);
}

type NumberFormatOptions = Intl.NumberFormatOptions & { currency?: string };

const formatters = new Map<string, Intl.NumberFormat>();

function numberFormatter(options: NumberFormatOptions): Intl.NumberFormat {
  const locale = intlLocale();
  const currency = options.currency ?? territoryCurrency();
  const { currency: _c, ...rest } = options;
  const key = `${locale}|${currency}|${JSON.stringify(rest)}`;
  let fmt = formatters.get(key);
  if (!fmt) {
    fmt =
      rest.style === "currency"
        ? new Intl.NumberFormat(locale, { ...rest, currency })
        : new Intl.NumberFormat(locale, rest);
    formatters.set(key, fmt);
  }
  return fmt;
}

/** Clear cached Intl formatters (e.g. after territory or language change). */
export function resetLocaleFormatters(): void {
  formatters.clear();
}

export function formatMoney(n?: number | null): string {
  if (n == null || Number.isNaN(n)) return "—";
  return numberFormatter({
    style: "currency",
    currency: territoryCurrency(),
    currencyDisplay: "narrowSymbol",
    maximumFractionDigits: 0,
  }).format(n);
}

/** Compact currency for chart axes (locale symbol + grouping). */
export function formatCompactMoney(n: number): string {
  return numberFormatter({
    style: "currency",
    currency: territoryCurrency(),
    currencyDisplay: "narrowSymbol",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

/** @deprecated use formatMoney — kept for existing imports */
export function formatMoneyIls(n?: number | null): string {
  return formatMoney(n);
}

export function formatNumber(n: number): string {
  return numberFormatter({ maximumFractionDigits: 20 }).format(n);
}

/** Compact integer/count labels for charts (locale grouping + K/M/B). */
export function formatCompactNumber(n: number): string {
  return numberFormatter({
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

export function formatDecimal(n: number, maximumFractionDigits: number): string {
  return numberFormatter({ maximumFractionDigits }).format(n);
}

/** Format a value already expressed as a percentage (e.g. 12.5 → 12.5%). */
export function formatPercentValue(n: number, maximumFractionDigits = 1): string {
  return numberFormatter({
    style: "percent",
    maximumFractionDigits,
  }).format(n / 100);
}

export function formatDateTime(iso: string | null | undefined, empty = "—"): string {
  if (!iso) return empty;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16).replace("T", " ");
  return d.toLocaleString(intlLocale(), {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function formatMonthYear(yearMonth: string): string {
  const [y, m] = yearMonth.split("-");
  if (!y || !m) return yearMonth;
  return new Date(Number(y), Number(m) - 1, 1).toLocaleString(intlLocale(), {
    month: "short",
    year: "numeric",
  });
}

export function formatBytes(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)} GB`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} KB`;
  return `${n} B`;
}

/** Format a unitless rate in 0–1 range as a percentage string. */
export function formatRatePercent(
  rate: number | null | undefined,
  digits = 1,
  empty = "—",
): string {
  if (rate == null || Number.isNaN(rate)) return empty;
  return formatPercentValue(rate * 100, digits);
}

export function qualityStatusClass(status: string): string {
  if (status === "critical") return "quality-badge quality-critical";
  if (status === "warn") return "quality-badge quality-warn";
  return "quality-badge quality-ok";
}
