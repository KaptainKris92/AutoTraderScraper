import React from "react";

function getDaysAgo(postDateStr) {
  if (!postDateStr) return null;

  const postDate = new Date(postDateStr);
  const today = new Date();
  const diffTime = today - postDate;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (isNaN(diffDays)) return null;

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "1 day ago";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 14) return "Last week";
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;

  return "Over a year ago";
}



export default function AdCard({ ad }) {
  if (!ad || Object.keys(ad).length === 0) {
    return <div className="text-center p-4">Invalid ad data</div>;
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
      {/* Placeholder image */}
      <img
        src={`http://localhost:5000/api/thumbnail/${ad["Ad ID"]}`}
        alt={`Thumbnail for ${ad?.Title || "car"}`}
        className="w-full h-64 object-cover bg-gray-100"
      />

      <div className="p-4 space-y-2 text-center">
        {/* Mileage & Reg Year */}
        <div className="flex justify-between text-sm text-gray-600 font-medium">
          <span>
            {ad?.Mileage && typeof ad.Mileage === "number"
              ? ad.Mileage.toLocaleString() + " mi"
              : "Unknown mileage"}
          </span>
          <span>{ad?.["Registered Year"] || "Unknown year"}</span>
        </div>

        {/* Title & Subtitle */}
        <div>
          <div className="text-lg font-bold text-gray-800">{ad?.Title || "No title"}</div>
          <div className="text-sm text-gray-500">{ad?.Subtitle || ""}</div>
        </div>

        {/* Price */}
        <div className="text-2xl font-extrabold text-green-700">{ad?.Price || "£0"}</div>

        {/* Distance & Location */}
        <div className="text-sm text-gray-600">
          {ad?.["Distance (miles)"] ? `${ad["Distance (miles)"]} mi` : "Distance unknown"} ·{" "}
          {ad?.Location || "Unknown location"}
        </div>

        {/* Post Date */}
        <div className="text-xs text-zinc-500">
          <div>Posted: {ad?.["Ad post date"] || "Unknown"}</div>          
          {getDaysAgo(ad?.["Ad post date"]) && (
            <div className="text-[12px] text-zinc-500 italic">
              {getDaysAgo(ad["Ad post date"])} 
              </div>
          )}
        </div>

        {/* View Link */}
        <div className="pt-2">
          <a
            href={ad?.["Ad URL"] || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline text-sm"
          >
            View on AutoTrader
          </a>
        </div>
      </div>
    </div>
  );
}
