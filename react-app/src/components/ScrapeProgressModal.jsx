import { useEffect, useState } from "react";

export default function ScrapeProgressModal({ profileId, onClose }) {
  const [status, setStatus] = useState("Starting...");

  const isError = status.startsWith("Error:");
  const isCancelled = status.startsWith("Cancelled.");
  const isComplete = status.startsWith("Complete.");

  useEffect(() => {
    let closeTimer;

    const poll = async () => {
      try {
        const res = await fetch(`/api/scrape-progress/${profileId}`);

        if (!res.ok) {
          throw new Error(`Progress request failed (${res.status})`);
        }

        const data = await res.json();
        const nextStatus = data.status ?? "Unknown status";

        setStatus(nextStatus);

        if (nextStatus.startsWith("Complete.")) {
          clearInterval(interval);
          closeTimer = setTimeout(onClose, 1500);
        } else if (
          nextStatus.startsWith("Error:") ||
          nextStatus.startsWith("Cancelled.")
        ) {
          clearInterval(interval);
        }
      } catch (err) {
        clearInterval(interval);
        setStatus(`Error: ${err.message}`);
      }
    };

    const interval = setInterval(poll, 500);
    poll();

    return () => {
      clearInterval(interval);

      if (closeTimer) {
        clearTimeout(closeTimer);
      }
    };
  }, [profileId]);

  const handleClose = async () => {
    if (!isError && !isCancelled && !isComplete) {
      await fetch(`/api/cancel-scraper/${profileId}`, {
        method: "POST",
      });
    }

    onClose();
  };

  const heading = isError
    ? "Scrape failed"
    : isCancelled
      ? "Scrape cancelled"
      : isComplete
        ? "Scrape complete"
        : "Scraping ads...";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex flex-col items-center justify-center text-white">
      <div className="text-xl mb-4">{heading}</div>

      <div className="text-sm text-gray-300 max-w-lg text-center break-words">
        {status}
      </div>

      {!isComplete && (
        <button
          onClick={handleClose}
          className="mt-4 px-3 py-1 bg-red-600 text-white rounded"
        >
          {isError || isCancelled ? "Close" : "Cancel"}
        </button>
      )}
    </div>
  );
}