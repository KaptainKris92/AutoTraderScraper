import React, { useState } from "react";
import AdCard from "./AdCard";
import { FaHeart, FaTimes } from "react-icons/fa";

export default function CardViewer({ ads, updateFavourite, updateExclude }) {
  const [currentIndex, setCurrentIndex] = useState(0);

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

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative">
      {/* Card & Arrows */}
      <div className="relative flex items-center justify-center w-full max-w-2xl">
        <button
          onClick={prev}
          className="absolute left-[-4.0rem] text-3xl text-gray-500 hover:text-black transition"
        >
          ◀
        </button>

        <AdCard ad={currentAd} />

        <button
          onClick={next}
          className="absolute right-[-4.0rem] text-3xl text-gray-500 hover:text-black transition"
        >
          ▶
        </button>
      </div>

      {/* Bottom Bar */}
      <div className="fixed bottom-6 flex space-x-10 justify-center">
        <button
          onClick={() => currentAd["Ad ID"] && updateFavourite(currentAd["Ad ID"])}
          className="text-4xl text-pink-500 hover:scale-110 transition"
        >
          <FaHeart />
        </button>
        <button
          onClick={() => currentAd["Ad ID"] && updateExclude(currentAd["Ad ID"])}
          className="text-4xl text-red-600 hover:scale-110 transition"
        >
          <FaTimes />
        </button>
      </div>
    </div>
  );
}
