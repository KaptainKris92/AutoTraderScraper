import React, { useState, useEffect } from "react";
import CardViewer from "./components/CardViewer";

function App() {  

  const [ads, setAds] = useState([]);
  const [sortBy, setSortBy] = useState("Ad post date");
  const [sortDirection, setSortDirection] = useState("asc");

  useEffect(() => {
    fetch("api/ads")
      .then((res) => res.json())
      .then((data) => {
        const sorted = sortAds(data, sortBy, sortDirection);        
        setAds(sorted);
      })
      .catch((err) => console.error("Failed to load ads:", err));
  }, [sortBy, sortDirection]);

  const sortAds = (adsArray, key, direction = "desc") => {
    const keyMap = {
      "Price": (ad) => parseInt(ad.Price.replace(/[^0-9]/g, "")) || 0,
      "Mileage": (ad) => ad.Mileage || 0,
      "Registered Year": (ad) => {
        const yearMatch = ad["Registered Year"]?.match(/\d{4}/);
        return yearMatch ? parseInt(yearMatch[0]) : 0;
      },
      "Distance": (ad) => ad["Distance (miles)"] || 0,
      "Ad post date": (ad) => new Date(ad["Ad post date"]),
      "Scraped at": (ad) => new Date(ad["Scraped at"])   
    };

    return [...adsArray].sort((a, b) => {
      const valA = keyMap[key](a);
      const valB = keyMap[key](b);

      if (valA > valB) return direction === "asc" ? 1 : -1;
      if (valA < valB) return direction === "asc" ? -1 : 1;

      return valA > valB ? - 1 : valA < valB ? 1 : 0 // Descending
    });
  };

  const handleSortChange = (e) => setSortBy(e.target.value);

  const updateFavourite = (adId, newValue = 1) => {
    fetch("/api/fav_exc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ad_id: adId, operation: "favourite", value: newValue}),
    }).then(() => {
      // Update local state for immediate feedback
      setAds((prevAds) =>
        prevAds.map((ad) =>
          ad["Ad ID"] === adId ? { ...ad, Favourited: newValue } : ad 
        )
      );      
    });
  };

  const updateExclude = (adId) => {
    fetch("/api/fav_exc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ad_id: adId, operation: "exclude", value: 1}),
    });
  };

  const filteredAds = ads.filter(ad => ad.Excluded !== 1); // Don't show excluded ads

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-start py-10 space-y-6">
      <div className="text-sm">
        <label className="mr-2 font-medium text-gray-700">Sort by:</label>
        <select
          value={sortBy}
          onChange={handleSortChange}
          className="px-3 py-1 border rounded shadow-sm text-gray-800 bg-white"
        >
          <option>Price</option>
          <option>Mileage</option>
          <option>Registered Year</option>
          <option>Distance</option>
          <option>Ad post date</option>
          <option>Scraped at</option>
        </select>

        <button
          onClick = {() => setSortDirection((d) => (d === "asc" ? "desc" : "asc"))}
          className="ml-4 px-3 py-1 border rounded text-sm bg-white shadow-sm"
        >
          {sortDirection === "asc" ? "⬆ Ascending" : "⬇ Descending"}
        </button>
      </div>

      {ads.length > 0 ? (
        <CardViewer
          ads={filteredAds}
          updateFavourite={updateFavourite}
          updateExclude={updateExclude}
        />
      ) : (
        <p>Loading ads...</p>
      )}
    </div>
  );
}

export default App;
