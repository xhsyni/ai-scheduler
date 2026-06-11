import { useState } from "react";
import { Eye, EyeOff, Mail, Lock, User, ArrowRight, Sparkles, Users, Brain, CheckCircle2, Calendar } from "lucide-react";
import { CogniLogo } from "./CogniLogo";
import { useDispatch } from "react-redux";
import { registerUser, loginUser } from "../redux/auth";
import Cookies from "js-cookie";
import { toast } from "sonner";
import { showErrorToast } from "@/utils/errors";

type Mode = "login" | "register";

export function AuthScreen({ onAuthed }: { onAuthed: (name: string) => void }) {
  const dispatch = useDispatch();
  const [mode, setMode] = useState<Mode>("login");
  const [showPw, setShowPw] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [agree, setAgree] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mode === "register") {
        if (password !== confirmPassword) {
          throw new Error("Passwords do not match");
        }
        const result = await dispatch(registerUser({ username: name, email, password })).unwrap();
        if (result.status_code === 200) {
          toast.success("Account created successfully! Please sign in.");
          setMode("login");
          setEmail("");
          setPassword("");
          setConfirmPassword("");
          setName("");
        } else {
          toast.error(result.detail || "Registration failed");
        }
      }
      if (mode === "login") {
        const result = await dispatch(loginUser({ email, password })).unwrap();
        if (result.access_token) {
          Cookies.set("access_token", result.access_token);
          toast.success("Signed in successfully!");
          onAuthed(email);
        }
      }
    } catch (error) {
      console.error("Authentication failed:", error);
      showErrorToast(error, "Authentication failed");
    }
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center px-4 py-10">
      <div className="ambient-bg" />

      <div className="grid w-full max-w-5xl grid-cols-1 overflow-hidden rounded-3xl glass shadow-card lg:grid-cols-2 animate-float-up">
        {/* Sidebar banner */}
        <div className="relative hidden flex-col justify-between bg-aura p-10 lg:flex">
          <CogniLogo size={42} withWordmark />

          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card/40 px-3 py-1 text-xs font-medium text-foreground/90">
              <Sparkles size={12} className="text-primary" /> AI-Powered Scheduling
            </div>
            <h2 className="text-4xl font-bold leading-tight">
              AI-Powered <span className="text-gradient-primary">Personal Time</span> Optimization
            </h2>
            <p className="text-sm text-white/70 leading-relaxed">
              CogniPlan learns your rhythm and auto-blocks deep work — so your calendar finally works for you.
            </p>
            <ul className="space-y-4 text-sm">
              {[
                { Icon: Brain, t: "Adaptive focus & energy mapping" },
                { Icon: Calendar, t: "Smart scheduling & time-blocking in seconds" },
                { Icon: CheckCircle2, t: "Smart conflict resolution & reminders" },
              ].map(({ Icon, t }) => (
                <li key={t} className="flex items-center gap-3 text-white/90 font-medium"> { }
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10 ring-1 ring-white/15"> { }
                    <Icon size={15} className="text-white" /> { }
                  </span>
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-white/40 font-medium">© 2026 CogniPlan — Plan smarter, live better.</p>
        </div>

        {/* Form panel */}
        <div className="bg-card/40 p-8 sm:p-10">
          <div className="mb-6 flex items-center justify-between lg:hidden">
            <CogniLogo size={32} withWordmark />
          </div>

          {/* Toggle */}
          <div className="mb-7 inline-flex rounded-full border border-border bg-input p-1">
            {(["login", "register"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`relative rounded-full px-5 py-1.5 text-xs font-semibold uppercase tracking-wider transition-all ${mode === m
                  ? "bg-gradient-primary text-primary-foreground shadow-glow"
                  : "text-muted-foreground hover:text-foreground"
                  }`}
              >
                {m === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>

          <h1 className="text-2xl font-bold sm:text-3xl">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {mode === "login"
              ? "Sign in to continue optimizing your day."
              : "Join thousands planning smarter with AI."}
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {mode === "register" && (
              <Field icon={User} label="Username">
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  type="text"
                  placeholder="Alex Rivera"
                  className="input-bare"
                />
              </Field>
            )}

            <Field icon={Mail} label="Email">
              <input
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="you@cogniplan.ai"
                className="input-bare"
              />
            </Field>

            <Field icon={Lock} label="Password">
              <input
                required
                type={showPw ? "text" : "password"}
                placeholder="••••••••"
                className="input-bare"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPw((s) => !s)}
                className="text-muted-foreground transition-colors hover:text-foreground"
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </Field>

            {mode === "register" && (
              <Field icon={Lock} label="Confirm Password">
                <input required type="password" placeholder="••••••••" className="input-bare" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
              </Field>
            )}

            {mode === "login" ? (
              <div className="flex items-center justify-between text-xs">
                <label className="flex items-center gap-2 text-muted-foreground">
                  <input type="checkbox" className="accent-[oklch(0.78_0.18_195)]" /> Remember me
                </label>
                <a href="#" className="font-medium text-primary hover:underline">
                  Forgot password?
                </a>
              </div>
            ) : (
              <label className="flex items-start gap-2 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  required
                  checked={agree}
                  onChange={(e) => setAgree(e.target.checked)}
                  className="mt-0.5 accent-[oklch(0.78_0.18_195)]"
                />
                <span>
                  I agree to the{" "}
                  <a href="#" className="text-primary hover:underline">Terms of Service</a> and{" "}
                  <a href="#" className="text-primary hover:underline">Privacy Policy</a>.
                </span>
              </label>
            )}

            <button
              type="submit"
              className="group relative mt-2 flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-glow transition-transform hover:scale-[1.01] active:scale-[0.99]"
            >
              {mode === "login" ? "Sign In" : "Create Account"}
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
            </button>

            <div className="relative my-5 text-center">
              <span className="relative z-10 bg-card/40 px-3 text-[11px] uppercase tracking-widest text-muted-foreground">
                or continue with
              </span>
              <div className="absolute left-0 right-0 top-1/2 -z-0 h-px bg-border" />
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-border bg-input/60 px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-input"
            >
              <GoogleIcon /> Continue with Google
            </button>

            <p className="pt-2 text-center text-xs text-muted-foreground">
              {mode === "login" ? "New to CogniPlan?" : "Already a member?"}{" "}
              <button
                type="button"
                onClick={() => setMode(mode === "login" ? "register" : "login")}
                className="font-semibold text-primary hover:underline"
              >
                {mode === "login" ? "Create an account" : "Sign in instead"}
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}

function Field({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div className="flex items-center gap-3 rounded-xl border border-border bg-input/60 px-3.5 py-2.5 transition-all focus-within:border-primary focus-within:shadow-[0_0_0_3px_oklch(0.78_0.18_195_/_0.15)]">
        <Icon size={16} className="text-muted-foreground" />
        {children}
      </div>
      <style>{`.input-bare{flex:1;background:transparent;outline:none;border:none;color:inherit;font-size:14px;}.input-bare::placeholder{color:oklch(0.55 0.03 250);}`}</style>
    </label>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 48 48">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 35.5 24 35.5c-6.4 0-11.5-5.1-11.5-11.5S17.6 12.5 24 12.5c2.9 0 5.6 1.1 7.6 2.9l5.7-5.7C33.6 6.3 29 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.3-.3-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c2.9 0 5.6 1.1 7.6 2.9l5.7-5.7C33.6 6.8 29 5 24 5 16.3 5 9.6 9 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 43c4.9 0 9.4-1.9 12.8-5l-5.9-5c-2 1.4-4.4 2.2-6.9 2.2-5.3 0-9.7-3.4-11.3-8.1l-6.5 5C9.5 38.9 16.2 43 24 43z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l5.9 5C40.9 35.4 44 30.1 44 24c0-1.2-.1-2.3-.4-3.5z" />
    </svg>
  );
}
