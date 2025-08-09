import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import StudentManagement from './components/StudentManagement';
import AttendanceMarking from './components/AttendanceMarking';
import AttendanceHistory from './components/AttendanceHistory';
import Navbar from './components/Navbar';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  return isAuthenticated ? children : <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <ToastContainer />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Navigate to="/attendance" replace />} />
            <Route path="/dashboard" element={
              <PrivateRoute>
                <div>
                  <Navbar />
                  <Dashboard />
                </div>
              </PrivateRoute>
            } />
            <Route path="/students" element={
              <PrivateRoute>
                <div>
                  <Navbar />
                  <StudentManagement />
                </div>
              </PrivateRoute>
            } />
            <Route path="/attendance" element={
              <div>
                <Navbar />
                <AttendanceMarking />
              </div>
            } />
            <Route path="/history" element={
              <PrivateRoute>
                <div>
                  <Navbar />
                  <AttendanceHistory />
                </div>
              </PrivateRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App; 