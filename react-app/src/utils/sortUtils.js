export const sortKeyMap = {
    "Title": (ad) => ad.title || "",
    "Price": (ad) => parseInt(ad.price?.replace(/[^0-9]/g, "")) || 0,
    "Mileage": (ad) => ad.mileage || 0,
    "Registered Year": (ad) => {
        const yearMatch = ad.reg_year?.match(/\d{4}/);
        return yearMatch ? parseInt(yearMatch[0]) : 0;
    },
    "Distance": (ad) => ad.distance || 0,
    "Ad post date": (ad) => new Date(ad.post_date),
    "Scraped at": (ad) => new Date(ad.scrape_date),
};

export const sortOptions = Object.keys(sortKeyMap);

export function sortAds(adsArray, key, direction = "asc") {
    if (!Array.isArray(adsArray)) {
        console.error("❌ sortAds expected array but got:", adsArray);
        return [];
    }

    const getVal = sortKeyMap[key];
    if (!getVal) return adsArray;

    return [...adsArray].sort((a, b) => {
        const valA = getVal(a);
        const valB = getVal(b);

        if (valA > valB) return direction === "asc" ? 1 : -1;
        if (valA < valB) return direction === "asc" ? -1 : 1;
        return 0;
    });
}

