import  { useEffect, useState } from "react";

type Match = { // must match with API response
  utcDate: string;
  homeTeam: string;
  awayTeam: string;
  matchday: number;
  status: string;
  homeTeamCrest: string;
  awayTeamCrest: string;
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

function formatTime(utc: string): string {
  return new Date(utc).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const Fixtures = () => {
  const [fixtures, setFixtures] = useState<FixturesByDate>({});
  const [matchday, setMatchday] = useState(1);
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState("");

  const [status, setStatus] = useState("");
  // SCHEDULED | TIMED | IN_PLAY | PAUSED | EXTRA_TIME | PENALTY_SHOOTOUT 
  // FINISHED | SUSPENDED | POSTPONED | CANCELLED | AWARDED

  const fetchFixtures = async () => {
    const params = new URLSearchParams();
    if (selectedTeam) {
      params.append("team", selectedTeam);
    }
    if (matchday && matchday > 0) params.append("matchday", matchday.toString());
    if (status) params.append("status", status);
    fetch(`http://localhost:8000/fixtures?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        const grouped: FixturesByDate = {}; // group matches by date
        data.fixtures.forEach((match: Match) => {
          const dateKey = formatDate(match.utcDate);
          if (!grouped[dateKey]) { // add new date if doesn't exist
            grouped[dateKey] = [];
          }
          grouped[dateKey].push(match);
        });
        setFixtures(grouped);
      });
  };

  useEffect(() => {
    fetchFixtures();
  }, [matchday, status, selectedTeam]);

  ;
  useEffect(() => {
    fetch(`http://localhost:8000/teams`)
      .then((res) => res.json())
      .then((data) => {
        setTeams(data.teams);
      });
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
        {Object.entries(fixtures).map(([date, matches]) => (
          <div key={date} className="mb-8">
            <h2 className="text-lg font-bold mb-4">{date}</h2>
            <div className="space-y-4">
              {matches.map((match, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center bg-purple-900 p-4 rounded shadow"
                >
                  {/* Home Team (Left) */}
                  <div className="team-left">
                    <span className="text-white">{match.homeTeam}</span>
                    <img src={match.homeTeamCrest} alt={match.homeTeam} className="team-crest" />
                  </div>
                  
                  {/* Match Time */}
                  <div className="match-time text-white">
                    {formatTime(match.utcDate)}
                  </div>
                  
                  {/* Away Team (Right) */}
                  <div className="team-right">
                    <img src={match.awayTeamCrest} alt={match.awayTeam} className="team-crest" />
                    <span className="text-white">{match.awayTeam}</span>
                  </div>
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
