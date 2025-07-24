import { useState } from "react";
import { FaTimes } from "react-icons/fa";

export default function MOTHistoryModal({ onClose, adId }) {
    const [regInput, setRegInput] = useState("");
    const [activeIndex, setActiveIndex] = useState(0);

    // POPULATE THIS WITH REAL DATA LATER
    const fakeMOTHistories = [
        {
            registration: "AA51AAA",
            make: "Ford",
            model: "Focus",
            motTests: [
            {
                completedDate: "2023-06-12T10:12:00Z",
                testResult: "PASSED",
                expiryDate: "2024-06-12",
                odometerValue: "42000",
                odometerUnit: "MI",
                motTestNumber: "TST123456",
                dataSource: "DVSA",
                defects: [
                {
                    text: "Nearside front tyre close to legal limit",
                    type: "ADVISORY",
                    dangerous: false,
                },
                ],
            },
            {
                completedDate: "2022-06-10T09:00:00Z",
                testResult: "FAILED",
                odometerValue: "39000",
                odometerUnit: "MI",
                motTestNumber: "TST654321",
                dataSource: "DVSA",
                defects: [
                {
                    text: "Brake pads below service limit",
                    type: "MAJOR",
                    dangerous: true,
                },
                ],
            },
            ],
        },
        {
            registration: "AB12XYZ",
            make: "Toyota",
            model: "Yaris",
            motTests: [
            {
                completedDate: "2024-01-10T08:15:00Z",
                testResult: "PASSED",
                expiryDate: "2025-01-10",
                odometerValue: "25000",
                odometerUnit: "MI",
                motTestNumber: "TST987654",
                dataSource: "DVSA",
                defects: [],
            },
            ],
        },
        {
            registration: "XY99FFF",
            make: "Volkswagen",
            model: "Golf",
            motTests: [
            {
                completedDate: "2023-09-01T14:30:00Z",
                testResult: "FAILED",
                odometerValue: "71500",
                odometerUnit: "MI",
                motTestNumber: "TST111222",
                dataSource: "DVSA",
                defects: [
                {
                    text: "Windscreen wiper does not clear windscreen effectively",
                    type: "MINOR",
                    dangerous: false,
                },
                {
                    text: "Rear brake lights not working",
                    type: "MAJOR",
                    dangerous: true,
                },
                ],
            },
            ],
        },
    ];

    const activeHistory = fakeMOTHistories[activeIndex];

    return (
        <div className="fixed inset-0 bg-white z-50 flex flex-col p-4 space-y-4 overflow-y-auto">
        {/* Close Button */}
        <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">MOT History</h2>
            <button onClick={onClose} className="text-gray-600 hover:text-black text-xl">
            <FaTimes />
            </button>
        </div>

        {/* Reg Input & Search */}
        <div className="flex flex-col sm:flex-row gap-3 items-center">
            <input
            type="text"
            placeholder="Enter Reg (e.g. AA51AAA)"
            value={regInput}
            onChange={(e) => setRegInput(e.target.value.toUpperCase())}
            className="border rounded p-2 w-full sm:w-64 text-center uppercase"
            />

            <button
            onClick={() => console.log("Trigger EasyOCR")}
            className="text-sm px-3 py-2 border border-blue-500 text-blue-600 rounded hover:bg-blue-50"
            >
            Detect with EasyOCR
            </button>

            <button
            onClick={async() => {                
                console.log(encodeURIComponent(regInput))
                const res = await fetch (`/api/mot_history?reg=${encodeURIComponent(regInput)}`);
                const data = await res.json();
                console.log("MOT data:", data);
                // TODO: setMOTResults(data) to store/display data
                
            }}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded disabled:bg-gray-400"
            disabled={!regInput}
            >
            Search MOT
            </button>
        </div>

        {/* Saved MOT History List (placeholder) */}
        <div className="mt-4 w-full">
            <h3 className="font-semibold text-gray-700 mb-2">Saved MOT History</h3>

            {/* Tab Selector */}
            <div className="flex flex-wrap gap-2 mb-4">
            {fakeMOTHistories.map((entry, idx) => (
                <button
                key={idx}
                onClick={() => setActiveIndex(idx)}
                className={`px-3 py-1 rounded text-sm border ${
                    idx === activeIndex
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-gray-100 text-gray-800 border-gray-300"
                }`}
                >
                {entry.registration}
                </button>
            ))}
            </div>

            {/* Meta info */}
            <div className="text-sm text-gray-600 mb-1">
            {activeHistory.make} {activeHistory.model}
            </div>

            <div className="space-y-4">
            {activeHistory?.motTests.map((test, i) => (
                <div key={i} className="p-4 border rounded bg-gray-50 space-y-2">
                <div className="flex justify-between">
                    <span className="font-semibold text-green-700">{test.testResult}</span>
                    <span className="text-sm text-gray-600">
                    {new Date(test.completedDate).toLocaleDateString()}
                    </span>
                </div>
                <div className="text-sm text-gray-700">
                    Mileage: {test.odometerValue} {test.odometerUnit}
                </div>
                {test.defects?.length > 0 && (
                    <div className="text-sm text-red-600">
                    Issues:
                    <ul className="list-disc list-inside ml-4">
                        {test.defects.map((d, idx) => (
                        <li key={idx}>
                            <span className="font-medium">{d.type}</span>: {d.text}
                            {d.dangerous && <span className="ml-1 text-xs font-semibold bg-red-200 text-red-800 px-1 rounded">Dangerous</span>}
                        </li>
                        ))}
                    </ul>
                    </div>
                )}
                </div>
            ))}
            </div>


            {/* <div className="text-sm text-gray-500 italic">No MOT results yet...</div> */}
        </div>
        </div>
    );
}
