import React from 'react';

export default function CarCard({ ad }) {
  const imageDir = `/images/${ad.adId}`;
  const imageCount = 34; // Automate this later by counting number of images in the folder

  const images = Array.from({ length: imageCount }, (_, i) => {
    const padded = String(i + 1).padStart(2, '0');
    return `${imageDir}/${padded}.jpg`;
  });

  return (
    <div className="w-full max-w-5xl mx-auto bg-white rounded-xl shadow-lg p-6 space-y-4">
      <h2 className="text-2xl font-bold">{ad.title} — {ad.subtitle}</h2>

    <div className="overflow-x-auto flex space-x-2 w-full snap-x snap-mandatory scroll-smooth">
      {images.map((src, i) => (
        <img
          key={i}
          src={src}
          alt={`Car ${ad.title} ${i}`}
          className="w-72 h-48 object-cover rounded-lg snap-center shrink-0"
          loading="lazy"
        />
      ))}
    </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
        <p><strong>Price:</strong> £{ad.price.toLocaleString()}</p>
        <p><strong>Mileage:</strong> {ad.mileage.toLocaleString()} miles</p>
        <p><strong>Year:</strong> {ad.registeredYear}</p>
        <p><strong>Distance:</strong> {ad.distance} miles</p>
        <p><strong>Location:</strong> {ad.location}</p>
        <p><strong>Possible Plates:</strong> {ad.possiblePlates.join(', ')}</p>
      </div>

      <a
        href={ad.adUrl}
        className="text-blue-600 text-sm"
        target="_blank"
        rel="noreferrer"
      >
        View on AutoTrader ↗
      </a>
    </div>
  );
}
