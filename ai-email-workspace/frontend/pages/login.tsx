import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../lib/auth';

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const { user, login, initialized } = useAuth();
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initialized) return;
    if (user) {
      router.replace('/');
    }
  }, [initialized, router, user]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json();
        const detail = body.detail;
        if (Array.isArray(detail)) {
          const message = detail
            .map((entry: { msg?: string }) => entry.msg)
            .filter(Boolean)
            .join(' ');
          setError(message || 'Login failed.');
        } else {
          setError(detail || 'Login failed.');
        }
        return;
      }
      const data = await res.json();
      login({ userId: data.user_id, email: data.email });
      router.push('/');
    } catch (err) {
      setError('Unable to reach the backend. Is it running on port 8000?');
    } finally {
      setLoading(false);
    }
  };

  if (user) {
    return null;
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>Inboxia</h1>
        <p>Sign in to your workspace.</p>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && <div className="login-error">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
