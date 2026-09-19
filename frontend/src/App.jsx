import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import JobDetails from './pages/JobDetails';
import JobResults from './pages/JobResults';
import JobSearch from './pages/JobSearch';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import UploadResume from './pages/UploadResume';

function ProtectedRoute({ user, children }) {
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const handleLogin = (userData) => setUser(userData);
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <BrowserRouter>
      {user && <Navbar user={user} onLogout={handleLogout} />}
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login onLogin={handleLogin} />} />
        <Route path="/register" element={user ? <Navigate to="/" /> : <Register onLogin={handleLogin} />} />
        <Route
          path="/"
          element={
            user ? (
              <ProtectedRoute user={user}>
                <Dashboard />
              </ProtectedRoute>
            ) : (
              <Landing />
            )
          }
        />
        <Route path="/upload" element={<ProtectedRoute user={user}><UploadResume /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute user={user}><JobSearch /></ProtectedRoute>} />
        <Route path="/results" element={<ProtectedRoute user={user}><JobResults /></ProtectedRoute>} />
        <Route path="/jobs/:id" element={<ProtectedRoute user={user}><JobDetails /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
