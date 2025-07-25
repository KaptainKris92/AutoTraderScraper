import { useState, useRef, useEffect } from "react";
import AdCard from "./AdCard";
import { FaHeart, FaTimes, FaCar } from "react-icons/fa";
import { useDrag } from '@use-gesture/react'; // For mobile swiping
import MOTHistoryModal from "./MOTHistoryModal";

export default function CardViewer({ ads, updateFavourite, updateExclude }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showMOTModal, setShowMOTModal] = useState(false);
  const [showFavouritesOnly, setShowFavouritesOnly] = useState(false);

  const filteredAds = showFavouritesOnly
    ? ads.filter(ad => ad.Favourited === 1)
    : ads;
  
  const currentAd = filteredAds.length > 0 ? filteredAds[currentIndex] : null;

  const next = () => {
    if (currentIndex < filteredAds.length - 1) setCurrentIndex((i) => i + 1);
  };

  const prev = () => {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1);
  };

  useEffect(() => {
    // Reset index if filter changes and currentIndex becomes invalid
    if (currentIndex >= filteredAds.length) {
      setCurrentIndex(0);
    }
  }, [showFavouritesOnly, ads])

  // Swipe triggers
  const bind = useDrag(
    ({ swipe: [swipeX, swipeY] }) => {
      const modalOpen = document.querySelector(".modal-open");
      if (modalOpen) return; // Don't swipe if a modal is open

      if (swipeX === -1) next(); // Left
      if (swipeX === 1) prev(); // Right       
    },
    { axis: undefined, swipe: { velocity: 0.2, distance: 30 }}
  );

  // Keyboard triggers
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Only listen if no modals are open
      const modalOpen = document.querySelector(".modal-open");
      if (modalOpen) return;

      if (!currentAd || !currentAd["Ad ID"]) return;
      const adId = currentAd["Ad ID"];      

      switch (e.key) {
        case "ArrowRight":
          next();
          break;
        case "ArrowLeft":
          prev();
          break;
        case "f":
        case "F":
          updateFavourite(adId, currentAd.Favourited === 1 ? 0 : 1);
          break;
        case "e":
        case "E":
          updateExclude(adId);
          break;
        case "Escape":
          setShowMOTModal(false);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentAd, updateFavourite, updateExclude]);

  const cardRef = useRef(null);

  if (!filteredAds || filteredAds.length === 0) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-gray-600">
      <div className="mb-4">No ads to display.</div>
      <button
        onClick={() => setShowFavouritesOnly(false)}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Show All Ads
      </button>
    </div>
  );
}

  // RETURN
  return (
    currentAd && (
      <div className="relative min-h-screen flex flex-col items-center justify-start pt-2 pb-14">          

        {/* Filter favourites toggle */}
        <div className="flex items-center mb-2 gap-2">
          <input
            type="checkbox"
            id="favOnlyToggle"
            checked={showFavouritesOnly}
            onChange={() => setShowFavouritesOnly(val => !val)}
            className="w-4 h-4"
          />
          <label htmlFor="favOnlyToggle" className="text-sm text-gray-700">Favourites only</label>
        </div>
        
        {/* Card & Arrows */}
        <div 
          {...bind()}
          ref={cardRef}
          className="relative flex items-center justify-center w-full max-w-2xl min-h-[540px] touch-none"
        >
          {/* Arrows */}
          <>
          <button
            onClick={prev}
            className="absolute left-[-2.5rem] text-3xl text-gray-500 hover:text-black transition hidden sm:block"
          >
            ◀
          </button>

          <button
            onClick={next}
            className="absolute right-[-2.5rem] text-3xl text-gray-500 hover:text-black transition hidden sm:block"
          >
            ▶
          </button>
          </>

          {/* Tap zones for mobile (left/right) */}      
          <div className="absolute top-0 left-0 h-full w-[15%] z-10 block sm:hidden" onClick={prev}></div>     
          <div className="absolute top-0 right-0 h-full w-[15%] z-10 block sm:hidden" onClick={next}></div>        
          <div><AdCard ad={currentAd} /></div>        
        </div>      

        {/* Bottom bar with favourite and exclude buttons */}
        <div className="mt-4 flex justify-center space-x-10">
          {/* Toggle favourite */}
          <button
            onClick={() => {
              const adId = currentAd["Ad ID"];
              const newFaveStatus = currentAd.Favourited === 1 ? 0 : 1;
              updateFavourite(adId, newFaveStatus);

              // Auto skip to next if in filtered mode and unfavourited
              if (showFavouritesOnly && newFaveStatus === 0) {
                setTimeout(() => {
                  const remaining = ads.filter((ad) => ad.Favourited === 1);
                  if (remaining.length > 0) {
                    setCurrentIndex((i) => Math.min(i, remaining.length - 1));
                  }
                }, 100);
              }
            }}
            className="text-5xl md:text-6xl text-pink-500 hover:scale-110 transition"
            title={currentAd.Favourited === 1 ? "Unfavourite" : "Favourite"}
          >
            {currentAd.Favourited === 1 ? <FaTimes /> : <FaHeart />}
          </button>

          {/* Exclude or disable */}
          {!showFavouritesOnly ? (
            <button
              onClick={() => updateExclude(currentAd["Ad ID"])}
              className="text-5xl md:text-6xl text-red-600 hover:scale-110 transition"
              title="Exclude"
            >
              <FaTimes />
            </button>
          ) : (
            <div className="text-sm text-gray-400 italic mt-2">Unfavourite to remove</div>
          )}
        </div>



      <button
        onClick={() => setShowMOTModal(true)}
        className="fixed bottom-4 right-4 z-50 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg"
        title="MOT History"
      >
        <FaCar className="text-xl" />
      </button>      

      {showMOTModal && (
        <MOTHistoryModal onClose={() => setShowMOTModal(false)} />
      )}

      </div>
    )
  );
}
