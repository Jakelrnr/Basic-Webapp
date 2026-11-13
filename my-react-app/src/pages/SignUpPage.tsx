import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { animate, createTimeline, stagger } from 'animejs'
import { Input } from '../components/ui/input'
import { prefersReducedMotion } from '../lib/motion'
import { register } from '../lib/api'
import { Logo } from '../components/Logo'
import { APP_NAME } from '../lib/config'
import { useAuth0 } from "@auth0/auth0-react";
import { loginWithAuth0 } from "../lib/api";

export default function SignUpPage(){

    const navigate = useNavigate()
    const {
        loginWithRedirect,
        isLoading: auth0Loading,
        isAuthenticated,
        getAccessTokenSilently,
      } = useAuth0();
      
      const authHandled = useRef(false);
      const [notice, setNotice] = useState("");
      
      const authHandled = useRef(false);
      const [notice, setNotice] = useState("");
    const root = useRef<HTMLDivElement>(null)
    const formRef = useRef<HTMLFormElement>(null)
    
    const [error, setError] = useState<string>('')
    const [loading, setLoading] = useState(false)

    useEffect(() =>{
        const el = root.current
        if(!el || prefersReducedMotion()) return 
        const brand = el.querySelectorAll('.signup-brand')
        const fields = el.querySelectorAll('.signup-field')
        const glow = el.querySelectorAll('.signup-glow')
        const tl = createTimeline({ defaults: { ease: 'outExpo' } })
      .add(brand, { opacity: [0, 1], translateX: [-24, 0], duration: 900 })
      .add(fields, { opacity: [0, 1], translateY: [16, 0], duration: 700, delay: stagger(80) }, '-=600')

        const loop = animate(glow,{scale : [1,1.3],opacity:[0.2,0.5],duration:5000,ease:"inOutSine",alternate:true,loop:true})

        return() =>{
            tl.revert()
            loop.revert()
        }
    },[])
    function shake() {
        if (prefersReducedMotion() || !formRef.current) return
        animate(formRef.current, {
          translateX: [0, -12, 12, -8, 8, -4, 4, 0],
          duration: 450,
          ease: 'outQuad',
        })
      }

      async function handleSocialLogin(connection: string) {
        setError("");
        setLoading(true);
      
        try {
          await loginWithRedirect({
            authorizationParams: {
              connection,
              audience: "https://yourapp-api",
              scope: "openid profile email",
            },
          });
        } catch (err) {
          setError("Could not start social login. Please try again.");
          setLoading(false);
        }
      }

      async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        setError('')
        const data = new FormData(e.currentTarget)
        const username = data.get('username') as string
        const email = data.get('email') as string
        const password = data.get('password') as string
        const confirmPassword = data.get('confirmPassword') as string
    
      
        if (password !== confirmPassword) {
          setError('Passwords do not match')
          shake()
          return
        }
    
        if (password.length < 8) {
          setError('Password must be at least 8 characters')
          shake()
          return
        }
    
        setLoading(true)
        try{await register({username,email,password})
        navigate("/homepage")
    }catch(err:any){
        setError(err.message || "registration failed")
        shake()
    }finally{
        setLoading(false)
    }
    }

    return (
        <main ref={root} className="grid min-h-screen lg:grid-cols-2 bg-[#120D1A] text-zinc-100">
    
          <aside className="relative hidden overflow-hidden lg:block border-r border-white/5 bg-[#171022]">
            <div className="signup-glow pointer-events-none absolute inset-0 m-auto h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />
            <div className="relative z-10 flex h-full flex-col items-center justify-center gap-6 p-12 text-center">
              <Logo size={180} />
              <div className="signup-brand motion-safe:opacity-0">
                <h2 className="text-3xl font-bold text-emerald-400">{APP_NAME}</h2>
                <p className="mx-auto mt-3 max-w-sm text-lg leading-relaxed text-zinc-300">
                  Create an account to begin tracking and reducing your household footprint.
                </p>
              </div>
            </div>
          </aside>
    
        
          <section className="grid place-items-center p-6">
            <form ref={formRef} onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
              <div className="signup-field motion-safe:opacity-0">
                <h1 className="text-2xl font-bold text-white">Create an account</h1>
                <p className="mt-1 text-sm text-zinc-400">
                  Already have an account?{' '}
                  <Link to="/login" className="text-emerald-400 hover:underline">
                    Sign in
                  </Link>
                </p>
              </div>
    
              <div className="signup-field motion-safe:opacity-0">
                <Input label="Username" name="username" autoComplete="username" required />
              </div>
    
              <div className="signup-field motion-safe:opacity-0">
                <Input label="Email Address" name="email" type="email" autoComplete="email" required />
              </div>
    
              <div className="signup-field motion-safe:opacity-0">
                <Input label="Password" name="password" type="password" required />
              </div>
    
              <div className="signup-field motion-safe:opacity-0">
                <Input label="Confirm Password" name="confirmPassword" type="password" required />
              </div>
    
              {error && (
                <p role="alert" className="text-sm font-medium text-rose-400">
                  {error}
                </p>
              )}
    
              <button
                type="submit"
                disabled={loading}
                className="signup-field w-full rounded-lg bg-emerald-500 py-2.5 font-semibold text-zinc-950 transition-colors hover:bg-emerald-400 disabled:opacity-50 motion-safe:opacity-0"
              >
                {loading ? 'Creating Account...' : 'Sign Up'}
              </button>
    
             
              <div className="signup-field relative my-6 flex items-center justify-center text-xs uppercase text-zinc-500 motion-safe:opacity-0">
                <div className="absolute inset-x-0 h-px bg-zinc-800" />
                <span className="relative bg-[#120D1A] px-3 font-medium">Or continue with</span>
              </div>
    
              <div className="signup-field grid grid-cols-2 gap-3 motion-safe:opacity-0">
                <a
                  href="http://localhost:8001/api/auth/google"
                  className="flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-sm font-medium text-zinc-200 transition-all hover:border-zinc-700 hover:bg-zinc-800"
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24">
                    <path
                      fill="#EA4335"
                      d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
                    />
                    <path
                      fill="#4285F4"
                      d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3 0-.8.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15s.7 5.3 1.9 7.7l3.7-2.9z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2-6.4-4.8L1.9 16.4C3.7 20.4 7.5 23 12 23z"
                    />
                  </svg>
                  Google
                </a>
    
                <a
                  href="http://localhost:8001/api/auth/discord"
                  className="flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-[#5865F2]/10 px-4 py-2.5 text-sm font-medium text-[#7983F5] transition-all hover:bg-[#5865F2]/20"
                >
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.893.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                  Discord
                </a>
              </div>
            </form>
          </section>
        </main>
      )
    }




    











