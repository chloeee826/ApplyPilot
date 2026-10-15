import { useEffect, useState, type FormEvent } from 'react'
import App from '../App'
import { currentUser, signIn, signOut, type User } from '../api/auth'

export function AuthGate() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void currentUser().then((saved) => { if (!cancelled) setUser(saved) })
      .catch(() => { if (!cancelled) setError('Could not connect. Reload the page to try again.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    function expired() { setUser(null); setPassword(''); setError('Your session expired. Sign in again.') }
    function checkOtherTab() {
      void currentUser().then((saved) => {
        if (!cancelled) setUser(saved)
      }).catch(() => { /* Network failure is not proof of session revocation. */ })
    }
    window.addEventListener('applypilot-session-expired', expired)
    window.addEventListener('focus', checkOtherTab)
    return () => {
      cancelled = true
      window.removeEventListener('applypilot-session-expired', expired)
      window.removeEventListener('focus', checkOtherTab)
    }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true); setError(null)
    try {
      const saved = await signIn(mode, email, password)
      setPassword(''); setUser(saved)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign-in failed') }
    finally { setBusy(false) }
  }

  async function logout() {
    setBusy(true); setError(null)
    try {
      await signOut()
      setUser(null); setPassword('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign-out failed') }
    finally { setBusy(false) }
  }

  if (loading) return <main className="auth-screen"><p role="status">Checking your session…</p></main>
  if (user) return <>
    <div className="account-bar"><span>Signed in as {user.email}</span>
      <button type="button" disabled={busy} onClick={logout}>Sign out</button>
      {error && <p role="alert">{error}</p>}
    </div>
    {/* A different account must mount a fresh workspace: no previous user's state. */}
    <App key={user.id} />
  </>

  return <main className="auth-screen"><section className="auth-card" aria-label="Account access">
    <p className="eyebrow">ApplyPilot</p>
    <h1>{mode === 'login' ? 'Welcome back.' : 'Your next role starts here.'}</h1>
    <p>Keep your resume evidence, saved roles and match reports in your own workspace.</p>
    <form onSubmit={submit}>
      <label>Email<input type="email" autoComplete="username" required maxLength={254} value={email}
        disabled={busy} onChange={(event) => setEmail(event.target.value)} /></label>
      <label>Password<input type="password" required minLength={12} maxLength={128}
        autoComplete={mode === 'register' ? 'new-password' : 'current-password'} value={password}
        disabled={busy} onChange={(event) => setPassword(event.target.value)} /></label>
      <p className="muted">Use 12–128 characters. Email is a login identifier; email verification and password recovery are not available yet. Use a unique password.</p>
      {error && <p role="alert" className="error-message">{error}</p>}
      <button className="primary-button" disabled={busy} type="submit">
        {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
      </button>
    </form>
    <button type="button" className="text-button" disabled={busy} onClick={() => {
      setMode(mode === 'login' ? 'register' : 'login'); setPassword(''); setError(null)
    }}>{mode === 'login' ? 'New here? Create an account' : 'Already registered? Sign in'}</button>
  </section></main>
}
