import { useState, useEffect } from "react";
import Slider from "rc-slider";
import "rc-slider/assets/index.css";
import Select from "react-select";
import ScrapeProgressModal from "../components/ScrapeProgressModal";

export default function Settings() {
  const [generatedUrl, setGeneratedUrl] = useState(""); // For debugging
  // Existing profiles
  const [profileName, setProfileName] = useState("");
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [profiles, setProfiles] = useState([]);

  // Modal state
  const [showScrapeModal, setShowScrapeModal] = useState(false);

  const generateUrl = async () => {
    const payload = {
      postcode: formData.postcode.replace(/\s+/g, "").toUpperCase(), // Remove whitespace from postcode
      radius: formData.radius,
      make: formData.make.join(","),
      min_price: priceSteps[formData.priceIndex[0]],
      max_price: priceSteps[formData.priceIndex[1]],
      min_mileage: mileageSteps[formData.mileageIndex[0]],
      max_mileage: mileageSteps[formData.mileageIndex[1]],
      gearbox: formData.transmission.join(","),
    };

    const res = await fetch("/api/generate-search-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (data.url) {
      setGeneratedUrl(data.url);
      return data.url;
    } else {
      console.error("Error:", data.error);
      setGeneratedUrl(data.error);
      return null;
    }
  };

  const saveProfile = async () => {
    const url = await generateUrl();
    if (!url) return;

    const payload = {
      name: profileName,
      params: {
        postcode: formData.postcode.replace(/\s/g, "").toUpperCase(),
        radius: formData.radius,
        make: formData.make.join(","),
        min_price: priceSteps[formData.priceIndex[0]],
        max_price: priceSteps[formData.priceIndex[1]],
        min_mileage: mileageSteps[formData.mileageIndex[0]],
        max_mileage: mileageSteps[formData.mileageIndex[1]],
        gearbox: formData.transmission.join(","),
      },
      generated_url: url,
    };

    const res = await fetch("/api/save-search-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (res.status == 409) {
      alert(`Profile already exists with name: ${data.name}`);
    } else if (res.ok) {
      alert("Saved profile: " + profileName);
    } else {
      alert("Something went wrong: " + data.error);
    }

    return data;
  };

  // Selection options
  const mileageSteps = [
    0, 100, 500, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000,
    50000, 60000, 70000, 80000, 90000, 100000, 125000, 150000, 200000,
  ];
  const priceSteps = [
    0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000,
    6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 11000, 12000, 13000, 14000,
    15000, 16000, 17000, 18000, 19000, 20000, 22500, 25000, 27500, 30000, 35000,
    40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000, 100000, 250000,
    500000, 1000000, 2000000,
  ];
  const radiusOptions = [
    "1",
    "5",
    "10",
    "15",
    "20",
    "25",
    "30",
    "35",
    "40",
    "45",
    "50",
    "55",
    "60",
    "70",
    "80",
    "90",
    "100",
    "200",
  ];
  const trasmissionOptions = ["Automatic", "Manual"]; // Not currently used
  const makeOptions = [
    "Abarth",
    "AC",
    "AK",
    "Alfa Romeo",
    "Allard",
    "Alpine",
    "Alvis",
    "Ariel",
    "Aston Martin",
    "Audi",
    "Austin",
    "BAC",
    "Beauford",
    "Bentley",
    "BMW",
    "Bramwith",
    "Bugatti",
    "BYD",
    "Cadillac",
    "Caterham",
    "Chesil",
    "Chevrolet",
    "Chrysler",
    "Citroen",
    "Corbin",
    "Corvette",
    "CUPRA",
    "Dacia",
    "Daewoo",
    "Daihatsu",
    "Daimler",
    "Datsun",
    "David Brown",
    "Dax",
    "Delorean",
    "Dodge",
    "DS AUTOMOBILES",
    "E-COBRA",
    "Ferrari",
    "Fiat",
    "Fisker",
    "Ford",
    "Gardner Douglas",
    "Genesis",
    "GMC",
    "Great Wall",
    "GWM",
    "Hillman",
    "Honda",
    "Hummer",
    "Hyundai",
    "INEOS",
    "Infiniti",
    "ISO",
    "Isuzu",
    "Iveco",
    "JAECOO",
    "Jaguar",
    "JBA",
    "Jeep",
    "Jensen",
    "KGM",
    "Kia",
    "Koenigsegg",
    "Lada",
    "Lagonda",
    "Lamborghini",
    "Lancia",
    "Land Rover",
    "LDV",
    "Leapmotor",
    "LEVC",
    "Lexus",
    "Leyland",
    "Lincoln",
    "Lister",
    "London Taxis International",
    "Lotus",
    "Ludis Currus",
    "Mahindra",
    "Maserati",
    "MAXUS",
    "Maybach",
    "Mazda",
    "McLaren",
    "Mercedes-Benz",
    "MEV",
    "MG",
    "Micro",
    "MINI",
    "Mitsubishi",
    "Mitsuoka",
    "MK",
    "MNR",
    "MOKE",
    "Morgan",
    "Morris",
    "Nardini",
    "NG",
    "Nissan",
    "Noble",
    "Omoda",
    "Opel",
    "Perodua",
    "Peugeot",
    "PGO",
    "Pilgrim",
    "Plymouth",
    "Polestar",
    "Pontiac",
    "Porsche",
    "Porsche Singer",
    "Proton",
    "Radical",
    "Rage",
    "Ram",
    "RBW",
    "RCR",
    "Reliant",
    "Renault",
    "Riley",
    "Robin Hood",
    "Rolls-Royce",
    "Rover",
    "Saab",
    "Santana",
    "SEAT",
    "Sebring",
    "Shelby",
    "Skoda",
    "Skywell",
    "Smart",
    "SsangYong",
    "Standard",
    "Subaru",
    "Sunbeam",
    "Suzuki",
    "Tesla",
    "Tiger",
    "Tornado",
    "Toyota",
    "Triumph",
    "TVR",
    "Ultima",
    "Vauxhall",
    "Volkswagen",
    "Volvo",
    "VRS",
    "Westfield",
    "Wolseley",
    "XPENG",
    "Zenos",
  ];
  const regYearOptions = [
    "new",
    "2025",
    "2024",
    "2023",
    "2022",
    "2021",
    "2020",
    "2019",
    "2018",
    "2017",
    "2016",
    "2015",
    "2014",
    "2013",
    "2012",
    "2011",
    "2010",
    "2009",
    "2008",
    "2007",
    "2006",
    "2005",
    "2004",
    "2003",
    "2002",
    "2001",
    "2000",
    "1995",
    "1990",
    "1980",
    "1970",
    "1960",
    "1950",
    "1940",
    "1930",
    "1920",
  ];
  const bodyTypeOptions = [
    "Convertible",
    "Coupe",
    "Estate",
    "Hatchback",
    "MPV",
    "Pickup",
    "Saloon",
    "SUV",
    "Camper",
    "Car Derived Van",
    "Combi Van",
    "Minibus",
  ];
  const colourOptions = [
    "Black",
    "Blue",
    "Grey",
    "White",
    "Silver",
    "Red",
    "Green",
    "Beige",
    "Bronze",
    "Brown",
    "Gold",
    "Multicolour",
    "Orange",
    "Pink",
    "Purple",
    "Yellow",
  ];
  const doorOptions = ["0", "1", "2", "3", "4", "5", "6"];
  const seatOptions = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "20",
    "59",
  ];
  const fuelTypeOptions = ["Petrol", "Diesel", "Electric", "Hybrid", "Bi Fuel"];
  const engineSizeOptions = [
    "0",
    "1.0",
    "1.2",
    "1.4",
    "1.6",
    "1.8",
    "1.9",
    "2.0",
    "2.2",
    "2.4",
    "2.6",
    "3.0",
    "3.5",
    "4.0",
    "4.5",
    "5.0",
    "5.5",
    "6.0",
    "6.5",
    "7.0",
  ];
  const enginePowerOptions = [
    "0",
    "50",
    "100",
    "150",
    "200",
    "250",
    "300",
    "350",
    "400",
    "450",
    "500",
    "550",
    "600",
    "650",
    "700",
    "750",
    "800",
    "850",
    "900",
    "950",
    "1000",
  ];
  const accelerationOptions = [
    "TO_4",
    "4_TO_6",
    "6_TO_8",
    "8_TO_10",
    "10_TO_12",
    "OVER_12",
  ];
  const fuelConsumptionOptions = ["OVER_30", "OVER_40", "OVER_50", "OVER_60"];
  const co2EmissionsOptions = [
    "TO_0",
    "TO_75",
    "TO_100",
    "TO_110",
    "TO_120",
    "TO_130",
    "TO_140",
    "TO_150",
    "TO_165",
    "TO_175",
    "TO_185",
    "TO_200",
    "TO_225",
    "TO_255",
    "OVER_255",
  ];
  const taxPerYearOptions = [
    "EQ_0",
    "TO_35",
    "TO_200",
    "TO_300",
    "TO_400",
    "OVER_400",
  ];
  const insuranceOptions = ["03U", "05U", "10U", "20U", "30U", "40U", "50U"];
  const driveTypeOptions = ["Four", "Front", "Rear"];
  const bootSpaceOptions = ["Small", "Medium", "Large"];
  const sellerTypeOptions = ["private", "trade"];
  const prevWriteOffOptions = ["Include", "Exclude", "Show only"];

  // Functions

  const [formData, setFormData] = useState({
    postcode: "",
    radius: 50,
    make: [],
    priceIndex: [0, priceSteps.length - 1],
    mileageIndex: [0, mileageSteps.length - 1],
    transmission: [],
  });

  const handleMakeChange = (selected) => {
    setFormData((prev) => ({ ...prev, make: selected.map((s) => s.value) }));
  };

  const handleTransmissionChange = (selected) => {
    setFormData((prev) => ({
      ...prev,
      transmission: selected.map((s) => s.value),
    }));
  };

  useEffect(() => {    
    const fetchProfiles = async () => {      
      const res = await fetch("/api/search-profiles");
      const data = await res.json();
      setProfiles(data.profiles);      
    };
    fetchProfiles();
  }, []); // The `[]` means it only runs once on intiial mount

  const handleSave = async () => {
    const payload = { ...formData, name: profileName, url: generatedUrl };
    await fetch("/api/save-search-profile", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
    });
    // fetchProfiles();
  };

  // Changes inputs to loaded profile when clicked
  const loadProfileIntoForm = async (id) => {
    try {
      const res = await fetch(`/api/search-profile/${id}`);
      const data = await res.json();

      if (res.ok && data.params) {
        setSelectedProfileId(id); // Highlight sidebar
        const p = data.params;

        setFormData({
          postcode: p.postcode || "",
          radius: p.radius || 50,
          make: (p.make || "").split(",").filter(Boolean),
          priceIndex: [
            priceSteps.indexOf(p.min_price),
            priceSteps.indexOf(p.max_price),            
          ],
          mileageIndex: [
            mileageSteps.indexOf(p.min_mileage),
            mileageSteps.indexOf(p.max_mileage),
          ],
          transmission: (p.gearbox || "").split(",").filter(Boolean),
        });

        setProfileName(data.name);
        setGeneratedUrl(data.url);
      }
    } catch (err) {
    console.error("Failed to load profile", err);
    }
  };  


  // Format `created_at` date
  function formatDate(dateStr) {
    if (!dateStr) return "Unknown date";
    const trimmed = dateStr.split(".")[0]; // Remove microseconds so JS can process it
    const date = new Date(trimmed);
    return isNaN(date.getTime()) ? "Unknown date" : date.toLocaleDateString("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  }

  return (
    <div className="flex">

      {/* Sidebar */}
      <div className="w-1/4 pr-4 border-r">
        <h2 className="font-bold mb-2">Saved Profiles</h2>

        {profiles.length === 0 && (        
          <p className="text-sm text-gray-400 italic">No profiles found</p>
        )}

        <ul className="space-y-2">
          {profiles.map((p) => (
            <li
              key={p.id}
              className={`p-2 border rounded cursor-pointer ${
                selectedProfileId === p.id
                  ? "bg-blue-100 border-blue-600"
                  : "bg-white"
              }`}
            >
              <div
                onClick={() => loadProfileIntoForm(p.id)}
                className="flex justify-between items-center"
              >
                <span className="font-medium">{p.name}</span>
                <span className="text-sm text-gray-500">
                  {formatDate(p.created_at)}
                </span>
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  className="text-sm bg-red-500 text-white px-2 py-1 rounded"
                  onClick={async () => {
                    await fetch(`/api/delete-search-profile/${p.id}`, {
                      method: "DELETE",
                    });
                    setProfiles((prev) => prev.filter((x) => x.id !== p.id));
                    if (selectedProfileId === p.id) setSelectedProfileId(null);
                  }}
                >
                  Delete
                </button>
                <button
                  className="text-sm bg-green-600 text-white px-2 py-1 rounded"
                  onClick={async () => {
                    const res = await fetch(`/api/run-scraper/${p.id}`, { method: "POST" });
                    const data = await res.json();

                    if (res.ok){
                      setSelectedProfileId(p.id); 
                      setShowScrapeModal(true);
                    } else {
                      alert("Failed to start scraping for " + p.name + " " + data.error);
                    }                    
                  }}
                >
                  Update Table
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Settings parameters */}
      <div className="flex-1 p-6">
        <form className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Profile Name */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Profile Name
              </label>
              <input
                type="text"
                className="border p-2 rounded w-full"
                placeholder="e.g. 'Low mileage BMWs'"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
              />
            </div>

            {/* Postcode */}
            <div>
              <label className="block text-sm font-medium mb-1">Postcode</label>
              <input
                type="text"
                name="postcode"
                maxLength={8}
                className="border rounded p-2 w-full"
                value={formData.postcode}
                onChange={(e) => {
                  const raw = e.target.value;
                  const noSpaces = raw.replace(/\s+/g, "");
                  const alphanumeric = noSpaces.replace(/[^a-zA-Z0-9]/g, "");
                  if (alphanumeric.length <= 7) {
                    setFormData({ ...formData, postcode: e.target.value });
                  }
                }}
              />
            </div>

            {/* Radius */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                Radius: {formData.radius} miles
              </label>
              <Slider
                min={0}
                max={radiusOptions.length - 1}
                step={1}
                value={radiusOptions.indexOf(formData.radius.toString())}
                marks={radiusOptions.reduce((acc, val, idx) => {
                  if (idx % 4 === 0) acc[idx] = val;
                  return acc;
                }, {})}
                onChange={(i) =>
                  setFormData({
                    ...formData,
                    radius: parseInt(radiusOptions[i]),
                  })
                }
              />
            </div>

            {/* Make */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Make</label>
              <Select
                isMulti
                options={makeOptions.map((m) => ({ label: m, value: m }))}
                onChange={handleMakeChange}
                value={formData.make.map((m) => ({ label: m, value: m }))}
              />
            </div>

            {/* Price */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                Price Range: £{priceSteps[formData.priceIndex[0]]} – £
                {priceSteps[formData.priceIndex[1]]}
              </label>
              <Slider
                range
                min={0}
                max={priceSteps.length - 1}
                step={1}
                value={formData.priceIndex}
                allowCross={false}
                onChange={(value) =>
                  setFormData({ ...formData, priceIndex: value })
                }
              />
            </div>

            {/* Mileage */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                Mileage Range: {mileageSteps[formData.mileageIndex[0]]} –{" "}
                {mileageSteps[formData.mileageIndex[1]]} mi
              </label>
              <Slider
                range
                min={0}
                max={mileageSteps.length - 1}
                step={1}
                value={formData.mileageIndex}
                allowCross={false}
                onChange={(value) =>
                  setFormData({ ...formData, mileageIndex: value })
                }
              />
            </div>

            {/* Transmission */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                Transmission
              </label>
              <Select
                isMulti
                options={trasmissionOptions.map((t) => ({ label: t, value: t }))}
                onChange={handleTransmissionChange}
                value={formData.transmission.map((t) => ({ label: t, value: t }))}
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-4 mt-4">
            <button
              type="button"
              className="bg-green-600 text-white px-4 py-2 rounded"
              onClick={async () => {
                const res = await saveProfile();
              }}
            >
              Save Search Profile
            </button>

          </div>

          {/* Debug + URL */}
          <div className="bg-gray-100 p-4 text-sm mt-6 rounded shadow-inner">
            <pre>{JSON.stringify(formData, null, 2)}</pre>
            {generatedUrl && (
              <div className="mt-2 text-blue-700">
                <strong>Generated URL:</strong>
                <br />
                <a
                  href={generatedUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline break-words"
                >
                  {generatedUrl}
                </a>
              </div>
            )}
          </div>

        </form>
      </div>

      {/* Progress modal */}
      {showScrapeModal && (
        <ScrapeProgressModal
          profileId={selectedProfileId}
          onClose={() => setShowScrapeModal(false)}
          />
      )}
    </div>
  );
}
