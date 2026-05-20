import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Plus, Timer, Flame } from "lucide-react";

type View = "day" | "3day" | "week";
export type Priority = "high" | "med" | "low";
export type Category = "Study" | "Travel" | "Personal" | "Social" | "Focus" | "Work";

export type Block = {
  id: number;
  title: string;
  day: number;
  start: number;
  end: number;
  category: Category;
  priority: Priority;
  focus?: boolean;
};

const CATEGORY_STYLE: Record<Category, string> = {
  Study: "bg-primary/15 border-primary/40 text-primary",
  Travel: "bg-amber-500/15 border-amber-500/40 text-amber-300",
  Personal: "bg-emerald-500/15 border-emerald-500/40 text-emerald-300",
  Social: "bg-accent/15 border-accent/40 text-accent",
  Focus: "bg-cyan-400/15 border-cyan-400/50 text-cyan-200",
  Work: "bg-indigo-400/15 border-indigo-400/40 text-indigo-200",
};

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_NUMS = [11, 12, 13, 14, 15, 16, 17];

const HOURS = Array.from({ length: 14 }, (_, i) => 7 + i);
const HOUR_PX = 56;

export const INITIAL_BLOCKS: Block[] = [
  { id: 1, title: "Deep Work — Strategy", day: 3, start: 9, end: 11, category: "Work", priority: "high" },
  { id: 2, title: "Pomodoro · Reading", day: 3, start: 8, end: 8.42, category: "Focus", priority: "med", focus: true },
  { id: 3, title: "Design Sync", day: 3, start: 11.5, end: 12, category: "Social", priority: "med" },
  { id: 4, title: "Lunch + Walk", day: 3, start: 12.5, end: 13.25, category: "Personal", priority: "low" },
  { id: 5, title: "ML Study Block", day: 3, start: 14, end: 15.5, category: "Study", priority: "high" },
  { id: 6, title: "Commute", day: 3, start: 17, end: 17.75, category: "Travel", priority: "low" },
  { id: 7, title: "Pomodoro · Notes", day: 4, start: 9, end: 9.42, category: "Focus", priority: "med", focus: true },
  { id: 8, title: "Stand-up", day: 4, start: 10, end: 10.5, category: "Work", priority: "med" },
  { id: 9, title: "Gym", day: 4, start: 18, end: 19, category: "Personal", priority: "med" },
  { id: 10, title: "Team Lunch", day: 2, start: 12, end: 13, category: "Social", priority: "low" },
  { id: 11, title: "Client Call", day: 2, start: 15, end: 16, category: "Work", priority: "high" },
  { id: 12, title: "Flight to NYC", day: 5, start: 8, end: 11, category: "Travel", priority: "high" },
  { id: 13, title: "Pomodoro · Code", day: 1, start: 10, end: 10.42, category: "Focus", priority: "med", focus: true },
  { id: 14, title: "Yoga", day: 0, start: 7.5, end: 8.5, category: "Personal", priority: "low" },
  { id: 15, title: "Conference Prep", day: 6, start: 16, end: 18, category: "Study", priority: "med" },
];

export function CalendarView({
  blocks = INITIAL_BLOCKS,
  flashIds = new Set<number>(),
  pulseIds = new Set<number>(),
}: {
  blocks?: Block[];
  flashIds?: Set<number>;
  pulseIds?: Set<number>;
}) {
  const [view, setView] = useState<View>("week");
  const [anchor, setAnchor] = useState(3);

  const visibleDays = useMemo(() => {
    if (view === "week") return [0, 1, 2, 3, 4, 5, 6];
    if (view === "3day") return [anchor, (anchor + 1) % 7, (anchor + 2) % 7];
    return [anchor];
  }, [view, anchor]);

  const shift = (d: number) => {
    if (view === "week") return;
    setAnchor((a) => Math.min(6, Math.max(0, a + d)));
  };

  return (
    <section className="glass flex h-full flex-col rounded-2xl p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">May 2026</h2>
          <p className="text-xs text-muted-foreground">
            Week 20 · {visibleDays.length} {visibleDays.length === 1 ? "day" : "days"} ·{" "}
            <span className="text-primary">Focus protected</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-border bg-card/60 p-0.5">
            {(["day", "3day", "week"] as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-md px-3 py-1 text-xs font-medium capitalize transition-colors ${
                  view === v ? "bg-gradient-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {v === "3day" ? "3-Day" : v}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card/60 p-0.5">
            <button onClick={() => shift(-1)} className="rounded p-1 text-muted-foreground hover:bg-card hover:text-foreground">
              <ChevronLeft size={14} />
            </button>
            <button onClick={() => shift(1)} className="rounded p-1 text-muted-foreground hover:bg-card hover:text-foreground">
              <ChevronRight size={14} />
            </button>
          </div>
          <button className="flex items-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow">
            <Plus size={13} /> Block
          </button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {(["Study", "Work", "Social", "Personal", "Travel", "Focus"] as Category[]).map((c) => (
          <span key={c} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] uppercase tracking-wider ${CATEGORY_STYLE[c]}`}>
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {c}
          </span>
        ))}
      </div>

      <div className="flex-1 overflow-auto rounded-xl border border-border bg-background/30">
        <div className="flex min-w-fit">
          <div className="sticky left-0 z-10 w-14 shrink-0 border-r border-border bg-background/60 backdrop-blur">
            <div className="h-10 border-b border-border" />
            {HOURS.map((h) => (
              <div key={h} style={{ height: HOUR_PX }} className="relative border-b border-border/60">
                <span className="absolute -top-2 right-2 text-[10px] text-muted-foreground">
                  {h > 12 ? h - 12 : h}{h >= 12 ? "p" : "a"}
                </span>
              </div>
            ))}
          </div>

          <div className="grid flex-1" style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(140px, 1fr))` }}>
            {visibleDays.map((d) => {
              const dayBlocks = blocks.filter((b) => b.day === d);
              const isToday = d === 3;
              return (
                <div key={d} className="relative border-r border-border/60 last:border-r-0">
                  <div className={`sticky top-0 z-10 flex h-10 items-center justify-center gap-2 border-b border-border backdrop-blur ${isToday ? "bg-primary/10" : "bg-background/60"}`}>
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{DAY_LABELS[d]}</span>
                    <span className={`text-sm font-semibold ${isToday ? "text-primary" : ""}`}>{DAY_NUMS[d]}</span>
                  </div>

                  <div className="relative" style={{ height: HOURS.length * HOUR_PX }}>
                    {HOURS.map((h) => (
                      <div key={h} style={{ height: HOUR_PX }} className="border-b border-border/40" />
                    ))}

                    {isToday && (
                      <div className="pointer-events-none absolute left-0 right-0 z-20" style={{ top: (10.5 - HOURS[0]) * HOUR_PX }}>
                        <div className="flex items-center">
                          <span className="-ml-1 h-2 w-2 rounded-full bg-primary shadow-glow" />
                          <span className="h-px flex-1 bg-primary/70" />
                        </div>
                      </div>
                    )}

                    {dayBlocks.map((b) => {
                      const top = (b.start - HOURS[0]) * HOUR_PX;
                      const height = Math.max(28, (b.end - b.start) * HOUR_PX);
                      const isHigh = b.priority === "high";
                      const isFlashing = flashIds.has(b.id);
                      const isPulse = pulseIds.has(b.id);
                      return (
                        <button
                          key={b.id}
                          style={{ top, height, transition: "top 600ms cubic-bezier(.2,.8,.2,1), height 600ms" }}
                          className={`group absolute left-1 right-1 overflow-hidden rounded-lg border px-2 py-1.5 text-left text-[11px] hover:z-10 hover:scale-[1.02] ${CATEGORY_STYLE[b.category]} ${
                            isHigh ? "ring-1 ring-current shadow-[0_0_18px_-2px_currentColor]" : ""
                          } ${b.focus ? "border-dashed" : ""} ${isFlashing ? "animate-pulse ring-2 ring-amber-400" : ""} ${isPulse ? "ring-2 ring-primary animate-pulse" : ""}`}
                        >
                          <div className="flex items-center gap-1 font-semibold">
                            {b.focus && <Timer size={10} />}
                            {isHigh && !b.focus && <Flame size={10} />}
                            <span className="truncate">{b.title}</span>
                          </div>
                          <div className="mt-0.5 text-[10px] opacity-80">
                            {fmt(b.start)} – {fmt(b.end)}
                          </div>
                          {b.focus && (
                            <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-current/20">
                              <div className="h-full w-2/5 bg-current" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function fmt(h: number) {
  const hr = Math.floor(h);
  const m = Math.round((h - hr) * 60);
  const ampm = hr >= 12 ? "pm" : "am";
  const hh = hr > 12 ? hr - 12 : hr === 0 ? 12 : hr;
  return `${hh}:${m.toString().padStart(2, "0")}${ampm}`;
}
