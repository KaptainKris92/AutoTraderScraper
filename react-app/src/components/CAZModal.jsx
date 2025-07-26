// CAZModal.jsx
import { FaTimes } from "react-icons/fa";

export default function CAZModal({ onClose, registration, results }) {
    return (
        <div className="fixed inset-0 bg-white z-50 flex flex-col p-4 space-y-4 overflow-y-auto modal-open">
        {/* Header */}
        <div className="flex justify-between items-center border-b pb-2 mb-2">
            <h2 className="text-xl font-semibold">
            CAZ Status for <span className="text-blue-700">{registration}</span>
            </h2>
            <button onClick={onClose} className="text-gray-600 hover:text-black text-xl">
            <FaTimes />
            </button>
        </div>

        {/* Table */}
        {results && results.length > 0 ? (
            <table className="table-auto w-full text-sm border border-gray-300">
            <thead>
                <tr className="bg-gray-100">
                <th className="border px-2 py-1 text-left">Zone</th>
                <th className="border px-2 py-1 text-left">Daily Charge</th>
                </tr>
            </thead>
            <tbody>
                {results.map((zone, idx) => (
                <tr
                    key={idx}
                    className={
                    zone["Daily Charge"] !== "No Charge" ? "bg-red-100" : ""
                    }
                >
                    <td className="border px-2 py-1">{zone.Zone}</td>
                    <td className="border px-2 py-1">{zone["Daily Charge"]}</td>
                </tr>
                ))}
            </tbody>
            </table>
        ) : (
            <p className="text-gray-700 italic">No CAZ data available.</p>
        )}
        </div>
    );
}
