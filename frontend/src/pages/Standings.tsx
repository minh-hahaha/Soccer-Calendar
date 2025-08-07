import { useEffect, useState } from "react";
import MatchdayDropdown from "../components/MatchdayDropdown";

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
};

export default function Standings() {
  const [standings, setStandings] = useState<Standing[]>([]);
  const [matchday, setMatchday] = useState<number | null>(null);

  useEffect(() => {
    const url = matchday
      ? `http://localhost:8000/standings?matchday=${matchday}`
      : `http://localhost:8000/standings`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const result = data.standings.map((t: any) => ({
          ...t,
        //   crest: t.teamCrest, // if you added crest to the response
        }));
        setStandings(result);
      });
  }, [matchday]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Premier League Standings</h1>

      <MatchdayDropdown selected={matchday} onChange={setMatchday} />

      <table className="w-full border-collapse text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 text-left">#</th>
            <th className="p-2 text-left">Team</th>
            <th className="p-2">P</th>
            <th className="p-2">W</th>
            <th className="p-2">D</th>
            <th className="p-2">L</th>
            <th className="p-2">GD</th>
            <th className="p-2">Pts</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((team) => (
            <tr key={team.position} className="border-t">
              <td className="p-2">{team.position}</td>
              <td className="p-2 flex items-center gap-2">
                <img src={team.crest} alt="crest" className="w-5 h-5" />
                {team.team}
              </td>
              <td className="p-2 text-center">{team.playedGames}</td>
              <td className="p-2 text-center">{team.won}</td>
              <td className="p-2 text-center">{team.draw}</td>
              <td className="p-2 text-center">{team.lost}</td>
              <td className="p-2 text-center">{team.goalDifference}</td>
              <td className="p-2 text-center font-semibold">{team.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
