import { useEffect, useRef, useState } from "react";
import {
  Bell, Search, Plus, CalendarDays, Users, Brain, Sparkles, Zap,
  TrendingUp, Send, LogOut, Settings, MoreHorizontal,
  LayoutDashboard, ListTodo, MessageSquare, PanelRightClose, PanelRightOpen,
  AlarmClock, Clock, Coffee, Plane, CheckCircle2, XCircle, Loader2,
  MapPin, BookOpen, Tag, ListChecks, CalendarRange, TimerReset,
} from "lucide-react";
import { CogniLogo } from "./CogniLogo";
import { CalendarView, INITIAL_BLOCKS, type Block, type Category, type Priority } from "./CalendarView";
// GroupsView has been removed
import { getTasks, createTask, updateTask } from "../api/tasks";
import { showErrorToast } from "../utils/errors";
import { getConversations, createConversation, getMessages, sendMessage } from "../api/conversations";
import { CreateTaskModal } from "./CreateTaskModal";
import { TasksView } from "./TasksView";
import { toast } from "sonner";

type Workspace = "calendar" | "tasks";

function getStartOfWeek(date: Date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d.setDate(diff));
  monday.setHours(0, 0, 0, 0);
  return monday;
}

function formatDateString(d: Date) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function Dashboard({ name, onLogout }: { name: string; onLogout: () => void }) {
  const [weekStart, setWeekStart] = useState<Date>(() => getStartOfWeek(new Date()));
  const [prompt, setPrompt] = useState("");
  const [aiOpen, setAiOpen] = useState(true);
  const [workspace, setWorkspace] = useState<Workspace>("calendar");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string }[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  const [dbTasks, setDbTasks] = useState<any[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState<any>(null);
  const [flashIds, setFlashIds] = useState<Set<number>>(new Set());
  const [pulseIds, setPulseIds] = useState<Set<number>>(new Set());

  const [agentState, setAgentState] = useState<"idle" | "processing">("idle");

  const fetchTasks = async () => {
    try {
      const startStr = formatDateString(weekStart);
      const end = new Date(weekStart.getTime() + 7 * 24 * 60 * 60 * 1000);
      const endStr = formatDateString(end);
      const res = await getTasks(startStr, endStr);
      if (res.status === 200 && res.tasks) {
        const allTasks: any[] = [];
        Object.values(res.tasks).forEach((dayTasks: any) => {
          allTasks.push(...dayTasks);
        });
        setDbTasks(allTasks);

        if (taskToEdit) {
          const freshTask = allTasks.find(t => (t.task_id || t.id) === (taskToEdit.task_id || taskToEdit.id));
          if (freshTask) {
            setTaskToEdit(freshTask);
          }
        }
      }
    } catch (error) {
      console.error("Error fetching tasks:", error);
    }
  };

  const initConversation = async () => {
    try {
      const res = await getConversations();
      let convId = null;
      if (res.status === 200 && res.conversations && res.conversations.length > 0) {
        convId = res.conversations[0].conversation_id;
      } else {
        const newConv = await createConversation("My Focus Session");
        if (newConv.status === 200) {
          convId = newConv.conversation_id;
        }
      }

      if (convId) {
        setActiveConvId(convId);
        const msgRes = await getMessages(convId);
        if (msgRes.status === 200 && msgRes.messages && msgRes.messages.length > 0) {
          const history = msgRes.messages.map((m: any) => ({
            role: m.role === "assistant" ? ("ai" as const) : ("user" as const),
            text: m.content || "",
          }));
          setMessages(history);
        } else {
          setMessages([
            { role: "ai", text: `Hi ${name} 👋 Try asking me to schedule a study block or gym session.` }
          ]);
        }
      }
    } catch (err) {
      console.error("Failed to initialize conversation:", err);
    }
  };

  useEffect(() => {
    if (name) {
      initConversation();
    }
  }, [name]);

  useEffect(() => {
    if (name) {
      fetchTasks();
    }
  }, [name, weekStart]);

  const mapTasksToBlocks = (tasksList: any[]): Block[] => {
    const parsed = tasksList.map((t) => {
      const startDate = new Date(t.start_time);
      const mytStartTime = startDate.getTime() + (startDate.getTimezoneOffset() + 480) * 60 * 1000;
      const sDate = new Date(mytStartTime);

      const endDate = new Date(t.end_time);
      const mytEndTime = endDate.getTime() + (endDate.getTimezoneOffset() + 480) * 60 * 1000;
      const eDate = new Date(mytEndTime);

      const targetMidnight = new Date(sDate.getFullYear(), sDate.getMonth(), sDate.getDate()).getTime();
      const wsMidnight = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate()).getTime();
      const msDiff = targetMidnight - wsMidnight;
      let dayIndex = Math.round(msDiff / (24 * 60 * 60 * 1000));
      if (dayIndex < 0 || dayIndex > 6) {
        dayIndex = 0; // fallback safety
      }

      const startHour = sDate.getHours() + sDate.getMinutes() / 60;
      const endHour = eDate.getHours() + eDate.getMinutes() / 60;

      return {
        id: t.task_id || t.id || Math.random(),
        title: t.title,
        day: dayIndex,
        start: startHour,
        end: endHour,
        category: (t.category || "Work") as Category,
        priority: (t.priority || "low") as Priority,
        focus: t.status === "focus",
        rawStart: startDate.getTime(),
        rawEnd: endDate.getTime(),
      };
    });

    // Detect conflicts (overlapping time slots) on the fly
    return parsed.map((b1) => {
      const hasConflict = parsed.some((b2) => {
        if (b1.id === b2.id) return false;
        // Two tasks conflict if they overlap
        return b1.rawStart < b2.rawEnd && b1.rawEnd > b2.rawStart;
      });
      return {
        id: b1.id,
        title: b1.title,
        day: b1.day,
        start: b1.start,
        end: b1.end,
        category: b1.category,
        priority: b1.priority,
        focus: b1.focus,
        hasConflict,
      };
    });
  };

  const blocks = mapTasksToBlocks(dbTasks);

  const focusHours = dbTasks
    .filter((t) => (t.category === "Focus" || t.status === "focus") && t.start_time && t.end_time)
    .reduce((acc, t) => {
      const start = new Date(t.start_time).getTime();
      const end = new Date(t.end_time).getTime();
      if (isNaN(start) || isNaN(end)) return acc;
      return acc + Math.max(0, (end - start) / (1000 * 60 * 60));
    }, 0);

  const sendPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !activeConvId) return;
    const userMsg = prompt.trim();
    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setPrompt("");
    setAgentState("processing");

    try {
      const res = await sendMessage(activeConvId, userMsg);
      if (res.status === 200 && res.assistant_message) {
        setMessages((m) => [
          ...m,
          { role: "ai", text: res.assistant_message.content || "" },
        ]);
        await fetchTasks();
      }
    } catch (error) {
      console.error("Failed to send message to AI Agent:", error);
      toast.error("Failed to receive response from AI Agent");
    } finally {
      setAgentState("idle");
    }
  };

  const handleBlockMove = async (
    blockId: string | number,
    dayIndex: number,
    startHour: number,
    endHour: number
  ) => {
    const targetTask = dbTasks.find((t) => (t.task_id || t.id) === blockId);
    if (!targetTask) return;

    const targetDate = new Date(weekStart.getTime());
    targetDate.setDate(targetDate.getDate() + dayIndex);

    const formatTimeOffset = (date: Date, decimalHour: number) => {
      const target = new Date(date.getTime());
      let hours = Math.floor(decimalHour);
      let minutes = Math.round((decimalHour - hours) * 60);
      if (minutes >= 60) {
        hours += 1;
        minutes -= 60;
      }
      if (hours >= 24) {
        target.setDate(target.getDate() + Math.floor(hours / 24));
        hours = hours % 24;
      }
      const yyyy = target.getFullYear();
      const mm = String(target.getMonth() + 1).padStart(2, "0");
      const dd = String(target.getDate()).padStart(2, "0");
      const hh = String(hours).padStart(2, "0");
      const minStr = String(minutes).padStart(2, "0");
      return `${yyyy}-${mm}-${dd}T${hh}:${minStr}:00+08:00`;
    };

    const newStartISO = formatTimeOffset(targetDate, startHour);
    const newEndISO = formatTimeOffset(targetDate, endHour);

    const taskPayload = {
      title: targetTask.title,
      description: targetTask.description,
      priority: targetTask.priority,
      category: targetTask.category,
      location: targetTask.location,
      link: targetTask.link,
      start_time: newStartISO,
      end_time: newEndISO,
      reminder: targetTask.reminder,
      status: targetTask.status,
    };

    const previousTasks = [...dbTasks];

    // Optimistically update the UI tasks state
    setDbTasks((prev) =>
      prev.map((t) =>
        (t.task_id || t.id) === blockId
          ? { ...t, start_time: newStartISO, end_time: newEndISO }
          : t
      )
    );

    try {
      const result = await updateTask(String(blockId), taskPayload);
      if (result.status_code === 400 && result.detail !== "Time conflict") {
        toast.error(result.detail || "Failed to reschedule task");
        setDbTasks(previousTasks);
        return;
      }
      toast.success("Task rescheduled successfully!");
      // Refetch to sync clean details and recheck conflicts
      fetchTasks();
    } catch (err: any) {
      setDbTasks(previousTasks);
      console.error(err);
      showErrorToast(err, "Failed to reschedule task");
    }
  };

  return (
    <div className="fixed inset-0 h-screen w-screen overflow-hidden flex flex-col text-foreground select-none"> { }
      <div className="ambient-bg" />

      {/* Top bar */}
      <header className="w-full shrink-0 border-b border-border bg-[#0d0f14] shadow-[0_4px_30px_rgba(0,0,0,0.5)] z-50"> { }
        <div className="flex items-center gap-4 px-6 py-3">
          <CogniLogo size={32} withWordmark />
          <nav className="ml-8 hidden items-center gap-1 md:flex">
            {[
              { Icon: CalendarDays, label: "Calendar", ws: "calendar" as const },
              { Icon: ListTodo, label: "Tasks", ws: "tasks" as const },
            ].map(({ Icon, label, ws }) => {
              const active = workspace === ws;
              return (
                <button
                  key={label}
                  onClick={() => setWorkspace(ws)}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors ${active
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
          <LeftPanel name={name} dbTasks={dbTasks} onNewPlan={() => { setTaskToEdit(null); setIsCreateModalOpen(true); }} />
        </aside>

        <main className="min-w-0 flex-1">
          {workspace === "calendar" ? (
            <CalendarView
              blocks={blocks}
              flashIds={flashIds}
              pulseIds={pulseIds}
              weekStart={weekStart}
              onWeekChange={(d) => setWeekStart(d)}
              onNewPlan={() => { setTaskToEdit(null); setIsCreateModalOpen(true); }}
              onBlockClick={(id) => {
                const targetTask = dbTasks.find((t) => (t.task_id || t.id) === id);
                if (targetTask) {
                  setTaskToEdit(targetTask);
                  setIsCreateModalOpen(true);
                }
              }}
              onBlockMove={handleBlockMove}
            />
          ) : (
            <TasksView
              tasks={dbTasks}
              weekStart={weekStart}
              onWeekChange={setWeekStart}
              onOpenCreateModal={() => { setTaskToEdit(null); setIsCreateModalOpen(true); }}
              onEditTask={(task) => {
                setTaskToEdit(task);
                setIsCreateModalOpen(true);
              }}
            />
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
                    {agentState === "processing" ? "Processing prompt…" : "Online · learning rhythm"}
                  </p>
                </div>
              </div>
              <button onClick={() => setAiOpen(false)} className="text-muted-foreground hover:text-foreground">
                <PanelRightClose size={15} />
              </button>
            </div>

            <div className="mb-3 grid grid-cols-2 gap-2">
              <MiniStat Icon={Zap} label="Focus" value={`${focusHours.toFixed(1)}h`} />
              <MiniStat Icon={TrendingUp} label="Energy" value="86" />
            </div>

            {/* Scrollable middle: processing + chat */}
            <div className="mb-3 flex-1 space-y-3 overflow-y-auto pr-1">
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

              {/* Chat history */}
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`max-w-[92%] rounded-2xl px-3 py-2 text-xs ${m.role === "ai" ? "bg-card text-foreground" : "ml-auto bg-gradient-primary text-primary-foreground"
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

      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => { setIsCreateModalOpen(false); setTaskToEdit(null); }}
        onTaskCreated={(taskDate) => {
          if (taskDate) {
            const taskWeekStart = getStartOfWeek(taskDate);
            if (taskWeekStart.getTime() !== weekStart.getTime()) {
              setWeekStart(taskWeekStart);
              return;
            }
          }
          fetchTasks();
        }}
        taskToEdit={taskToEdit}
        weekStart={weekStart}
      />
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

function LeftPanel({ name, dbTasks = [], onNewPlan }: { name: string; dbTasks?: any[]; onNewPlan?: () => void }) {
  const reminders = dbTasks
    .filter((t) => t.reminder && t.start_time)
    .map((t) => {
      const startTime = new Date(t.start_time);
      const mytStartTime = startTime.getTime() + (startTime.getTimezoneOffset() + 480) * 60 * 1000;
      const sDate = new Date(mytStartTime);
      const timeStr = sDate.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
      const dayStr = sDate.toLocaleDateString("en-US", { weekday: "short" });
      return {
        Icon: AlarmClock,
        title: t.title,
        time: `${dayStr} ${timeStr}`,
        tone: (t.priority === "high" ? "primary" : t.priority === "med" ? "accent" : "muted") as "primary" | "accent" | "muted",
      };
    });

  const notifications = [...dbTasks]
    .sort((a, b) => new Date(b.created_at || b.start_time).getTime() - new Date(a.created_at || a.start_time).getTime())
    .slice(0, 3)
    .map((t) => {
      const collaborators = t.users || [];
      const who = collaborators.length > 1 ? collaborators[collaborators.length - 1].name || "Squad" : "AI";
      return {
        who,
        text: `scheduled block "${t.title}"`,
        t: "Recent",
      };
    });

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="glass rounded-2xl p-4">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Focus Workspace</p>
        <h1 className="mt-1 text-lg font-semibold leading-tight">
          Hi <span className="text-gradient-primary">{name}</span>
        </h1>
        <p className="mt-1 text-[11px] text-muted-foreground">{dbTasks.length} plan blocks scheduled</p>
        <button onClick={onNewPlan} className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow">
          <Plus size={12} /> New Plan
        </button>
      </div>

      <div className="glass rounded-2xl p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reminders</h3>
          <MoreHorizontal size={14} className="text-muted-foreground" />
        </div>
        <ul className="space-y-2">
          {reminders.length === 0 ? (
            <div className="text-center py-4 text-xs text-muted-foreground">
              No active reminders
            </div>
          ) : (
            reminders.map((r, i) => (
              <li key={i} className="group flex items-start gap-2.5 rounded-lg border border-transparent bg-card/40 p-2 hover:border-border">
                <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-md ${r.tone === "primary" ? "bg-primary/15 text-primary" :
                    r.tone === "accent" ? "bg-accent/15 text-accent" : "bg-muted text-muted-foreground"
                  }`}>
                  <r.Icon size={13} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-[12px] font-medium">{r.title}</p>
                  <p className="text-[10px] text-muted-foreground">{r.time}</p>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>

      <div className="glass flex-1 rounded-2xl p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Activity</h3>
        <ul className="space-y-3">
          {notifications.length === 0 ? (
            <div className="text-center py-4 text-xs text-muted-foreground">
              No recent activity
            </div>
          ) : (
            notifications.map((n, i) => (
              <li key={i} className="flex gap-2.5 text-[11px]">
                <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-gradient-primary text-[10px] font-bold text-primary-foreground">
                  {n.who.charAt(0)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="leading-snug"><span className="font-semibold">{n.who}</span> <span className="text-muted-foreground">{n.text}</span></p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground">{n.t}</p>
                </div>
              </li>
            ))
          )}
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
