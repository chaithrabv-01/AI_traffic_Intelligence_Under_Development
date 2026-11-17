export default function StatCard({ label, value, hint, alert }) {
  return (
    <div className={`stat ${alert ? "alert-on" : ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}
