import { useEffect, useState } from "react";
import { FaTimes, FaTrash, FaLink } from "react-icons/fa";

// Gets the registration year from the registration number
function parseRegYear(reg) {
  // Expect format: two letters then two digits
    const match = reg.match(/^[A-Z]{2}(\d{2})/);
    if (!match) return null;
    const num = parseInt(match[1], 10);
    let year = num;
    const current = new Date().getFullYear();
    // If number >50, subtract 50 and treat as sept to feb
    if (num > 50) year = num - 50;
    // Heuristic for century: if year > current‑2000, it's likely 2000‑
    year += 2000;
    return year;
}

export default function MOTHistoryModal({ onClose, adId, initialReg }) {
    const [regInput, setRegInput] = useState("");
    const [motHistories, setMotHistories] = useState([]);        
    const [regInputFilter, setRegInputFilter] = useState("");           

    const [activeRegistration, setActiveRegistration] = useState(null);
    const activeHistory = motHistories.find(h => h.registration === activeRegistration);

    const showRegSelector = !initialReg; // Hide reg selector if history loaded from AdCard
    

    // Filter options: 'all', 'bound', 'unbound'
    const [filter, setFilter] = useState('all');
    const [sort, setSort] = useState('alpha'); // or 'year'

    const filtered = motHistories.filter(h => {
        if (filter === 'bound') return h.ad_id !== null;
        if (filter === 'unbound') return h.ad_id === null;
        return true;
    });

    const sorted = [...filtered].sort((a, b) => {
    if (sort === 'year') {
        const ya = parseRegYear(a.registration) || 0;
        const yb = parseRegYear(b.registration) || 0;
        return ya - yb;
    } else {
        return a.registration.localeCompare(b.registration);
    }
    });

    // Load all MOT histories
    useEffect(() => {
        fetch("/api/mot_history")
        .then((res) => res.json())
        .then((data) =>{
            setMotHistories(data);
            if (initialReg) setActiveRegistration (initialReg);
        })        
        .catch((err) => console.error("Failed to load MOT histories:", err));
    }, [adId]);

    const handleSearchMOT = async () => {
        try {
            const res = await fetch(`/api/mot_history/query?reg=${encodeURIComponent(regInput)}`);
            const data = await res.json();
            if (!data || data.error) throw new Error(data.error || "Invalid response");

            // Save to DB
            await fetch("/api/mot_history", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ registration: regInput.replace(/\s+/g, "").toUpperCase(), data, ad_id: null }),
            });

            // Refresh
            const updated = await fetch("/api/mot_history").then((r) => r.json());
            setMotHistories(updated);
            setActiveRegistration(regInput.toUpperCase());  // ✅ New line here
            setRegInput("");
        } catch (err) {
        console.error("❌ MOT search failed:", err);
        alert("Failed to retrieve MOT history. Please check the registration number.");
        }
    };

    const handleDelete = async (registration) => {
        await fetch(`/api/mot_history/${registration}`, { method: "DELETE" });
        setMotHistories((prev) => prev.filter((h) => h.registration !== registration));
        setActiveIndex(0);
    };

    const handleUnbind = async () => {
        await fetch(`/api/mot_history/bind`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ registration: activeHistory.registration, ad_id: "" }),
        });
        alert("Unbound from ad.");

        // Optimistically update state
        setMotHistories((prev) =>
            prev.map((entry) =>
                entry.registration === activeHistory.registration
                    ? { ...entry, ad_id: null }
                    : entry
                )
            );
    }

    return (
        <div className="fixed inset-0 bg-white z-50 flex flex-col p-4 space-y-4 overflow-y-auto">
        
        {/* Header & X */}
        <div className="flex justify-between items-center mb-2">            
            <h2 className="text-xl font-semibold">MOT History</h2>
            
            {/* Close Button */}
            <button onClick={onClose} className="text-gray-600 hover:text-black text-xl">
                <FaTimes />
            </button>
            </div>

            {/* Reg Input & Query */}
            {showRegSelector && (
                <div className="flex flex-col sm:flex-row gap-3 items-center">
                    {/* Input field */}
                    <input
                        type="text"
                        placeholder="Enter Reg (e.g. AA51AAA)"
                        value={regInput}
                        onChange={(e) => setRegInput(e.target.value.toUpperCase())}
                        className="border rounded p-2 w-full sm:w-64 text-center uppercase"
                    />

                    {/* Button to query MOT API */}
                    <button
                        onClick={handleSearchMOT}
                        className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded disabled:bg-gray-400"
                        disabled={!regInput}
                    >
                        Get MOT History
                    </button>
                </div>
            )}

            {/* Saved MOT History */}
            <div className="mt-4 w-full">
                <h3 className="font-semibold text-gray-700 mb-2">Saved MOT History</h3>

                {/* Sorting options & Reg Selector */}
                {showRegSelector && (
                    <>
                        {/* Sorting options */}
                        <div className="flex flex-wrap gap-4 mb-4 items-center">
                            {/* Filter by 'All', 'Bound' or 'Unbound' */}
                            <div className="flex flex-col">
                                <label className="text-sm font-medium text-gray-600 mb-1">Filter</label>
                                <select
                                    value={filter}
                                    onChange={(e) => setFilter(e.target.value)}
                                    className="border rounded p-2 text-sm"
                                >
                                    <option value="all">All</option>
                                    <option value="bound">Bound</option>
                                    <option value="unbound">Unbound</option>
                                </select>
                            </div>

                            {/* Sort alphabetically or by registration year */}
                            <div className="flex flex-col">
                                <label className="text-sm font-medium text-gray-600 mb-1">Sort</label>
                                <select
                                    value={sort}
                                    onChange={(e) => setSort(e.target.value)}
                                    className="border rounded p-2 text-sm"
                                >
                                    <option value="alpha">Sort A–Z</option>
                                    <option value="year">Sort by Year</option>
                                </select>
                            </div>

                            {/* Filter manually */}
                            <div className="flex flex-col flex-grow">
                                <label className="text-sm font-medium text-gray-600 mb-1">Search</label>
                                <input
                                    type="text"
                                    placeholder="Filter..."
                                    value={regInputFilter}
                                    onChange={(e) => setRegInputFilter(e.target.value.toUpperCase())}
                                    className="border rounded p-2 text-sm uppercase w-full"
                                />
                            </div>
                        </div>

                        {/* Reg Selector */}
                        <div className="overflow-x-auto whitespace-nowrap gap-2 mb-4 flex">
                            {sorted
                                .filter((entry) => entry.registration.includes(regInputFilter))
                                .map((entry, idx) => (
                                    // Button
                                    <button
                                        key={entry.registration}
                                        onClick={() => setActiveRegistration(entry.registration)}
                                        className={`px-3 py-1 rounded text-sm border ${
                                            entry.registration === activeRegistration
                                                ? "bg-blue-600 text-white border-blue-600"
                                                : "bg-gray-100 text-gray-800 border-gray-300"
                                        }`}
                                    >
                                        {entry.registration}
                                    </button>
                                ))}
                        </div>
                    </>
                )}

                {/* MOT history */}
                {activeHistory && (
                    <>
                        {/* Car info div */}
                        <div className="text-sm text-gray-600 mb-2">
                            {/* Make and model */}
                            <span className="font-bold text-black" style={{ fontSize: "14px" }}>
                                {activeHistory.data.make} {activeHistory.data.model}
                            </span>
                            {!showRegSelector && (
                                <span className="ml-2 text-gray-700" style={{ fontSize: "14px" }}>
                                    ({activeHistory.registration})
                                </span>
                            )}

                            {/* Delete button */}
                            <div className="mt-1 flex gap-2">
                                <button
                                    onClick={() => handleDelete(activeHistory.registration)}
                                    className="text-xs text-red-600 hover:underline flex items-center gap-1"
                                >
                                    <FaTrash /> Delete
                                </button>
                            </div>
                        </div>

                        {/* Unbind button */}
                        {activeHistory.ad_id && activeHistory.ad_id !== "" && (
                            <button
                                onClick={handleUnbind}
                                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                            >
                                <FaLink /> Unbind
                            </button>
                        )}

                {/* All MOT tests */}
                <div className="space-y-4">
                {activeHistory.data.motTests?.map((test, i) => (
                    <div key={i} className="p-4 border rounded bg-gray-50 space-y-2">
                    <div className="flex justify-between">
                        
                        {/* Pass/Fail */}
                        <span
                        className={`font-semibold ${
                            test.testResult === "FAILED" ? "text-red-700" : "text-green-700"
                        }`}
                        >
                        {test.testResult}
                        </span>
                        
                        {/* Test date */}
                        <span className="text-sm text-gray-600">
                        {new Date(test.completedDate).toLocaleDateString()}
                        </span>
                    </div>

                    {/* Mileage */}
                    <div className="text-sm text-gray-700 font-semibold">
                        Mileage: {Number(test.odometerValue).toLocaleString()}
                    </div>
                    
                    {/* List of advisories/defects */}
                    {test.defects?.length > 0 && (
                    <div className="space-y-2 text-sm">

                        {/* Failures (non-ADVISORY, non-PRS) */}
                        {test.defects.some(d => d.type !== "ADVISORY") && (
                        <div className="text-red-700">
                            <div className="font-semibold mb-1">Failures</div>
                            <ul className="list-disc list-inside ml-4">
                            {test.defects
                                .filter(d => d.type !== "ADVISORY")
                                .map((d, idx) => (
                                <li key={idx}>
                                    <span className="font-medium text-red-800">{d.type}</span>: {d.text}
                                    {d.dangerous && (
                                    <span className="ml-1 text-xs font-semibold bg-red-200 text-red-800 px-1 rounded">
                                        Dangerous
                                    </span>
                                    )}
                                </li>
                                ))}
                            </ul>
                        </div>
                        )}

                        {/* Advisories */}
                        {test.defects.some(d => d.type === "ADVISORY") && (
                        <div className="text-yellow-700">
                            <div className="font-semibold mb-1">Advisories</div>
                            <ul className="list-disc list-inside ml-4">
                            {test.defects
                                .filter(d => d.type === "ADVISORY")
                                .map((d, idx) => (
                                <li key={idx}>
                                    {d.text}
                                </li>
                                ))}
                            </ul>
                        </div>
                        )}
                    </div>
                    )}
                    </div>
                ))}
                </div>
            </>
            )}
        </div>
        </div>
    );
}
