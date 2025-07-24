import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
    const location = useLocation();
    const params = location.search; // Keep current sorting info

    const navLinkClass = (path) => 
        `font-semibold ${
            location.pathname === path
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-800 hover: text-black"
        }`;

    return (
        <nav className="w-full bg-white shadow p-4 flex justify-center space-x-6 sticky top-0 z-50">
        <Link to={`/${params}`} className="font-semibold text-gray-800 hover:text-black">Home</Link>
        <Link to={`/favourites${params}`} className="font-semibold text-gray-800 hover:text-black">Favourites</Link>
        <Link to={`/excluded${params}`} className="font-semibold text-gray-800 hover:text-black">Excluded</Link>
        </nav>
    );
}
