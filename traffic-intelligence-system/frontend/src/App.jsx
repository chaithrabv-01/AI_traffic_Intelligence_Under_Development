import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { useAuth } from "./hooks/useAuth.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Locations from "./pages/Locations.jsx";
import Datasets from "./pages/Datasets.jsx";
import Process from "./pages/Process.jsx";
import Compare from "./pages/Compare.jsx";
import History from "./pages/History.jsx";

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/locations" element={<Locations />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/process" element={<Process />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/history" element={<History />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
