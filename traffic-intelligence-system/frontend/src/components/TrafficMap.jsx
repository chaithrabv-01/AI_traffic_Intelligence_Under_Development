import { useEffect } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import { DataBadges } from "./DataBadge.jsx";
import CongestionBadge from "./CongestionBadge.jsx";

const COLORS = { low: "#2e9e6b", medium: "#d99a00", high: "#d2433a" };

function Fit({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 11);
    else if (points.length > 1) map.fitBounds(points, { padding: [40, 40] });
  }, [points, map]);
  return null;
}

// locations: items from /traffic/overview -> locations (they carry latitude, longitude, latest_level ...)
export default function TrafficMap({ locations }) {
  const points = locations.map((l) => [l.latitude, l.longitude]);
  return (
    <div className="map-box">
      <MapContainer center={[20.59, 78.96]} zoom={5} style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Fit points={points} />
        {locations.map((l) => (
          <CircleMarker key={l.location_id} center={[l.latitude, l.longitude]} radius={11}
            pathOptions={{ color: "#20252b", weight: 2, fillColor: COLORS[l.latest_level] || "#9aa5af", fillOpacity: 0.9 }}>
            <Popup>
              <strong>{l.name}</strong><br />
              {l.city}{l.state ? `, ${l.state}` : ""}<br />
              <CongestionBadge level={l.latest_level} /><br />
              Vehicles counted: {l.total_vehicles}<br />
              <DataBadges labels={l.data_labels} />
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
