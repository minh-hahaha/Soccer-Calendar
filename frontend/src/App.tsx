import { BrowserRouter, Routes, Route } from "react-router-dom";
import Standings from "./pages/Standings";
import Fixtures from "./pages/Fixtures"; // your existing page
import Logobar from "./components/Logobar";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Logobar />
        <Routes>
          <Route path="/" element={<Fixtures />} />
          <Route path="/standings" element={<Standings />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
 
export default App;