import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { animate, createScope, createTimeline, stagger } from 'animejs'
import { Input } from '../components/ui/input'
import { prefersReducedMotion } from '../lib/motion'
import { login } from '../lib/api'


export default function LoginPage(){
  const navigate = useNavigate()
  const root = useRef<HTMLDivElement>(null)
  const formRef = useRef<HTMLFormElement>(null)
  const [error,setError] = useState<"" | "Invalid credentials">("")
  const [loading,setLoading] = useState(false)
  useEffect(() => {
  const el = root.current
  if (!el || prefersReducedMotion()) return

  const brand = el.querySelectorAll('.login-brand')
  const fields = el.querySelectorAll('.login-field')
  const glow = el.querySelectorAll('.login-glow')
  console.log('found:', brand.length, fields.length, glow.length) // expect 1, 6, 1

  const tl = createTimeline({ defaults: { ease: 'outExpo' } })
    .add(brand, { opacity: [0, 1], translateX: [-24, 0], duration: 900 })
    .add(fields, { opacity: [0, 1], translateY: [16, 0], duration: 700, delay: stagger(90) }, '-=600')

  const loop = animate(glow, {
    scale: [1, 1.25],
    opacity: [0.2, 0.45],
    duration: 4500,
    ease: 'inOutSine',
    alternate: true,
    loop: true,
  })

  return () => {
    tl.revert()
    loop.revert()
  }
}, [])
  function shake() {
    if (prefersReducedMotion() || !formRef.current) return
    animate(formRef.current, {
      translateX: [0, -10, 10, -6, 6, 0],
      duration: 400,
      ease: 'outQuad',
    })
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const data = new FormData(e.currentTarget)

    try {
      await login({
        username: data.get('username') as string,
        password: data.get('password') as string,
      })
      navigate('/account')
    } catch  {
      setError('Invalid credentials')
      shake()
    } finally {
      setLoading(false)
    }
}

 return (
    <main ref={root} className="grid min-h-screen lg:grid-cols-2">
      {/* left: brand panel, hidden on small screens */}
      <aside className="relative hidden overflow-hidden border-r border-zinc-800 lg:block">
        <div className="login-glow pointer-events-none absolute inset-0 m-auto h-96 w-96 rounded-full bg-emerald-500/25 blur-3xl" />
        <div className="login-brand relative z-10 flex h-full flex-col justify-between p-12 motion-safe:opacity-0">
          <Link to="/" className="text-lg font-semibold text-emerald-400">GreenApp</Link>
          <p className="max-w-sm text-3xl font-medium leading-snug">
            Small changes at home add up to a big drop in your footprint.
          </p>
        </div>
      </aside>

      {/* right: form */}
      <section className="grid place-items-center p-6">
        <form ref={formRef} onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
          <div className="login-field motion-safe:opacity-0">
            <h1 className="text-2xl font-semibold">Welcome back</h1>
            <p className="mt-1 text-sm text-zinc-400">Log in to see your footprint and bookings.</p>
          </div>

          <div className="login-field motion-safe:opacity-0">
            <Input label="Username" name="username" autoComplete="username" required />
          </div>
          <div className="login-field motion-safe:opacity-0">
            <Input label="Password" name="password" type="password" autoComplete="current-password" required />
          </div>

          {error && <p role="alert" className="text-sm text-red-400">{error}</p>}

          <button
            disabled={loading}
            className="login-field w-full rounded-lg bg-emerald-500 py-2.5 font-medium text-zinc-950 hover:bg-emerald-400 disabled:opacity-50 motion-safe:opacity-0"
          >
            {loading ? 'Signing in…' : 'Log in'}
          </button>

          <p className="login-field text-center text-sm text-zinc-400 motion-safe:opacity-0">
            No account? <Link to="/register" className="text-emerald-400 hover:underline">Sign up</Link>
          </p>
        </form>
      </section>
    </main>
  )
}