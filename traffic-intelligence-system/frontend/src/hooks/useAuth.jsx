import { createContext, useContext, useState } from "react";
import { login as apiLogin } from "../services/api.js";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("tis_user")); } catch { return null; }
  });

  async function login(username, password) {
    const data = await apiLogin(username, password);
    localStorage.setItem("tis_token", data.access_token);
    localStorage.setItem("tis_user", JSON.stringify(data.user));
    setUser(data.user);
  }

  function logout() {
    localStorage.removeItem("tis_token");
    localStorage.removeItem("tis_user");
    setUser(null);
  }

  return (
    <AuthCtx.Provider value={{ user, login, logout, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
