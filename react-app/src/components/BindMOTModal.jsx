import { useEffect, useState } from "react";

export default function BindMOTModal({ adId, onClose, onBindSuccess }) {
    const [unboundHistories, setUnboundHistories] = useState([]);

    useEffect(() => {
        fetch("/api/mot_history")
        .then((res) => res.json())
        .then((data) =>
            setUnboundHistories(data.filter((h) => !h.ad_id)) // Only show unbound MOT histories
        )        
        .catch((err) => console.error("Failed to load MOT histories:", err));
    }, []);

    const handleBind = async (registration) => {
        await fetch("/api/mot_history/bind", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ registration, ad_id: adId }),
        });

        alert(`Bound ${registration} to this ad.`);

        // Notify parent (AdCard)
        if (onBindSuccess) {
            onBindSuccess(registration);
        }

        onClose(); // close modal after binding
    };

    return (
        <div className="fixed inset-0 bg-white z-50 flex flex-col p-4 space-y-4 overflow-y-auto">
        <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">Bind MOT History</h2>
            <button onClick={onClose} className="text-gray-600 hover:text-black text-xl">×</button>
        </div>

        <ul className="space-y-2">
            {unboundHistories.length === 0 && <p className="text-sm text-gray-500">No unbound MOT histories found.</p>}

            {unboundHistories.map((entry) => (
            
            // Each row
            <li key={entry.registration} className="border p-3 rounded flex justify-between items-center">
                {/* Left row info */}
                <div>
                    {/* Reg number */}
                    <div className="font-mono">{entry.registration}</div> 
                    {/* Make and model */}
                    <div className="text-xs text-gray-500">{entry.data?.make} {entry.data?.model}</div>
                </div>
                                
                {/* Bind button */}
                <button
                onClick={() => handleBind(entry.registration)}
                className="text-sm text-blue-600 hover:underline"
                >
                Bind to this ad
                </button>

            </li>
            ))}
        </ul>

        <button onClick={onClose} className="mt-4 text-sm text-gray-600 hover:text-black underline">
            Close
        </button>
        </div>
    );
}
