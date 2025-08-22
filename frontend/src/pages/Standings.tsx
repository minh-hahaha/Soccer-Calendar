import { useEffect, useState } from "react";

type Standing = {
  position: number;
  team: string;
  crest: string;
  playedGames: number;
  won: number;
  draw: number;
  lost: number;
  points: number;
  goalDifference: number;
  form: string;
};

export default function Standings() {
  const [standings, setStandings] = useState<Standing[]>([]);
  const [matchday, setMatchday] = useState<number | null>(null);
  const [season, setSeason] = useState<number>(2025);

  useEffect(() => {
    const url = matchday 
      ? `http://localhost:8000/v1/standings/?season=${season}&matchday=${matchday}`
      : `http://localhost:8000/v1/standings/?season=${season}`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const result = data.standings.map((t: any) => ({
          ...t,
        }));
        setStandings(result);
      });
  }, [matchday, season]);


  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Premier League Standings</h1>

      {/* no more filter since complicated db */}
      {/* <div className="flex flex-wrap text-white gap-4 mb-8 bg-purple-900 p-4 rounded">
        <div>
          <label className="mr-2 font-medium">Matchday:</label>
            <select
              className="text-white p-1 rounded"
              value={matchday || ""}
              onChange={(e) => setMatchday(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">All</option>
              {[...Array(38)].map((_, i) => (
                <option key={i} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </select>
            </div>
            <div>
              <label className="mr-2 font-medium">Season:</label>
              <select
                className="text-white p-1 rounded"
                value={season}
                onChange={(e) => setSeason(Number(e.target.value))}
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
              </select>
            </div>
      </div> */}

      <table className="w-full border-collapse text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 text-left align-middle">#</th>
            <th className="p-2 text-left align-middle">Team</th>
            <th className="p-2 align-middle">P</th>
            <th className="p-2 align-middle">W</th>
            <th className="p-2 align-middle">D</th>
            <th className="p-2 align-middle">L</th>
            <th className="p-2 align-middle">GD</th>
            <th className="p-2 align-middle">Pts</th>
            <th className="p-2 align-middle">Form</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((team) => (
            <tr key={team.position} className="border-t">
              <td className="p-2 align-middle">{team.position}</td>
              <td className="p-3 align-middle">
                <div className="flex items-center gap-2">
                  <img src={team.crest} alt="crest" className="w-5 h-5" />
                  {team.team}
                </div>
              </td>
              <td className="p-2 text-center align-middle">{team.playedGames}</td>
              <td className="p-2 text-center align-middle">{team.won}</td>
              <td className="p-2 text-center align-middle">{team.draw}</td>
              <td className="p-2 text-center align-middle">{team.lost}</td>
              <td className="p-2 text-center align-middle">{team.goalDifference}</td>
              <td className="p-2 text-center font-semibold align-middle">{team.points}</td>
              <td className="p-2 align-middle w-40">
                <div className="flex gap-1 items-center justify-center">
                  {team.form
                    ? team.form.split(",").map((result, idx) => {
                        let bgColor = "";
                        if (result === "W") bgColor = "bg-green-500";
                        else if (result === "D") bgColor = "bg-yellow-400";
                        else if (result === "L") bgColor = "bg-red-500";

                        return (
                          <span
                            key={idx}
                            className={`${bgColor} text-white px-2 py-1 rounded text-xs font-bold w-6 h-6 flex items-center justify-center`}
                          >
                            {result}
                          </span>
                        );
                      })
                    : <span className="bg-gray-300 text-white px-2 py-1 rounded text-xs font-bold w-6 h-6 flex items-center justify-center">
                        -
                      </span>}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
