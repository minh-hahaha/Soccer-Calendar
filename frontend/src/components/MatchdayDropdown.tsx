type Props = {
    selected: number | null;
    onChange: (value: number) => void;
  };
  
  export default function MatchdayDropdown({ selected, onChange }: Props) {
    const matchdays = Array.from({ length: 38 }, (_, i) => i + 1);
  
    return (
      <div className="mb-4">
        <label className="mr-2 font-medium">Matchday:</label>
        <select
          value={selected ?? ""}
          onChange={(e) => onChange(Number(e.target.value))}
          className="border p-2 rounded"
        >
          <option value="">All</option>
          {matchdays.map((day) => (
            <option key={day} value={day}>
              {day}
            </option>
          ))}
        </select>
      </div>
    );
  }
  