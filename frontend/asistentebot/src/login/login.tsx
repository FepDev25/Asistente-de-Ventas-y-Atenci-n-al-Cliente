// src/components/Login/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './login.css';

const Login: React.FC = () => {
  const [identifier, setIdentifier] = useState(''); // Puede ser email o username
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validación básica
    if (!identifier || !password) {
      setError('Por favor completa todos los campos');
      return;
    }

    try {
      setIsLoading(true);
      await login(identifier, password);
      
      // Redirigir a la tienda después del login exitoso
      navigate('/tienda');
    } catch (err: any) {
      console.error('Error de login:', err);
      
      // Manejo de errores específicos según el código de estado
      if (err.response) {
        switch (err.response.status) {
          case 401:
            setError('Credenciales inválidas. Verifica tu usuario/email y contraseña.');
            break;
          case 403:
            setError('Usuario desactivado. Contacte al administrador.');
            break;
          case 429:
            setError('Demasiados intentos. Por favor espera un momento e intenta de nuevo.');
            break;
          case 400:
            setError(err.response.data?.detail || 'Datos inválidos. Verifica la información ingresada.');
            break;
          default:
            setError('Error al iniciar sesión. Por favor intenta de nuevo.');
        }
      } else if (err.request) {
        setError('No se pudo conectar con el servidor. Verifica tu conexión a internet.');
      } else {
        setError('Error inesperado. Por favor intenta de nuevo.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Bienvenido</h1>
          <p>Inicia sesión para continuar</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="identifier">Usuario o Email</label>
            <input
              type="text"
              id="identifier"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="usuario o tu@email.com"
              disabled={isLoading}
              autoComplete="username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={isLoading}
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="login-footer">
          <a href="#" className="forgot-password">¿Olvidaste tu contraseña?</a>
        </div>
      </div>
    </div>
  );
};

export default Login;