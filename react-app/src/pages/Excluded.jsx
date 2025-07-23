// src/pages/Excluded.jsx
import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export default function Excluded() {
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
            const onlyExcluded = data.filter((ad) => ad.Excluded === 1);
            const sorted = sortAds(onlyExcluded, sortBy, sortDirection);
            setAds(sorted);
        })
        .catch((err) => console.error("Failed to load excluded ads:", err));
    }, [sortBy, sortDirection]);

    const sortAds = (adsArray, key, direction) => {
        const keyMap = {
        "Title": (ad) => ad.Title || "",
        "Price": (ad) => parseInt(ad.Price.replace(/[^0-9]/g, "")) || 0,
        "Mileage": (ad) => ad.Mileage || 0,
        "Registered Year": (ad) => {
            const yearMatch = ad["Registered Year"]?.match(/\d{4}/);
            return yearMatch ? parseInt(yearMatch[0]) : 0;
        },
        "Distance": (ad) => ad["Distance (miles)"] || 0,
        "Ad post date": (ad) => new Date(ad["Ad post date"]),
        "Scraped at": (ad) => new Date(ad["Scraped at"]),
        };

        return [...adsArray].sort((a, b) => {
        const valA = keyMap[key](a);
        const valB = keyMap[key](b);
        if (valA > valB) return direction === "asc" ? 1 : -1;
        if (valA < valB) return direction === "asc" ? -1 : 1;
        return 0;
        });
    };

    const handleSortChange = (e) => {
        const newSortBy = e.target.value;
        setSortBy(newSortBy);
        setSearchParams({ sortBy: newSortBy, direction: sortDirection });
    };

    const toggleSortDirection = () => {
        const newDirection = sortDirection === "asc" ? "desc" : "asc";
        setSortDirection(newDirection);
        setSearchParams({ sortBy, direction: newDirection });
    };

    const handleUnexclude = (adId) => {
        fetch("/api/fav_exc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_id: adId, operation: "exclude", value: 0 }),
        }).then(() => {
        setAds((prev) => prev.filter((ad) => ad["Ad ID"] !== adId));
        });
    };

    return (
        <div className="min-h-screen bg-gray-100 px-4 py-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Excluded Cars</h2>

        <div className="text-sm mb-4 text-center">
            <label className="mr-2 font-medium text-gray-700">Sort by:</label>
            <select
            value={sortBy}
            onChange={handleSortChange}
            className="px-3 py-1 border rounded shadow-sm text-gray-800 bg-white"
            >
            <option>Title</option>
            <option>Price</option>
            <option>Mileage</option>
            <option>Registered Year</option>
            <option>Distance</option>
            <option>Ad post date</option>
            <option>Scraped at</option>
            </select>
            <button
            onClick={toggleSortDirection}
            className="ml-4 px-3 py-1 border rounded text-sm bg-white shadow-sm"
            >
            {sortDirection === "asc" ? "⬆ Ascending" : "⬇ Descending"}
            </button>
        </div>

        {ads.length === 0 ? (
            <p className="text-center text-gray-600">No excluded ads.</p>
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
                    <strong>Year:</strong> {ad["Registered Year"]} | <strong>Distance:</strong>{" "}
                    {ad["Distance (miles)"]} mi | <strong>Location:</strong> {ad.Location} |{" "}
                    <strong>Posted:</strong> {ad["Ad post date"]}
                    </p>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-4 space-y-2">
                    <button
                    onClick={() => handleUnexclude(ad["Ad ID"])}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                    Unexclude
                    </button>
                </div>
                </li>
            ))}
            </ul>
        )}
        </div>
    );
}
