import { useEffect, useRef, useState } from "react";
import {
  Bell, Search, Plus, CalendarDays, Users, Brain, Sparkles, Zap,
  TrendingUp, Send, LogOut, Settings, MoreHorizontal,
  LayoutDashboard, ListTodo, MessageSquare, PanelRightClose, PanelRightOpen,
  AlarmClock, Clock, Coffee, Plane, CheckCircle2, XCircle, Loader2,
  MapPin, BookOpen, Tag, ListChecks, CalendarRange, TimerReset,
} from "lucide-react";
import { CogniLogo } from "./CogniLogo";
import { CalendarView, INITIAL_BLOCKS, type Block } from "./CalendarView";
import { GroupsView } from "./GroupsView";

type Workspace = "calendar" | "groups";

type Proposal = {
  title: string;
  tags: string[];
  location: string;
  subtasks: string[];
  slots: { day: string; time: string }[];
};

const FYP_PROPOSAL: Proposal = {
  title: "Research FYP Problem Statement",
  tags: ["Study", "Academic"],
  location: "Library / Remote",
  subtasks: [
    "Research 5 papers a day (1 hour)",
    "Draft problem statement outline",
  ],
  slots: [
    { day: "Mon", time: "10:00 – 11:00" },
    { day: "Tue", time: "10:00 – 11:00" },
    { day: "Wed", time: "14:00 – 15:00" },
    { day: "Thu", time: "10:00 – 11:00" },
    { day: "Fri", time: "09:00 – 10:00" },
  ],
};

export function Dashboard({ name, onLogout }: { name: string; onLogout: () => void }) {
  const [prompt, setPrompt] = useState("");
  const [aiOpen, setAiOpen] = useState(true);
  const [workspace, setWorkspace] = useState<Workspace>("calendar");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string }[]>([
    { role: "ai", text: `Hi ${name} 👋 Try "Plan my FYP" and I'll structure it across your free slots.` },
  ]);

  const [blocks, setBlocks] = useState<Block[]>(INITIAL_BLOCKS);
  const [flashIds, setFlashIds] = useState<Set<number>>(new Set());
  const [pulseIds, setPulseIds] = useState<Set<number>>(new Set());

  // Agent state machine
  const [agentState, setAgentState] = useState<"idle" | "processing" | "proposal" | "approved" | "rejected">("idle");
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const runAgent = (userText: string) => {
    setAgentState("processing");
    setProposal(null);
    timer.current = setTimeout(() => {
      setProposal(FYP_PROPOSAL);
      setAgentState("proposal");
      setMessages((m) => [...m, { role: "ai", text: `I parsed "${userText}" into 2 subtasks and reserved 5 weekday slots. Review the proposal →` }]);
    }, 1400);
  };

  const sendPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    const userMsg = prompt.trim();
    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setPrompt("");
    runAgent(userMsg);
  };

  const approveProposal = () => {
    if (!proposal) return;
    const dayMap: Record<string, number> = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };
    let nextId = Math.max(...blocks.map((b) => b.id)) + 1;
    const newBlocks: Block[] = proposal.slots.map((s) => {
      const [startStr, endStr] = s.time.split(" – ");
      const toH = (t: string) => {
        const [hh, mm] = t.split(":").map(Number);
        return hh + mm / 60;
      };
      return {
        id: nextId++,
        title: proposal.title,
        day: dayMap[s.day] ?? 0,
        start: toH(startStr),
        end: toH(endStr),
        category: "Study",
        priority: "high",
      };
    });
    const ids = new Set(newBlocks.map((b) => b.id));
    setBlocks((b) => [...b, ...newBlocks]);
    setPulseIds(ids);
    setAgentState("approved");
    setMessages((m) => [...m, { role: "ai", text: "✅ Schedule approved and added to your calendar." }]);
    setTimeout(() => setPulseIds(new Set()), 2200);
  };

  const rejectProposal = () => {
    setAgentState("rejected");
    setMessages((m) => [...m, { role: "ai", text: "Got it — discarded. Want me to retry with tighter slots?" }]);
  };

  const delayFiveMin = () => {
    // Shift low/med blocks down by 5 minutes; high stays locked. Flash all shifted.
    const shifted = new Set<number>();
    setBlocks((bs) =>
      bs.map((b) => {
        if (b.priority === "high") return b;
        shifted.add(b.id);
        return { ...b, start: b.start + 5 / 60, end: b.end + 5 / 60 };
      })
    );
    setFlashIds(shifted);
    setMessages((m) => [...m, { role: "ai", text: "⏳ Dynamic reschedule: shifted low/med items by 5 min. High-priority blocks locked." }]);
    setTimeout(() => setFlashIds(new Set()), 1800);
  };

  return (
    <div className="relative min-h-screen text-foreground">
      <div className="ambient-bg" />

      {/* Top bar */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/70 backdrop-blur-xl">
        <div className="flex items-center gap-4 px-6 py-3">
          <CogniLogo size={32} withWordmark />
          <nav className="ml-8 hidden items-center gap-1 md:flex">
            {[
              { Icon: LayoutDashboard, label: "Overview", ws: null },
              { Icon: CalendarDays, label: "Calendar", ws: "calendar" as const },
              { Icon: ListTodo, label: "Tasks", ws: null },
              { Icon: Users, label: "Groups", ws: "groups" as const },
            ].map(({ Icon, label, ws }) => {
              const active = ws !== null && workspace === ws;
              return (
                <button
                  key={label}
                  onClick={() => ws && setWorkspace(ws)}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "bg-card text-foreground ring-1 ring-border"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon size={15} /> {label}
                </button>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-lg border border-border bg-input/60 px-3 py-1.5 text-sm sm:flex">
              <Search size={14} className="text-muted-foreground" />
              <input
                placeholder="Search or ask AI…"
                className="w-56 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
              <kbd className="hidden rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground md:inline">⌘K</kbd>
            </div>
            <IconBtn><Bell size={16} /></IconBtn>
            <IconBtn><Settings size={16} /></IconBtn>
            <button
              onClick={() => setAiOpen((v) => !v)}
              className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground transition-colors hover:bg-card hover:text-foreground"
              title={aiOpen ? "Hide AI panel" : "Show AI panel"}
            >
              {aiOpen ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
            </button>
            <div className="ml-1 flex items-center gap-2 rounded-full border border-border bg-card pl-1 pr-3">
              <div className="grid h-7 w-7 place-items-center rounded-full bg-gradient-primary text-xs font-bold text-primary-foreground">
                {name.charAt(0).toUpperCase()}
              </div>
              <span className="hidden text-sm font-medium sm:inline">{name}</span>
              <button onClick={onLogout} className="text-muted-foreground transition-colors hover:text-foreground">
                <LogOut size={14} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex gap-4 px-4 py-4" style={{ height: "calc(100vh - 65px)" }}>
        <aside className="hidden w-64 shrink-0 overflow-y-auto lg:block">
          <LeftPanel name={name} />
        </aside>

        <main className="min-w-0 flex-1">
          {workspace === "calendar" ? (
            <CalendarView blocks={blocks} flashIds={flashIds} pulseIds={pulseIds} />
          ) : (
            <GroupsView />
          )}
        </main>

        <aside className={`shrink-0 overflow-hidden transition-all duration-300 ${aiOpen ? "w-[360px]" : "w-0"}`}>
          <div className="glass flex h-full flex-col rounded-2xl p-5">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary shadow-glow">
                  <Brain size={16} className="text-primary-foreground" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold">AI Agent Panel</h2>
                  <p className="text-[10px] text-muted-foreground">
                    <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${agentState === "processing" ? "bg-amber-400 animate-pulse" : "bg-primary"}`} />
                    {agentState === "processing" ? "Processing prompt…" : agentState === "proposal" ? "Awaiting approval" : "Online · learning rhythm"}
                  </p>
                </div>
              </div>
              <button onClick={() => setAiOpen(false)} className="text-muted-foreground hover:text-foreground">
                <PanelRightClose size={15} />
              </button>
            </div>

            <div className="mb-3 grid grid-cols-2 gap-2">
              <MiniStat Icon={Zap} label="Focus" value="4.5h" />
              <MiniStat Icon={TrendingUp} label="Energy" value="86" />
            </div>

            {/* Scrollable middle: proposal + chat */}
            <div className="mb-3 flex-1 space-y-3 overflow-y-auto pr-1">
              {/* Agent proposal card */}
              {agentState === "processing" && (
                <div className="rounded-xl border border-primary/40 bg-card/40 p-4">
                  <div className="flex items-center gap-2 text-xs">
                    <Loader2 size={14} className="animate-spin text-primary" />
                    <span className="font-semibold">Processing prompt</span>
                  </div>
                  <div className="mt-3 space-y-1.5">
                    {["Parsing intent…", "Tagging categories…", "Scanning free slots…"].map((s, i) => (
                      <div key={s} className="flex items-center gap-2 text-[11px] text-muted-foreground" style={{ animation: `pulse 1.2s ${i * 0.3}s infinite` }}>
                        <span className="h-1 w-1 rounded-full bg-primary" /> {s}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {agentState === "proposal" && proposal && (
                <div className="rounded-xl border border-primary/50 bg-card/60 p-4 shadow-glow">
                  <div className="mb-2 flex items-center gap-2">
                    <Sparkles size={13} className="text-primary" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-primary">Proposed Plan</span>
                  </div>

                  <div className="flex items-start gap-2">
                    <BookOpen size={14} className="mt-0.5 text-muted-foreground" />
                    <h3 className="text-sm font-semibold leading-snug">{proposal.title}</h3>
                  </div>

                  <Field Icon={Tag} label="Tags">
                    <div className="flex flex-wrap gap-1">
                      {proposal.tags.map((t) => (
                        <span key={t} className="rounded-full border border-primary/40 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                          {t}
                        </span>
                      ))}
                    </div>
                  </Field>

                  <Field Icon={MapPin} label="Location">
                    <p className="text-xs">{proposal.location}</p>
                  </Field>

                  <Field Icon={ListChecks} label="Subtasks">
                    <ul className="space-y-1">
                      {proposal.subtasks.map((s) => (
                        <li key={s} className="flex items-start gap-1.5 text-xs">
                          <CheckCircle2 size={11} className="mt-0.5 text-primary" /> {s}
                        </li>
                      ))}
                    </ul>
                  </Field>

                  <Field Icon={CalendarRange} label="Scheduled slots">
                    <ul className="space-y-1">
                      {proposal.slots.map((s) => (
                        <li key={s.day} className="flex items-center justify-between rounded-md border border-border/60 bg-background/40 px-2 py-1 text-[11px]">
                          <span className="font-semibold">{s.day}</span>
                          <span className="text-muted-foreground">{s.time}</span>
                        </li>
                      ))}
                    </ul>
                  </Field>

                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={approveProposal}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow-glow"
                    >
                      <CheckCircle2 size={13} /> Approve Schedule
                    </button>
                    <button
                      onClick={rejectProposal}
                      className="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
                    >
                      <XCircle size={13} /> Reject / Edit
                    </button>
                  </div>

                  <button
                    onClick={delayFiveMin}
                    className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg border border-amber-400/40 bg-amber-400/10 px-3 py-1.5 text-[11px] font-medium text-amber-300 hover:bg-amber-400/15"
                  >
                    <TimerReset size={12} /> Delay 5 min (simulate dynamic reschedule)
                  </button>
                </div>
              )}

              {(agentState === "approved" || agentState === "rejected" || agentState === "idle") && (
                <button
                  onClick={delayFiveMin}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-amber-400/30 bg-amber-400/5 px-3 py-1.5 text-[11px] font-medium text-amber-300 hover:bg-amber-400/15"
                >
                  <TimerReset size={12} /> Simulate · Delay 5 minutes
                </button>
              )}

              {/* Chat history */}
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`max-w-[92%] rounded-2xl px-3 py-2 text-xs ${
                    m.role === "ai" ? "bg-card text-foreground" : "ml-auto bg-gradient-primary text-primary-foreground"
                  }`}
                >
                  {m.text}
                </div>
              ))}
            </div>

            <div className="mb-2 flex flex-wrap gap-1.5">
              {["Plan my FYP", "Find 1h gym", "Sync team"].map((s) => (
                <button
                  key={s}
                  onClick={() => setPrompt(s)}
                  className="rounded-full border border-border bg-card/60 px-2.5 py-1 text-[10px] text-muted-foreground hover:bg-card hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>

            <form onSubmit={sendPrompt} className="flex items-center gap-2 rounded-xl border border-border bg-input/60 p-1.5 focus-within:border-primary">
              <MessageSquare size={14} className="ml-2 text-muted-foreground" />
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask CogniPlan…"
                className="flex-1 bg-transparent text-xs outline-none placeholder:text-muted-foreground"
              />
              <button type="submit" className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-primary text-primary-foreground">
                <Send size={12} />
              </button>
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Field({ Icon, label, children }: { Icon: React.ComponentType<{ size?: number; className?: string }>; label: string; children: React.ReactNode }) {
  return (
    <div className="mt-2.5">
      <div className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        <Icon size={10} /> {label}
      </div>
      {children}
    </div>
  );
}

function LeftPanel({ name }: { name: string }) {
  const reminders = [
    { Icon: AlarmClock, title: "Deep work starts soon", time: "in 12 min", tone: "primary" as const },
    { Icon: Coffee, title: "Hydration break", time: "10:45 am", tone: "muted" as const },
    { Icon: Plane, title: "Flight check-in opens", time: "Saturday 8am", tone: "accent" as const },
    { Icon: Clock, title: "Pomodoro ready", time: "Queued ×3", tone: "primary" as const },
  ];
  const notifications = [
    { who: "Lina", text: "moved design sync to 11:30", t: "2m" },
    { who: "Marcus", text: "accepted Q3 strategy invite", t: "8m" },
    { who: "AI", text: "auto-shortened your 3pm call", t: "21m" },
  ];

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="glass rounded-2xl p-4">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Sunday · May 17</p>
        <h1 className="mt-1 text-lg font-semibold leading-tight">
          Hi <span className="text-gradient-primary">{name}</span>
        </h1>
        <p className="mt-1 text-[11px] text-muted-foreground">3 AI-prioritized blocks today</p>
        <button className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow">
          <Plus size={12} /> New Plan
        </button>
      </div>

      <div className="glass rounded-2xl p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reminders</h3>
          <MoreHorizontal size={14} className="text-muted-foreground" />
        </div>
        <ul className="space-y-2">
          {reminders.map((r, i) => (
            <li key={i} className="group flex items-start gap-2.5 rounded-lg border border-transparent bg-card/40 p-2 hover:border-border">
              <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-md ${
                r.tone === "primary" ? "bg-primary/15 text-primary" :
                r.tone === "accent" ? "bg-accent/15 text-accent" : "bg-muted text-muted-foreground"
              }`}>
                <r.Icon size={13} />
              </span>
              <div className="min-w-0">
                <p className="truncate text-[12px] font-medium">{r.title}</p>
                <p className="text-[10px] text-muted-foreground">{r.time}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="glass flex-1 rounded-2xl p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Activity</h3>
        <ul className="space-y-3">
          {notifications.map((n, i) => (
            <li key={i} className="flex gap-2.5 text-[11px]">
              <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-gradient-primary text-[10px] font-bold text-primary-foreground">
                {n.who.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="leading-snug"><span className="font-semibold">{n.who}</span> <span className="text-muted-foreground">{n.text}</span></p>
                <p className="mt-0.5 text-[10px] text-muted-foreground">{n.t} ago</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function IconBtn({ children }: { children: React.ReactNode }) {
  return (
    <button className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground transition-colors hover:bg-card hover:text-foreground">
      {children}
    </button>
  );
}

function MiniStat({ Icon, label, value }: { Icon: React.ComponentType<{ size?: number; className?: string }>; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card/40 p-2.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Icon size={11} /> {label}
      </div>
      <p className="mt-1 text-lg font-bold">{value}</p>
    </div>
  );
}
