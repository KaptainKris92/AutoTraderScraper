import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Favourites from "./pages/Favourites";
import Excluded from "./pages/Excluded";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/favourites" element={<Favourites />} />
        <Route path="/excluded" element={<Excluded />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  );
}
