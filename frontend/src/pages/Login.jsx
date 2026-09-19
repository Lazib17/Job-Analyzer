import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, loginGoogle } from '../api/axios';
import { AuthExperience } from '@/components/auth/AuthExperience';

function getErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  return fallback;
}

function persistSession(data, onLogin, navigate) {
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  onLogin(data.user);
  navigate('/');
}

export default function Login({ onLogin }) {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleSubmit = async (form) => {
    setError('');
    setLoading(true);
    try {
      const { data } = await login({ email: form.email, password: form.password });
      persistSession(data, onLogin, navigate);
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async (accessToken) => {
    setError('');
    setGoogleLoading(true);
    try {
      const { data } = await loginGoogle(accessToken);
      persistSession(data, onLogin, navigate);
    } catch (err) {
      setError(getErrorMessage(err, 'Google sign-in failed'));
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <AuthExperience
      mode="login"
      loading={loading}
      googleLoading={googleLoading}
      serverError={error}
      onSubmit={handleSubmit}
      onGoogle={handleGoogle}
      onGoogleError={setError}
    />
  );
}
