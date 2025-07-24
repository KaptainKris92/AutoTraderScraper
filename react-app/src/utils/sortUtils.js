export const sortKeyMap = {
    "Title": (ad) => ad.Title || "",
    "Price": (ad) => parseInt(ad.Price?.replace(/[^0-9]/g, "")) || 0,
    "Mileage": (ad) => ad.Mileage || 0,
    "Registered Year": (ad) => {
        const yearMatch = ad["Registered Year"]?.match(/\d{4}/);
        return yearMatch ? parseInt(yearMatch[0]) : 0;
    },
    "Distance": (ad) => ad["Distance (miles)"] || 0,
    "Ad post date": (ad) => new Date(ad["Ad post date"]),
    "Scraped at": (ad) => new Date(ad["Scraped at"]),
};

export const sortOptions = Object.keys(sortKeyMap);

export function sortAds(adsArray, key, direction = "asc") {
    const getVal = sortKeyMap[key];
    if (!getVal) return adsArray; // fallback

    return [...adsArray].sort((a, b) => {
        const valA = getVal(a);
        const valB = getVal(b);

        if (valA > valB) return direction === "asc" ? 1 : -1;
        if (valA < valB) return direction === "asc" ? -1 : 1;
        return 0;
    });
}
