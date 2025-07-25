import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import CardViewer from "../components/CardViewer";
import { sortAds } from "../utils/sortUtils";
import SortControls from "../components/SortControls";

export default function Home() {  

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
            const adsArray = Array.isArray(data) ? data : data.data;
            console.log("Fetched ads array:", adsArray);
            const sorted = sortAds(adsArray, sortBy, sortDirection);
            setAds(sorted);
        })
        .catch((err) => console.error("Failed to load ads:", err));
    }, [sortBy, sortDirection]);

    // Prevent scrolling
    useEffect(() => {
        document.body.style.overflow = "hidden";
        return () => {
            document.body.style.overflow = "auto";  // Restore on unmount
        };
    }, []);

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
        }).then(() => {
            // Immediately remove excluded ad from state
            setTimeout(() => {
                setAds((prevAds) => prevAds.filter((ad) => ad["Ad ID"] !== adId));
            }, 200); // 200ms delay before removing the ad
            
        });
    };

    const filteredAds = ads.filter(ad => ad.Excluded !== 1); // Don't show excluded ads

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-start py-2 sm:pt-10 space-y-6">
        <SortControls
            sortBy={sortBy}
            sortDirection={sortDirection}
            setSortBy={setSortBy}
            setSortDirection={setSortDirection}
            setSearchParams={setSearchParams}
        />

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
