import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { sortAds } from "../utils/sortUtils";
import SortControls from "../components/SortControls";

export default function Favourites() {
    const [ads, setAds] = useState([]);
    const [searchParams, setSearchParams] = useSearchParams();

    const defaultSortBy = searchParams.get("sortBy") || "Price";
    const defaultDirection = searchParams.get("direction") || "asc";
    const [sortBy, setSortBy] = useState(defaultSortBy);
    const [sortDirection, setSortDirection] = useState(defaultDirection);

    useEffect(() => {
        fetch("/api/ads")
        .then((res) => res.json())
        .then((data) => {
            const onlyFaves = data.filter((ad) => ad.Favourited === 1 && ad.Excluded !== 1);
            const sorted = sortAds(onlyFaves, sortBy, sortDirection);
            setAds(sorted);
        })
        .catch((err) => console.error("Failed to load favourites:", err));
    }, [sortBy, sortDirection]);

    const handleUnfavourite = (adId) => {
        fetch("/api/fav_exc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_id: adId, operation: "favourite", value: 0 }),
        }).then(() => {
        setAds((prev) => prev.filter((ad) => ad["Ad ID"] !== adId));
        });
    };

    const handleRemoveAndExclude = (adId) => {
        fetch("/api/fav_exc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_id: adId, operation: "favourite", value: 0 }),
        }).then(() => {
        fetch("/api/fav_exc", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ad_id: adId, operation: "exclude", value: 1 }),
        }).then(() => {
            setAds((prev) => prev.filter((ad) => ad["Ad ID"] !== adId));
        });
        });
    };

    return (
        <div className="min-h-screen bg-gray-100 px-4 py-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Favourited Cars</h2>

        <SortControls
            sortBy={sortBy}
            sortDirection={sortDirection}
            setSortBy={setSortBy}
            setSortDirection={setSortDirection}
            setSearchParams={setSearchParams}
        />

        {ads.length === 0 ? (
            <p className="text-center text-gray-600">No favourites yet.</p>
        ) : (
            <ul className="space-y-4 max-w-4xl mx-auto">
            {ads.map((ad) => (
                <li
                key={ad["Ad ID"]}
                className="bg-white p-4 rounded shadow flex flex-col sm:flex-row sm:items-center justify-between"
                >
                <div>
                    <h3 className="font-bold text-lg">{ad.Title}</h3>
                    <p className="text-sm text-gray-600">{ad.Subtitle}</p>
                    <p className="text-sm mt-1">
                    <strong>Price:</strong> {ad.Price} | <strong>Mileage:</strong> {ad.Mileage} |{" "}
                    <strong>Year:</strong> {ad["Registered Year"]} | <strong>Distance:</strong> {ad["Distance (miles)"]} mi
                    | <strong>Location:</strong> {ad.Location} | <strong>Posted:</strong> {ad["Ad post date"]}
                    </p>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-4 space-y-2">
                    <button
                    onClick={() => handleUnfavourite(ad["Ad ID"])}
                    className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    >
                    Remove
                    </button>
                    <button
                    onClick={() => handleRemoveAndExclude(ad["Ad ID"])}
                    className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                    Remove & Exclude
                    </button>
                </div>
                </li>
            ))}
            </ul>
        )}
        </div>
    );
}
