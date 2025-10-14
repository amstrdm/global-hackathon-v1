import { Routes, Route, Navigate } from "react-router-dom";
import SimpleFlow from "./components/SimpleFlow";
import Dashboard from "./pages/Dashboard";
import Room from "./pages/Room";
import ErrorDisplay from "./components/ErrorDisplay";
import { useUserStore } from "./store/useStore";

function App() {
  const { user } = useUserStore();

  return (
    <div className="min-h-screen">
      <ErrorDisplay />
      <Routes>
        <Route
          path="/"
          element={!user ? <SimpleFlow /> : <Navigate to="/dashboard" />}
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
