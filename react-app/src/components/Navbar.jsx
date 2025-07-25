import { NavLink, useLocation } from "react-router-dom";

export default function Navbar() {
    const location = useLocation();
    const params = location.search; // Keep current sorting info

    const baseClass = "font-semibold px-2 transition-colors duration-150";

    const getLinkClass = ({ isActive }) =>
        `${baseClass} ${
            isActive
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-800 hover:text-black"
        }`

    return (
        <nav className="w-full bg-white shadow p-4 flex justify-center space-x-6 sticky top-0 z-50">
        <NavLink to={`/${params}`} className={getLinkClass}>Home</NavLink>
        <NavLink to={`/favourites${params}`} className={getLinkClass}>Favourites</NavLink>
        <NavLink to={`/excluded${params}`} className={getLinkClass}>Excluded</NavLink>
        </nav>
    );
}
