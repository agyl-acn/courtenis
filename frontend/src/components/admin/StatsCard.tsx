import './StatsCard.css';

interface Props {
  label: string;
  value: number | string;
}

export default function StatsCard({ label, value }: Props) {
  return (
    <div className="stats-card">
      <div className="stats-card-value">{value}</div>
      <div className="stats-card-label">{label}</div>
    </div>
  );
}
