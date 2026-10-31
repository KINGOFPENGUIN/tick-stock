import { useMarket, type MarketCode } from "../markets/MarketContext";

const OPTIONS: { code: MarketCode; label: string }[] = [
  { code: "CN", label: "A股" },
  { code: "US", label: "美股" },
];

export function MarketSwitcher() {
  const { market, setMarket, loading } = useMarket();

  return (
    <div className="inline-flex items-center rounded-lg border border-slate-200 bg-white p-0.5 text-sm shadow-sm">
      {OPTIONS.map((option) => (
        <button
          key={option.code}
          type="button"
          disabled={loading || market === option.code}
          onClick={() => void setMarket(option.code)}
          className={
            market === option.code
              ? "rounded-md bg-slate-900 px-3 py-1 font-medium text-white"
              : "rounded-md px-3 py-1 text-slate-600 hover:bg-slate-100"
          }
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
