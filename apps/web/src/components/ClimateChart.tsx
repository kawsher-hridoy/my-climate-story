import { useMemo, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import { Download, Table2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { ClimateComponent, Story, Locale } from "../lib/types";
import { date, downloadCsv, number } from "../lib/format";
import { useLocale } from "./shared";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
  Filler,
);
type Row = { label: string; value: number | null | undefined };

function lineOptions(locale: Locale, unit: string): ChartOptions<"line"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) =>
            `${number(context.parsed.y ?? 0, locale, 1)} ${unit}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          maxTicksLimit: 8,
          color: "#64715e",
          font: { family: "DM Sans, Noto Sans Bengali" },
        },
      },
      y: {
        title: { display: true, text: unit, color: "#586859" },
        grid: { color: "#e9e8dd" },
        ticks: {
          color: "#64715e",
          maxTicksLimit: 6,
          callback: (value) => number(Number(value), locale, 1),
        },
      },
    },
  };
}

export function TemperatureChart({
  component,
  release,
}: {
  component: ClimateComponent;
  release: string;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [mode, setMode] = useState("annual");
  const [history, setHistory] = useState(false);
  const [year, setYear] = useState(
    String(component.annual?.at(-1)?.year ?? 2025),
  );
  const [table, setTable] = useState(false);
  const rows = useMemo<Row[]>(
    () =>
      mode === "annual"
        ? (component.annual ?? [])
            .filter((x) => history || x.year >= 2001)
            .map((x) => ({ label: number(x.year, locale), value: x.value }))
        : (component.monthly ?? [])
            .filter((x) => x.date.startsWith(year + "-"))
            .map((x) => ({ label: date(x.date, locale), value: x.value })),
    [component, mode, history, year, locale],
  );
  const data = {
    labels: rows.map((x) => x.label),
    datasets: [
      {
        label: `${t("temperature")} (°C)`,
        data: rows.map((x) => x.value),
        borderColor: "#a95737",
        backgroundColor: "rgba(169,87,55,.075)",
        fill: true,
        tension: 0.12,
        pointRadius: mode === "monthly" ? 3 : 0,
        borderWidth: 2.5,
        spanGaps: false,
      },
    ],
  };
  return (
    <>
      <div className="chart-controls">
        <div className="segmented">
          <button
            aria-pressed={mode === "annual"}
            onClick={() => setMode("annual")}
          >
            {t("annual")}
          </button>
          <button
            aria-pressed={mode === "monthly"}
            onClick={() => setMode("monthly")}
          >
            {t("monthly")}
          </button>
        </div>
        {mode === "annual" ? (
          <button
            className="chart-history"
            aria-pressed={history}
            onClick={() => setHistory(!history)}
          >
            {history ? t("recentRecord") : t("fullRecord")}
          </button>
        ) : (
          <select
            aria-label={locale === "bn" ? "বছর বেছে নাও" : "Select year"}
            value={year}
            onChange={(event) => setYear(event.target.value)}
          >
            {(component.annual ?? []).map((item) => (
              <option key={item.year} value={item.year}>
                {number(item.year, locale)}
              </option>
            ))}
          </select>
        )}
      </div>
      <div className="chart-container">
        <Line
          data={data}
          options={lineOptions(locale, "°C")}
          aria-label={`${t("temperature")}, ${t(mode)} (°C). ${t("dataTable")}.`}
          role="img"
        />
      </div>
      <div className="chart-bottom">
        <span className="chart-key">
          <span className="line-key" />
          {t("temperature")} · °C
        </span>
        <div>
          <button onClick={() => setTable(!table)}>
            <Table2 size={15} />
            {table ? t("hideTable") : t("dataTable")}
          </button>
          <button onClick={() => downloadCsv(component, release)}>
            <Download size={15} />
            {t("downloadCsv")}
          </button>
        </div>
      </div>
      {table && <DataTable rows={rows} unit="°C" />}
    </>
  );
}

export function RainfallChart({ component }: { component: ClimateComponent }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [table, setTable] = useState(false);
  const rows = (component.annual ?? [])
    .filter((x) => x.complete && x.value != null)
    .map((x) => ({ label: number(x.year, locale), value: x.value }));
  const options: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
      y: { title: { display: true, text: "mm/year" }, beginAtZero: true },
    },
  };
  return (
    <>
      <div className="chart-container">
        <Bar
          data={{
            labels: rows.map((x) => x.label),
            datasets: [
              {
                label: t("rainfall"),
                data: rows.map((x) => x.value),
                backgroundColor: "#658693",
                borderRadius: 3,
              },
            ],
          }}
          options={options}
          role="img"
          aria-label={`${t("rainfall")} · mm/year`}
        />
      </div>
      <button className="quiet-link" onClick={() => setTable(!table)}>
        <Table2 size={15} />
        {t("dataTable")}
      </button>
      {table && <DataTable rows={rows} unit="mm/year" />}
    </>
  );
}

export function GlobalChart({ context }: { context: Story["global_context"] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [table, setTable] = useState(false);
  const rows = context.annual.map((x) => ({
    label: number(x.year, locale),
    value: x.value,
  }));
  const data = {
    labels: rows.map((x) => x.label),
    datasets: [
      {
        label: t("globalBaseline"),
        data: rows.map((x) => x.value),
        borderColor: "#557866",
        backgroundColor: "rgba(85,120,102,.065)",
        fill: true,
        pointRadius: 0,
        borderWidth: 2.2,
        tension: 0.08,
      },
      {
        label: "1951–1980",
        data: rows.map(() => 0),
        borderColor: "#aaa992",
        borderDash: [4, 5],
        borderWidth: 1,
        pointRadius: 0,
      },
    ],
  };
  return (
    <>
      <div className="chart-container global-chart">
        <Line
          data={data}
          options={lineOptions(locale, "°C anomaly")}
          aria-label={t("globalBaseline")}
          role="img"
        />
      </div>
      <div className="chart-bottom">
        <span>{t("globalBaseline")}</span>
        <button onClick={() => setTable(!table)}>
          <Table2 size={15} />
          {t("dataTable")}
        </button>
      </div>
      {table && <DataTable rows={rows} unit="°C anomaly" />}
    </>
  );
}

function DataTable({ rows, unit }: { rows: Row[]; unit: string }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <div className="data-table-wrap" tabIndex={0}>
      <table>
        <caption>
          {t("dataTable")} · {unit}
        </caption>
        <thead>
          <tr>
            <th scope="col">{t("period")}</th>
            <th scope="col">{t("value")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              <td>
                {row.value == null ? "—" : number(row.value, locale, 2)} {unit}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
