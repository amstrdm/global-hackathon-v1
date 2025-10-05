import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Room from "./pages/Room";
import { useUserStore } from "./store/useStore";

function App() {
  const { user } = useUserStore();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-4xl font-bold text-center mb-8 text-cyan-400">
        EAAS - Escrow as a Service
      </h1>
      <Routes>
        <Route
          path="/"
          element={!user ? <Home /> : <Navigate to="/dashboard" />}
        />
        <Route
          path="/dashboard"
          element={user ? <Dashboard /> : <Navigate to="/" />}
        />
        <Route
          path="/room/:room_phrase"
          element={user ? <Room /> : <Navigate to="/" />}
        />
      </Routes>
    </div>
  );
}

export default App;
