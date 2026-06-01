import { useState, useEffect } from "react";

const API_URL = "http://localhost:8000";

function NewsItem({ item }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-gray-100 py-3">
      <button
        onClick={() => setOpen(!open)}
        className="text-left w-full text-sm text-gray-800 hover:text-blue-600 font-medium"
      >
        {item.title}
      </button>
      {open && (
        <div className="mt-2 text-xs text-gray-500 space-y-1">
          <p>출처: {item.source}</p>
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="text-blue-500 hover:underline"
          >
            기사 보기 →
          </a>
        </div>
      )}
    </div>
  );
}

function ReportSection({ report }) {
  if (!report) return (
    <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
      파이프라인을 실행하면 투자 가이드가 여기에 표시됩니다.
    </div>
  );

  // 백엔드 반환 구조: { success, result: { report, trend_data, stock_data, generated_at } }
  const result = report?.result?.report || report?.result || report;

  return (
    <div className="prose prose-sm max-w-none">
      <p className="text-xs text-gray-400 mb-4">생성 시각: {result?.generated_at}</p>
      <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
        {result?.report}
      </div>

      {/* 섹터별 뉴스 분포 */}
      {result?.trend_data?.clusters && (
        <div className="mt-6">
          <h3 className="text-base font-semibold text-gray-800 mb-3">🔥 섹터별 뉴스 분포</h3>
          <div className="space-y-2">
            {result.trend_data.clusters.map((cluster, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-20 shrink-0">{cluster.sector}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4">
                  <div
                    className="bg-blue-500 h-4 rounded-full text-xs text-white flex items-center justify-end pr-2"
                    style={{ width: `${Math.min(cluster.news_count, 100)}%` }}
                  >
                    {cluster.news_count}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 주가 데이터 */}
      {result?.stock_data?.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base font-semibold text-gray-800 mb-3">📈 관련 종목 주가</h3>
          <div className="grid grid-cols-2 gap-3">
            {result.stock_data.map((stock, i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-sm">{stock.name}</span>
                  <span className={`text-xs font-bold ${stock.change_pct >= 0 ? "text-red-500" : "text-blue-500"}`}>
                    {stock.change_pct >= 0 ? "▲" : "▼"} {Math.abs(stock.change_pct)}%
                  </span>
                </div>
                <p className="text-lg font-bold text-gray-800">{stock.current_price?.toLocaleString()}원</p>
                <div className="mt-2 text-xs text-gray-500 space-y-1">
                  {stock.roe && <p>ROE: {stock.roe}%</p>}
                  {stock.operating_margin && <p>영업이익률: {stock.operating_margin}%</p>}
                  {stock.per && <p>PER: {stock.per}</p>}
                </div>
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>52주 저가</span>
                    <span>52주 고가</span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${stock.price_position}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [news, setNews] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [collecting, setCollecting] = useState(false);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const res = await fetch(`${API_URL}/news/list?limit=20`);
      const data = await res.json();
      setNews(data.items || []);
    } catch (e) {
      console.error("뉴스 로딩 실패:", e);
    }
  };

  const collectNews = async () => {
    setCollecting(true);
    try {
      const res = await fetch(`${API_URL}/news/collect`, { method: "POST" });
      const data = await res.json();
      alert(data.message);
      fetchNews();
    } catch (e) {
      console.error("뉴스 수집 실패:", e);
    } finally {
      setCollecting(false);
    }
  };

  const runPipeline = async () => {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);

      const res = await fetch(`${API_URL}/invest/run-pipeline`, {
        method: "POST",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const data = await res.json();
      console.log("파이프라인 결과:", data);
      setReport(data);
      fetchNews();
    } catch (e) {
      console.error("파이프라인 실패:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">📈 뉴스 트렌드 분석 & 투자 가이드</h1>
            <p className="text-xs text-gray-500 mt-1">RSS 뉴스 수집 → 트렌드 분석 → AI 투자 가이드 생성</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={collectNews}
              disabled={collecting}
              className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {collecting ? "수집 중..." : "🔄 뉴스 수집"}
            </button>
            <button
              onClick={runPipeline}
              disabled={loading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "분석 중..." : "🤖 파이프라인 실행"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-4">
              📰 수집된 뉴스 <span className="text-gray-400 font-normal">({news.length}건)</span>
            </h2>
            <div className="overflow-y-auto max-h-[calc(100vh-200px)]">
              {news.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">수집된 뉴스가 없어요.</p>
              ) : (
                news.map((item, i) => <NewsItem key={i} item={item} />)
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-800 mb-4">📊 투자 가이드</h2>
            <div className="overflow-y-auto max-h-[calc(100vh-200px)]">
              <ReportSection report={report} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}