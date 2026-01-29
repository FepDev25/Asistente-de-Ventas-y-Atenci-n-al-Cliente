// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './login/login';
import Store from './store/store';
import ChatBot from './chat/chatbot';
import './App.css';

function AppContent() {
  return (
    <>
      <Routes>
        {/* Login (ahora solo una página más) */}
        <Route path="/login" element={<Login />} />

        {/* Rutas públicas */}
        <Route path="/tienda" element={<Store />} />
        <Route path="/store" element={<Store />} />
        <Route path="/productos" element={<Store />} />

        {/* Ruta principal */}
        <Route path="/" element={<Navigate to="/tienda" />} />

        {/* 404 */}
        <Route
          path="*"
          element={
            <div className="loading-screen">
              <h1 style={{ fontSize: '48px', marginBottom: '16px' }}>404</h1>
              <p>Página no encontrada</p>
              <button
                onClick={() => window.location.href = '/tienda'}
                style={{
                  marginTop: '20px',
                  padding: '12px 24px',
                  background: '#1a1a1a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Volver a la tienda
              </button>
            </div>
          }
        />
      </Routes>

      {/* ChatBot siempre visible */}
      <ChatBot />
    </>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
