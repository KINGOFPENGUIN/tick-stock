import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type MarketCode = "CN" | "US";

interface MarketState {
  market: MarketCode;
  isUs: boolean;
  isCn: boolean;
  usDataSource: string;
  loading: boolean;
  setMarket: (market: MarketCode) => Promise<void>;
  refresh: () => Promise<void>;
}

const MarketContext = createContext<MarketState | null>(null);

async function fetchCurrentMarket(): Promise<{
  market: MarketCode;
  us_data_source: string;
}> {
  const response = await fetch("/api/market/current");
  if (!response.ok) {
    throw new Error("Failed to load current market");
  }
  return response.json();
}

export function MarketProvider({ children }: { children: ReactNode }) {
  const [market, setMarketState] = useState<MarketCode>("CN");
  const [usDataSource, setUsDataSource] = useState("none");
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    try {
      const data = await fetchCurrentMarket();
      setMarketState(data.market);
      setUsDataSource(data.us_data_source);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const setMarket = async (nextMarket: MarketCode) => {
    setLoading(true);
    try {
      const response = await fetch("/api/market/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ market: nextMarket }),
      });
      if (!response.ok) {
        throw new Error("Failed to switch market");
      }
      const data = await response.json();
      setMarketState(data.market);
      setUsDataSource(data.us_data_source);
    } finally {
      setLoading(false);
    }
  };

  return (
    <MarketContext.Provider
      value={{
        market,
        isUs: market === "US",
        isCn: market === "CN",
        usDataSource,
        loading,
        setMarket,
        refresh,
      }}
    >
      {children}
    </MarketContext.Provider>
  );
}

export function useMarket(): MarketState {
  const context = useContext(MarketContext);
  if (!context) {
    throw new Error("useMarket must be used within MarketProvider");
  }
  return context;
}
