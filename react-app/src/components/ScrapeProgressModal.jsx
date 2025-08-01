import { useEffect, useState } from "react";

export default function ScrapeProgressModal({ profileId, onClose }) {
  const [status, setStatus] = useState("Starting...");

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/api/scrape-progress/${profileId}`);
      const data = await res.json();
      setStatus(data.status);
      if (data.status === "Complete.") {
        clearInterval(interval);
        setTimeout(onClose, 1000);  // Slight delay before closing
      }
    }, 500);

    return () => clearInterval(interval);
  }, [profileId]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex flex-col items-center justify-center text-white">
      <div className="text-xl mb-4 animate-pulse">Scraping ads...</div>
      <div className="text-sm text-gray-300">{status}</div>

      <button onClick={async () => {
        await fetch(`/api/cancel-scraper/${profileId}`, { method: "POST" });
        onClose();
      }}
      className = "mt-4 px-3 py-1 bg-red-600 text-white rounded"
      >
        Cancel
      </button>
    </div>
  );
}
