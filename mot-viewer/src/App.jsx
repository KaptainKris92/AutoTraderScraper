import React, { useState, useEffect } from "react";
import CardViewer from "./components/CardViewer";

function App() {  

  const [ads, setAds] = useState([]);

  useEffect(() => {
    fetch("api/ads")
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched ads:", data);
        setAds(data);
      })
      .catch((err) => console.error("Failed to load ads:", err));
  }, []);

  const updateFavourite = (adId) => {
    fetch("/api/fav_exc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ad_id: adId, operation: "favourite", value: 1}),
    });
  };

  const updateExclude = (adId) => {
    fetch("/api/fav_exc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ad_id: adId, operation: "exclude", value: 1}),
    });
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      {ads.length > 0 ? (
        <CardViewer
          ads={ads}
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
