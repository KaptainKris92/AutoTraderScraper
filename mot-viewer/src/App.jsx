import React, { useState, useEffect } from 'react';
import CarCard from './components/CarCard';

const mockAds = [
  {
    adId: "e46b69ca14",
    title: "Reliant Scimitar",
    subtitle: "3.0 GTE 2dr",
    price: 5995,
    mileage: 76324,
    registeredYear: "1980 (W reg)",
    distance: 43,
    location: "Sheffield",
    adUrl: "https://www.autotrader.co.uk/car-details/202507054201480",
    possiblePlates: ["BTP 580W", "BTP 58OW"],
    vehicle: {
      registration: "FL09OWE",
      make: "AUDI",
      model: "A6",
      firstUsedDate: "2009-03-18",
      fuelType: "Diesel",
      primaryColour: "Black",
      engineSize: "2969",
      hasOutstandingRecall: "No",
      motTests: [
        {
          motTestNumber: "349708478165",
          completedDate: "2025-07-16T12:32:44.000Z",
          expiryDate: "2026-07-15",
          odometerValue: "105416",
          odometerUnit: "MI",
          testResult: "PASSED",
          defects: []
        },
        {
          motTestNumber: "968070582461",
          completedDate: "2024-06-11T10:24:15.000Z",
          expiryDate: null,
          odometerValue: "101986",
          odometerUnit: "MI",
          testResult: "FAILED",
          defects: [
            {
              dangerous: true,
              text: "Nearside Rear Inner Brake pad(s) less than 1.5 mm thick (1.1.13 (a) (ii))",
              type: "DANGEROUS"
            }
          ]
        }
      ]
    }
  },
  {
    adId: "fadc987e24",
    title: "BMW E30 Touring",
    subtitle: "318i Manual",
    price: 12995,
    mileage: 124122,
    registeredYear: "1990 (G reg)",
    distance: 12,
    location: "Leeds",
    adUrl: "https://www.autotrader.co.uk/car-details/202507211235",
    possiblePlates: ["G123 ABC", "G123 ABE"],
    vehicle: {
      registration: "G123ABC",
      make: "BMW",
      model: "318i",
      firstUsedDate: "1990-01-14",
      fuelType: "Petrol",
      primaryColour: "Red",
      engineSize: "1796",
      hasOutstandingRecall: "No",
      motTests: [
        {
          motTestNumber: "112233445566",
          completedDate: "2024-05-12T10:12:00.000Z",
          expiryDate: "2025-05-11",
          odometerValue: "124122",
          odometerUnit: "MI",
          testResult: "PASSED",
          defects: []
        }
      ]
    }
  }
];

const fetchMOTDataForPlate = async (plate) => {
  const match = mockAds.find(ad => ad.vehicle.registration === plate.replace(/\s/g, ''));
  return match ? match.vehicle : null;
};

export default function App() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [motHistories, setMotHistories] = useState([]);

  const selectedAd = mockAds[currentIndex];

  useEffect(() => {
    const fetchAll = async () => {
      const all = await Promise.all(
        selectedAd.possiblePlates.map(p => fetchMOTDataForPlate(p))
      );
      setMotHistories(all.filter(Boolean));
    };
    fetchAll();
  }, [selectedAd]);

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? mockAds.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === mockAds.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-3xl font-bold mb-6 text-center">AutoTrader MOT Explorer</h1>

      <div className="flex justify-between items-center mb-4">
        <button
          onClick={handlePrev}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded disabled:opacity-30"
        >
          ←
        </button>

        <div className="flex-1 px-4">
          <CarCard ad={selectedAd} motHistories={motHistories} />
        </div>

        <button
          onClick={handleNext}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded disabled:opacity-30"
        >
          →
        </button>
      </div>
    </div>
  );
}