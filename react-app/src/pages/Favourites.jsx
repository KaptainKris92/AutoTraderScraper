// src/pages/Favourites.jsx
import React, { useEffect, useState } from "react";

export default function Favourites() {
  const [favourites, setFavourites] = useState([]);

  useEffect(() => {
    fetch("/api/ads")
      .then((res) => res.json())
      .then((data) => {
        const onlyFaves = data.filter((ad) => ad.Favourited === 1);
        setFavourites(onlyFaves);
      })
      .catch((err) => console.error("Failed to load favourites:", err));
  }, []);

  const handleUnfavourite = (adId) => {
    fetch("/api/fav_exc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ad_id: adId, operation: "favourite", value: 0 }),
    }).then(() => {
      setFavourites((prev) => prev.filter((ad) => ad["Ad ID"] !== adId));
    });
  };

  return (
    <div className="min-h-screen overflow-y-auto bg-gray-100 px-4 py-8">
      <h2 className="text-2xl font-bold mb-6 text-center">Favourited Cars</h2>

      {favourites.length === 0 ? (
        <p className="text-center text-gray-600">No favourites yet.</p>
      ) : (
        <ul className="space-y-4 max-w-4xl mx-auto">
          {favourites.map((ad) => (
            <li
              key={ad["Ad ID"]}
              className="bg-white p-4 rounded shadow flex flex-col sm:flex-row sm:items-center justify-between"
            >
              <div>
                <h3 className="font-bold text-lg">{ad.Title}</h3>
                <p className="text-sm text-gray-600">{ad.Subtitle}</p>
                <p className="text-sm mt-1">
                  <strong>Price:</strong> {ad.Price} | <strong>Mileage:</strong> {ad.Mileage} |{" "}
                  <strong>Year:</strong> {ad["Registered Year"]}
                </p>
              </div>
              <button
                onClick={() => handleUnfavourite(ad["Ad ID"])}
                className="mt-3 sm:mt-0 sm:ml-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
