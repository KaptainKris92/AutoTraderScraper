import { useState, useEffect } from "react";
import { FaHeart, FaSearch, FaLink, FaEye, FaUnlink } from "react-icons/fa";
import BindMOTModal from "./BindMOTModal";
import MOTHistoryModal from "./MOTHistoryModal";

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
  const [showBindModal, setShowBindModal] = useState(false);
  const [showMOTModal, setShowMOTModal] = useState(false);
  const [boundReg, setBoundReg] = useState(null);
  const [regInput, setRegInput] = useState("");

  // Fetch the bound registration number
  const fetchBoundReg = async () => {
    const res = await fetch (`/api/mot_history?ad_id=${ad["Ad ID"]}`);
    const data = await res.json();
    if (data.length > 0) {
      setBoundReg(data[0].registration);
    } else {
      setBoundReg(null);
    }
  };

  // Show reg number bound to ad
  useEffect(() => {
    fetchBoundReg();
  }, [ad]);


  // Unbinding reg numbers
  const handleUnbind = async () => {
    if (!boundReg) return;
    await fetch(`/api/mot_history/bind`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ registration: boundReg, ad_id: "" }),      
    });
    setBoundReg(null); // Update UI
  }

  // Quick search 
  const handleQuickSearch = async() => {
    try {
      const res = await fetch (`/api/mot_history/query?reg=${encodeURIComponent(regInput)}`);
      const data = await res.json();
      if (!data || data.error) throw new Error(data.error || "Invalid response");

      await fetch("/api/mot_history", {
        method: "POST",
        headers: { "Content-Type" : "application/json" },
        body: JSON.stringify({ registration: regInput.replace(/\s+/g, "").toUpperCase(), data, ad_id: null }),        
      });

      setRegInput("");
      alert("✅ MOT history saved.");      
    } catch (err) {
      console.error("❌ MOT search failed:", err);
      alert("Failed to retrieve MOT history. Please check the registration number.");
    }
      
  }

  if (!ad || Object.keys(ad).length === 0) {
    return <div className="text-center p-4">Invalid ad data</div>;
  }

  return (
    <div className="w-full max-w-md mx-auto bg-white rounded-2xl shadow-md overflow-hidden sm:rounded-xl sm:shadow-lg">
    
      {/* Thumbnail image  + quick reg input */}
      <div className="relative w-full aspect-[4/3] sm:h-80 sm:aspect-auto bg-gray-100">
      <img
        src={`/api/thumbnail/${ad["Ad ID"]}`}
        alt={`Thumbnail for ${ad?.Title || "car"}`}
        className="w-full h-full object-cover"
      />

      {/* AutoTrader logo & URL */}
      {ad?.["Ad URL"] && (
        <a
          href={ad["Ad URL"]}
          target="_blank"
          rel="noopener noreferrer"
          title="View on AutoTrader"
          className="absolute bottom-0.5 left--1 rounded p-1 z-30"
        >
          <img
            src="/icons/autotrader-logo-small.png"
            alt="AutoTrader"
            className="w-12 h-15 hover:scale-110 transition-transform"
          />
        </a>
      )}
      </div>

      {/* Quick reg input overlay */}
      <div className="absolute bottom-1 left-1 right-1 bg-white/80 p-1 flex gap-2 items-center justify-center rounded shadow-md">
        <input
          type="text"
          placeholder="Enter Reg"
          value={regInput}
          onChange={(e) => setRegInput(e.target.value.toUpperCase())}
          className="text-xs text-center border p-1 rounded w-24"
        />
        <button
          onClick={handleQuickSearch}
          className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <FaSearch />
        </button>
      </div>      

      <div className="p-4 space-y-2 text-center">
        {/* Mileage & Reg Year */}
        <div className="flex justify-between text-sm text-gray-600 font-medium">
          <span>
            {ad?.Mileage && typeof ad.Mileage === "number"
              ? ad.Mileage.toLocaleString() + " mi"
              : "Unknown mileage"}
          </span>

          {/* Bound registration */}
          {boundReg && <div className="text-xs text-gray-500">Reg: {boundReg}</div>}   

          <span>{ad?.["Registered Year"] || "Unknown year"}</span>
        </div>
        
        {/* Title & Subtitle */}
        <div className="relative flex flex-col items-center">
          {/* Ad Title */}
          <div className="text-lg font-bold text-gray-800">{ad?.Title || "No title"}</div>
          
          {/* Subtitle */}
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
            <div className="text-[12px] text-zinc-500 italic mb-6">
              {getDaysAgo(ad["Ad post date"])} 
              </div>
          )}
        </div>
        
        {/* 'Favourited' indicator */}
        {ad.Favourited === 1 && (
          <div className = "absolute bottom-2 left-2 text-pink-500 text-xl">
            <FaHeart />
          </div>
        )}

        {/* Bind/Unbind + View MOT history */}
        {boundReg ? (
          <>
            {/* View bound MOT History */}
            <button
              onClick={() => setShowMOTModal(true)}
              className="absolute bottom-2 right-10 text-blue-600 text-xl z-20"
              title="View MOT History"
            >
              <FaEye />
            </button>

            {/* Unbind MOT History */}
            <button
              className="absolute bottom-2 right-3 text-red-600 text-xl z-20"
              onClick={handleUnbind}
              title="Unbind MOT"
            >
              <FaUnlink />
            </button>
          </>
        ) : (
          <button
            className="absolute bottom-2 right-2 text-blue-600 text-xl z-20"
            onClick={() => setShowBindModal(true)}
            title="Bind MOT"
          >
            <FaLink />
          </button>
        )}
      </div>

      {showBindModal && (
        <BindMOTModal 
          adId={ad["Ad ID"]} 
          onClose={() => setShowBindModal(false)} 
          onBindSuccess={fetchBoundReg} 
        />
    )}
      {showMOTModal && (
        <MOTHistoryModal
          onClose={() => {
            setShowMOTModal(false);
            fetchBoundReg(); // Refresh boundReg when modal closes
          }}
          adId={ad["Ad ID"]}
          initialReg={boundReg}
        />
      )}
    </div>
  );
}
