import React, { useMemo, useState, useRef } from "react";
import { ChevronLeft, ChevronRight, Plus, Timer, Flame, AlertCircle } from "lucide-react";

type View = "day" | "3day" | "week";
export type Priority = "high" | "med" | "low";
export type Category = "Study" | "Travel" | "Personal" | "Social" | "Focus" | "Work" | "Others";

export type Block = {
  id: number;
  title: string;
  day: number;
  start: number;
  end: number;
  category: Category;
  priority: Priority;
  focus?: boolean;
  hasConflict?: boolean;
};

const CATEGORY_STYLE: Record<Category, string> = {
  Study: "bg-primary/15 border-primary/40 text-primary",
  Travel: "bg-amber-500/15 border-amber-500/40 text-amber-300",
  Personal: "bg-emerald-500/15 border-emerald-500/40 text-emerald-300",
  Social: "bg-accent/15 border-accent/40 text-accent",
  Focus: "bg-cyan-400/15 border-cyan-400/50 text-cyan-200",
  Work: "bg-indigo-400/15 border-indigo-400/40 text-indigo-200",
  Others: "bg-gray-400/15 border-gray-400/40 text-gray-200",
};

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const HOUR_PX = 48;

export const INITIAL_BLOCKS: Block[] = [];

export function CalendarView({
  blocks = INITIAL_BLOCKS,
  flashIds = new Set<number>(),
  pulseIds = new Set<number>(),
  weekStart = new Date(),
  onWeekChange,
  onNewPlan,
  onBlockClick,
  onBlockMove,
}: {
  blocks?: Block[];
  flashIds?: Set<number>;
  pulseIds?: Set<number>;
  weekStart?: Date;
  onWeekChange?: (d: Date) => void;
  onNewPlan?: () => void;
  onBlockClick?: (id: string | number) => void;
  onBlockMove?: (id: string | number, day: number, start: number, end: number) => void;
}) {
  const [view, setView] = useState<View>("week");
  const [anchor, setAnchor] = useState(3);

  const scrollContainerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 9 * HOUR_PX;
    }
  }, []);

  // Dynamic day numbers based on weekStart
  const dayNums = useMemo(() => {
    const nums = [];
    const start = new Date(weekStart);
    for (let i = 0; i < 7; i++) {
      const d = new Date(start.getTime() + i * 24 * 60 * 60 * 1000);
      nums.push(d.getDate());
    }
    return nums;
  }, [weekStart]);

  // Dynamic month and year label
  const monthYearLabel = useMemo(() => {
    return weekStart.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  }, [weekStart]);

  // Dynamic today index relative to weekStart (0-6)
  const todayIndex = useMemo(() => {
    const today = new Date();
    const checkDate = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    const wsDate = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate());
    const diffTime = checkDate - wsDate.getTime();
    const diffDays = Math.round(diffTime / (24 * 60 * 60 * 1000));
    if (diffDays >= 0 && diffDays < 7) {
      return diffDays;
    }
    return -1;
  }, [weekStart]);

  // Dynamic current time line indicator
  const [nowTime, setNowTime] = useState(() => new Date());
  useMemo(() => {
    const timer = setInterval(() => setNowTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const currentHourDecimal = nowTime.getHours() + nowTime.getMinutes() / 60;

  const visibleDays = useMemo(() => {
    if (view === "week") return [0, 1, 2, 3, 4, 5, 6];
    if (view === "3day") return [anchor, (anchor + 1) % 7, (anchor + 2) % 7];
    return [anchor];
  }, [view, anchor]);

  const shift = (d: number) => {
    if (view === "week") {
      if (onWeekChange) {
        const nextWeek = new Date(weekStart.getTime() + d * 7 * 24 * 60 * 60 * 1000);
        onWeekChange(nextWeek);
      }
    } else {
      setAnchor((a) => Math.min(6, Math.max(0, a + d)));
    }
  };

  const goToToday = () => {
    const today = new Date();
    const day = today.getDay();
    // Monday is index 0. If day is Sunday (0), diff is today.getDate() - 6.
    // Otherwise, diff is today.getDate() - day + 1.
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(today.getTime());
    monday.setDate(diff);
    monday.setHours(0, 0, 0, 0);

    if (onWeekChange) {
      onWeekChange(monday);
    }
    const todayIndex = day === 0 ? 6 : day - 1;
    setAnchor(todayIndex);
  };

  return (
    <section className="glass flex h-full flex-col rounded-2xl p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{monthYearLabel}</h2>
          <p className="text-xs text-muted-foreground">
            Week {Math.ceil((((weekStart.getTime() - new Date(weekStart.getFullYear(), 0, 1).getTime()) / (24 * 60 * 60 * 1000)) + 1) / 7)} · {visibleDays.length} {visibleDays.length === 1 ? "day" : "days"} ·{" "}
            <span className="text-primary">Focus protected</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={goToToday}
            className="rounded-lg border border-border bg-card/60 px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-all"
          >
            Today
          </button>
          <div className="flex items-center rounded-lg border border-border bg-card/60 p-0.5">
            {(["day", "3day", "week"] as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-md px-3 py-1 text-xs font-medium capitalize transition-colors ${view === v ? "bg-gradient-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
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
          <button onClick={onNewPlan} className="flex items-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow">
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

      <div ref={scrollContainerRef} className="flex-1 overflow-auto rounded-xl border border-border bg-background/30">
        <div className="flex min-w-fit">
          <div className="sticky left-0 z-10 w-14 shrink-0 border-r border-border bg-background/60 backdrop-blur">
            <div className="h-10 border-b border-border" />
            {HOURS.map((h) => (
              <div key={h} style={{ height: HOUR_PX }} className="relative border-b border-border/60">
                <span className="absolute -top-2 right-2 text-[10px] text-muted-foreground">
                  {h > 12 ? h - 12 : h}{h >= 12 ? "pm" : "am"}
                </span>
              </div>
            ))}
          </div>

          <div className="grid flex-1" style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(140px, 1fr))` }}>
            {visibleDays.map((d) => {
              const dayBlocks = blocks.filter((b) => b.day === d);
              const isToday = d === todayIndex;
              return (
                <div key={d} className="relative border-r border-border/60 last:border-r-0">
                  <div className={`sticky top-0 z-10 flex h-10 items-center justify-center gap-2 border-b border-border backdrop-blur ${isToday ? "bg-primary/10" : "bg-background/60"}`}>
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{DAY_LABELS[d]}</span>
                    <span className={`text-sm font-semibold ${isToday ? "text-primary" : ""}`}>{dayNums[d]}</span>
                  </div>

                  <div
                    className="relative"
                    style={{ height: HOURS.length * HOUR_PX }}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      const blockIdStr = e.dataTransfer.getData("text/plain");
                      if (!blockIdStr) return;
                      const grabOffsetYStr = e.dataTransfer.getData("grabOffsetY");
                      const grabOffsetY = grabOffsetYStr ? parseFloat(grabOffsetYStr) : 0;

                      const rect = e.currentTarget.getBoundingClientRect();
                      const y = e.clientY - rect.top - grabOffsetY;
                      // Snap to nearest 15-minute block (0.25 hour increments)
                      const hour = Math.min(23.75, Math.max(0, Math.round((y / HOUR_PX) * 4) / 4));

                      const block = blocks.find(b => b.id.toString() === blockIdStr);
                      if (block) {
                        const duration = block.end - block.start;
                        const newEnd = Math.min(24, hour + duration);
                        onBlockMove?.(block.id, d, hour, newEnd);
                      }
                    }}
                  >
                    {HOURS.map((h) => (
                      <div key={h} style={{ height: HOUR_PX }} className="border-b border-border/40" />
                    ))}

                    {isToday && currentHourDecimal >= HOURS[0] && currentHourDecimal <= HOURS[HOURS.length - 1] + 1 && (
                      <div className="pointer-events-none absolute left-0 right-0 z-20" style={{ top: (currentHourDecimal - HOURS[0]) * HOUR_PX }}>
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
                          draggable
                          onDragStart={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect();
                            const grabOffsetY = e.clientY - rect.top;
                            e.dataTransfer.setData("text/plain", b.id.toString());
                            e.dataTransfer.setData("grabOffsetY", grabOffsetY.toString());
                            e.currentTarget.style.opacity = "0.5";
                          }}
                          onDragEnd={(e) => {
                            e.currentTarget.style.opacity = "1";
                          }}
                          onClick={() => onBlockClick?.(b.id)}
                          style={{ top, height, transition: "top 600ms cubic-bezier(.2,.8,.2,1), height 600ms" }}
                          className={`group absolute left-1 right-1 overflow-hidden rounded-lg border px-2 py-1.5 text-left text-[11px] hover:z-10 hover:scale-[1.02] cursor-grab active:cursor-grabbing ${b.hasConflict
                            ? "bg-red-500/20 border-red-500/60 text-red-200 ring-1 ring-red-500/50 shadow-[0_0_12px_-3px_rgba(239,68,68,0.5)]"
                            : CATEGORY_STYLE[b.category]
                            } ${isHigh ? "ring-1 ring-current shadow-[0_0_18px_-2px_currentColor]" : ""
                            } ${b.focus ? "border-dashed" : ""} ${isFlashing ? "animate-pulse ring-2 ring-amber-400" : ""} ${isPulse ? "ring-2 ring-primary animate-pulse" : ""}`}
                        >
                          <div className="flex items-center gap-1 font-semibold">
                            {b.hasConflict && <AlertCircle size={10} className="text-red-400 shrink-0" />}
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
