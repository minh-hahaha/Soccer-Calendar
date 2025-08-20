import { Link, useLocation } from "react-router-dom";

const Logobar = () => {
  const location = useLocation();

  const navigationLinks = [
    { path: "/", label: "Fixtures", description: "Match fixtures and predictions" },
    { path: "/standings", label: "Standings", description: "League table and standings" },
    { path: "/fantasy", label: "Fantasy AI", description: "Fantasy Football Assistant" }
  ];

  return (
    <nav className="bg-purple-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="bg-white rounded-md flex items-center justify-center">
                <img src="/PL_Logo.png" alt="Premier League Logo" className="w-20 h-full object-contain" />
              </div>
              <div>
                <span className="text-xl font-bold">Premier League</span>
                <div className="text-xs text-purple-200">AI-Powered Analytics</div>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-1">
            {navigationLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 relative group ${
                  location.pathname === link.path
                    ? "bg-purple-700 text-white shadow-lg"
                    : "text-purple-100 hover:bg-purple-700 hover:text-white"
                }`}
              >
                <div className="flex flex-col items-center">
                  <span>{link.label}</span>
                  {link.path === "/fantasy" && (
                    <div className="flex items-center">
                      <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                      <span className="text-xs text-green-300">AI</span>
                    </div>
                  )}
                </div>
                
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50">
                  {link.description}
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
              </Link>
            ))}
          </div>

          {/* Additional Info */}
          <div className="hidden md:flex items-center space-x-4 text-sm text-purple-200">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
              <span>Live Data</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Logobar;