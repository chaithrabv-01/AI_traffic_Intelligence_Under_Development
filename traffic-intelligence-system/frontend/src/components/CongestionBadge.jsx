const TEXT = { low: "Low", medium: "Medium", high: "High" };

// A small traffic signal: the lit lamp shows the congestion level.
export default function CongestionBadge({ level }) {
  if (!level) return <span className="text-muted">No data</span>;
  return (
    <span className="signal" title={`Congestion: ${TEXT[level]}`}>
      <span className="lamps">
        <span className={`lamp ${level === "high" ? "on-high" : ""}`} />
        <span className={`lamp ${level === "medium" ? "on-medium" : ""}`} />
        <span className={`lamp ${level === "low" ? "on-low" : ""}`} />
      </span>
      <span className="txt">{TEXT[level]}</span>
    </span>
  );
}
