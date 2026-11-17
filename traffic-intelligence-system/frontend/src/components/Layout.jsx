import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.jsx";

const links = [
  ["/", "Dashboard"],
  ["/locations", "Locations"],
  ["/datasets", "Datasets"],
  ["/process", "Upload & process"],
  ["/compare", "Compare"],
  ["/history", "History"],
];

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="shell">
      <nav className="sidebar">
        <div className="brand">Traffic Intelligence<small>vehicle counting from video</small></div>
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
            {label}
          </NavLink>
        ))}
        <div className="who">
          {user.username} ({user.role})<br />
          <a href="#logout" onClick={(e) => { e.preventDefault(); logout(); }} style={{ padding: 0 }}>Log out</a>
        </div>
      </nav>
      <main className="content"><Outlet /></main>
    </div>
  );
}
