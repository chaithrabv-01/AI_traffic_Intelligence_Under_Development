const INFO = {
  real: ["Real camera", "Footage from a real camera at this location"],
  dataset: ["Dataset footage", "Real footage from a public dataset, assigned only where the source supports the location"],
  demo: ["Demo data", "Sample or simulated footage. Not real traffic for this location"],
};

export default function DataBadge({ label }) {
  const [text, tip] = INFO[label] || INFO.demo;
  return <span className={`databadge ${INFO[label] ? label : "demo"}`} title={tip}>{text}</span>;
}

export function DataBadges({ labels }) {
  if (!labels || labels.length === 0) return <span className="text-muted">-</span>;
  return <>{labels.map((l) => <DataBadge key={l} label={l} />)}</>;
}
