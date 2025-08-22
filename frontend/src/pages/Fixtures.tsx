import  { useEffect, useState } from "react";

type Match = { // must match with API response
  id: number;
  utcDate: string;
  displayTime: string;
  homeTeam: string;
  awayTeam: string;
  matchday: number;
  status: string;
  homeTeamCrest: string;
  awayTeamCrest: string;
  homeScore?: number;
  awayScore?: number;
};

type Team = {
  id: number;
  name: string;
  shortName: string;
};

type FixturesByDate = {
  [date: string]: Match[];
};

function formatDate(utc: string): string {
  const options: Intl.DateTimeFormatOptions = {
    weekday: "short",
    day: "numeric",
    month: "short",
  };
  return new Date(utc).toLocaleDateString(undefined, options);
}


const Fixtures = () => {
  const [fixtures, setFixtures] = useState<FixturesByDate>({});
  const [matchday, setMatchday] = useState(1);
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState("");
  // SCHEDULED | TIMED | IN_PLAY | PAUSED | EXTRA_TIME | PENALTY_SHOOTOUT 
  // FINISHED | SUSPENDED | POSTPONED | CANCELLED | AWARDED

  const fetchFixtures = async () => {
    setLoading(true);
    setError(null);
    
    const params = new URLSearchParams();
    if (selectedTeam) {
      params.append("team", selectedTeam);
    }
    if (matchday && matchday > 0) params.append("matchday", matchday.toString());
    if (status) params.append("status", status);
    
    try {
      const response = await fetch(`http://localhost:8000/v1/fixtures?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();

      // console.log(data.fixtures)
      
      // Check if data.fixtures exists and is an array
      if (!data.fixtures || !Array.isArray(data.fixtures)) {
        console.error('Invalid fixtures data:', data);
        setFixtures({});
        setError('Invalid data received from server');
        return;
      }
      
      const grouped: FixturesByDate = {}; // group matches by date
      data.fixtures.forEach((match: Match) => {
        const dateKey = formatDate(match.utcDate);
        if (!grouped[dateKey]) { // add new date if doesn't exist
          grouped[dateKey] = [];
        }
        grouped[dateKey].push(match);
      });
      setFixtures(grouped);
    } catch (error) {
      console.error('Error fetching fixtures:', error);
      setFixtures({});
      setError(error instanceof Error ? error.message : 'Failed to fetch fixtures');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFixtures();
  }, [matchday, status, selectedTeam]);

  ;
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await fetch(`http://localhost:8000/v1/teams`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Check if data.teams exists and is an array
        if (!data.teams || !Array.isArray(data.teams)) {
          console.error('Invalid teams data:', data);
          setTeams([]);
          return;
        }
        
        setTeams(data.teams);
      } catch (error) {
        console.error('Error fetching teams:', error);
        setTeams([]);
      }
    };
    
    fetchTeams();
  }, []);

  return (
    <div className="pt-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Fixtures</h1>
        
        <div className="pr-10 pl-10">
        <div className="flex flex-wrap text-white gap-4 mb-8 bg-purple-900 p-4 rounded">
          <div>
            <label className="mr-2 font-medium">Team:</label>
            <select onChange={(e) => {
              setSelectedTeam(e.target.value);
              if (e.target.value) setMatchday(0);
            }}>
              <option value="">Select Team</option>
              {teams.map(team => (
                <option key={team.shortName} value={team.shortName}>
                  {team.shortName}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mr-2 font-medium">Matchday:</label>
            <select
              className="text-white p-1 rounded"
              value={matchday}
              onChange={(e) => setMatchday(Number(e.target.value))}
            >
              {selectedTeam && <option value={0}>All</option>}
              {[...Array(38)].map((_, i) => (
                <option key={i} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mr-2 font-medium">Status:</label>
            <select
              className="text-white p-1 rounded"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All</option>
              <option value="TIMED">Timed</option>
              <option value="SCHEDULED">Scheduled</option>
              <option value="IN_PLAY">Live</option>
              <option value="FINISHED">Finished</option>
              <option value="POSTPONED">Postponed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading fixtures...</p>
          </div>
        )}
        
        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800">Error: {error}</span>
            </div>
          </div>
        )}
        
        {/* Fixtures Display */}
        {!loading && !error && Object.entries(fixtures).map(([date, matches]) => (
          <div key={date} className="mb-8">
            <h2 className="text-lg font-bold mb-4">{date}</h2>
            <div className="space-y-4">
              {matches.map((match, i) => (
                <div
                  key={i}
                  className="bg-purple-900 p-4 rounded shadow"
                >
                  {/* Match Info Row */}
                  <div className="flex justify-between items-center mb-4">
                    {/* Home Team (Left) */}
                    <div className="team-left">
                      <span className="text-white">{match.homeTeam}</span>
                      <img src={match.homeTeamCrest} alt={match.homeTeam} className="team-crest" />
                    </div>
                    
                    {/* Match Time or Score */}
                    <div className="match-time text-white">
                      {match.status === "FINISHED" && match.homeScore !== null && match.awayScore !== null ? (
                        <div className="text-center">
                          <div className="text-2xl font-bold">
                            {match.displayTime}
                          </div>
                          <div className="text-sm text-gray-300">FT</div>
                        </div>
                      ) : (
                        match.displayTime
                      )}
                    </div>
                    
                    {/* Away Team (Right) */}
                    <div className="team-right">
                      <img src={match.awayTeamCrest} alt={match.awayTeam} className="team-crest" />
                      <span className="text-white">{match.awayTeam}</span>
                    </div>
                  </div>
                  {/* Prediction Display */}
                  {/* {match.status === "SCHEDULED" || match.status === "TIMED" ? (
                    <div className="mt-4">
                      <PredictionDisplay matchId={match.id} compact={true} />
                    </div>
                  ) : (
                    <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                      <p className="text-sm text-gray-600 text-center">
                        {match.status === "FINISHED" ? "Match completed" : 
                         match.status === "IN_PLAY" ? "Match in progress" : 
                         `Match status: ${match.status}`}
                      </p>
                    </div>
                  )} */}
                </div>
              ))}
            </div>
          </div>
        ))}
        </div>
      </div>
    </div>
  );
};

export default Fixtures;
