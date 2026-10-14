import { useTranslation } from "react-i18next";
import { SavingsAumTrendPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: SavingsAumTrendPoint[];
  loading?: boolean;
};

export default function SavingsAumObjectiveChart({ series, loading }: Props) {
  const { t } = useTranslation();
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip(t("charts.savingsAum.legendAum"), p.accumulation_total),
      t("charts.savingsAum.tooltipSavingsPolicies", {
        count: formatTooltipCount(p.savings_policies),
      }),
    ],
  }));

  return (
    <AnalyticsLineChart
      title={t("charts.savingsAum.title")}
      subtitle={t("charts.savingsAum.subtitle")}
      points={points}
      loading={loading}
      interactive={false}
      series={[
        {
          id: "aum",
          visualKey: "obj-aum",
          label: t("charts.savingsAum.legendAum"),
          values: series.map((p) => p.accumulation_total),
          axis: "primary",
          valueFormat: "money",
        },
        {
          id: "savings-policies",
          visualKey: "obj-policies",
          label: t("charts.savingsAum.legendSavingsPolicies"),
          values: series.map((p) => p.savings_policies),
          axis: "secondary",
          valueFormat: "count",
        },
      ]}
      emptyMessage={t("charts.savingsAum.empty")}
    />
  );
}
