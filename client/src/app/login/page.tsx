"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email === 'test' && password === 'test') {
      localStorage.setItem('melanoma_user', JSON.stringify({
        email: 'test',
        role: 'tester',
        subscription: 'active_multi_scan'
      }));
      router.push('/');
    } else {
      setError('Invalid credentials. Please use your authorized clinical account.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 style={{ color: 'white', marginBottom: '8px' }}>Clinical Portal</h2>
        <p style={{ color: 'var(--text-light)', marginBottom: '32px', fontSize: '14px' }}>
          Sign in to access the Melanoma AI framework.
        </p>

        {error && <div style={{ color: 'var(--warning)', marginBottom: '20px', fontSize: '13px' }}>{error}</div>}

        <form onSubmit={handleLogin}>
          <input 
            type="text" 
            placeholder="Gmail / Clinical ID" 
            className="input-field"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="input-field"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit" className="btn-primary" style={{ marginTop: '10px' }}>
            Authenticate
          </button>
        </form>

        <p style={{ color: 'var(--text-light)', marginTop: '24px', fontSize: '12px' }}>
          Protected by AES-256 Encryption
        </p>
      </div>
    </div>
  );
}
