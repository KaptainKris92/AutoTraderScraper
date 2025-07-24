import { sortOptions } from "../utils/sortUtils";

export default function SortControls({ sortBy, sortDirection, setSortBy, setSortDirection, setSearchParams }) {
    const handleSortChange = (e) => {
        const newSortBy = e.target.value;
        setSortBy(newSortBy);
        setSearchParams({ sortBy: newSortBy, direction: sortDirection });
    };

    const toggleSortDirection = () => {
        const newDirection = sortDirection === "asc" ? "desc" : "asc";
        setSortDirection(newDirection);
        setSearchParams({ sortBy, direction: newDirection });
    };

    return (
        <div className="text-sm text-center">
        <label className="mr-2 font-medium text-gray-700">Sort by:</label>
        <select
            value={sortBy}
            onChange={handleSortChange}
            className="px-3 py-1 border rounded shadow-sm text-gray-800 bg-white"
        >
            {sortOptions.map((opt) => (
            <option key={opt}>{opt}</option>
            ))}
        </select>
        <button
            onClick={toggleSortDirection}
            className="ml-4 px-3 py-1 border rounded text-sm bg-white shadow-sm"
        >
            {sortDirection === "asc" ? "⬆ Ascending" : "⬇ Descending"}
        </button>
        </div>
    );
}

