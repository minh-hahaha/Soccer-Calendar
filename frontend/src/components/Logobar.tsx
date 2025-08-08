import { Link, useLocation } from "react-router-dom";

const Logobar = () => {
  const location = useLocation();

  return (
    <nav className="bg-purple-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="bg-white rounded-md flex items-center justify-center ">
                <img src="/PL_Logo.png" alt="Premier League Logo" className="w-20 h-full object-contain" />
              </div>
              <span className="text-xl font-bold">Premier League</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-8">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                location.pathname === "/"
                  ? "bg-purple-700 text-white"
                  : "text-purple-100 hover:bg-purple-700 hover:text-white"
              }`}
            >
              Fixtures
            </Link>
            <Link
              to="/standings"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                location.pathname === "/standings"
                  ? "bg-purple-700 text-white"
                  : "text-purple-100 hover:bg-purple-700 hover:text-white"
              }`}
            >
              Standings
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Logobar;
