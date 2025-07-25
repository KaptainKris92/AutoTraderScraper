import { useState, useRef} from "react";
import AdCard from "./AdCard";
import { FaHeart, FaTimes, FaCar } from "react-icons/fa";
import { useDrag } from '@use-gesture/react'; // For mobile swiping
import MOTHistoryModal from "./MOTHistoryModal";

export default function CardViewer({ ads, updateFavourite, updateExclude }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showMOTModal, setShowMOTModal] = useState(false);
  
  if (!ads || ads.length === 0) {
    return <p className="text-center mt-20 text-gray-600 text-lg">No ads available</p>;
  }

  const currentAd = ads[currentIndex] || {};

  const next = () => {
    if (currentIndex < ads.length - 1) setCurrentIndex((i) => i + 1);
  };

  const prev = () => {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1);
  };

  // Swipe triggers
  const bind = useDrag(
    ({ swipe: [swipeX, swipeY] }) => {
      if (swipeX === -1) next(); // Left
      if (swipeX === 1) prev(); // Right 
      // // Up
      // if (swipeY === -1 && currentAd["Ad ID"]) { 
      //   const newFaveStatus = currentAd.Favourited === 1 ? 0 : 1;
      //   updateFavourite(currentAd["Ad ID"], newFaveStatus)
      // }
      // if (swipeY === 1) updateExclude(currentAd["Ad ID"]); // Down
    },
    { axis: undefined, swipe: { velocity: 0.2, distance: 30 }}
  )

  const cardRef = useRef(null);

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-start pt-2 pb-14">          

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
        <button
          onClick={() => {
            const adId = currentAd["Ad ID"];
            if (adId) {
              const newFaveStatus = currentAd.Favourited === 1 ? 0 : 1;
              updateFavourite(adId, newFaveStatus);
            }
          }}
          className="text-5xl md:text-6xl text-pink-500 hover:scale-110 transition"
        >
          <FaHeart />
        </button>
        <button
          onClick={() => currentAd["Ad ID"] && updateExclude(currentAd["Ad ID"])}
          className="text-5xl md:text-6xl text-red-600 hover:scale-110 transition"
        >
          <FaTimes />
        </button>
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
  );
}
