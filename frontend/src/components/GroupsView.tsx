import { Users, Vote, Sparkles, CheckCircle2, Clock, MapPin } from "lucide-react";
import { Fragment, useState } from "react";

const MEMBERS = [
  { name: "You", color: "bg-gradient-primary" },
  { name: "Lina", color: "bg-amber-500" },
  { name: "Marcus", color: "bg-emerald-500" },
  { name: "Priya", color: "bg-accent" },
  { name: "Jay", color: "bg-indigo-400" },
];

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SLOTS = ["9a", "11a", "1p", "3p", "5p", "7p", "9p"];

// 0 = busy, 1 = some free, 2 = all free
const OVERLAY: number[][] = [
  [0, 1, 1, 2, 0, 0, 0],
  [1, 0, 2, 1, 0, 0, 0],
  [0, 1, 2, 2, 1, 0, 0],
  [0, 0, 1, 2, 2, 1, 0],
  [0, 0, 0, 1, 2, 2, 1],
  [0, 1, 1, 2, 2, 2, 1],
  [0, 0, 1, 1, 2, 2, 2],
];

export function GroupsView() {
  const [votes, setVotes] = useState({ a: 4, b: 2, c: 1 });
  const [picked, setPicked] = useState<"a" | "b" | "c" | null>(null);

  const vote = (k: "a" | "b" | "c") => {
    if (picked) return;
    setVotes((v) => ({ ...v, [k]: v[k] + 1 }));
    setPicked(k);
  };

  const total = votes.a + votes.b + votes.c;

  return (
    <section className="glass flex h-full flex-col gap-4 overflow-y-auto rounded-2xl p-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Users size={18} className="text-primary" /> Squad · Weekend Plans
          </h2>
          <p className="text-xs text-muted-foreground">5 members · synced 2 min ago</p>
        </div>
        <div className="flex -space-x-2">
          {MEMBERS.map((m) => (
            <div key={m.name} className={`grid h-8 w-8 place-items-center rounded-full border-2 border-background text-[10px] font-bold text-primary-foreground ${m.color}`}>
              {m.name.charAt(0)}
            </div>
          ))}
        </div>
      </div>

      {/* AI suggestion banner */}
      <div className="relative overflow-hidden rounded-xl border border-primary/40 bg-gradient-primary/10 p-4">
        <div className="absolute inset-0 bg-gradient-primary opacity-10" />
        <div className="relative flex items-start gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-primary shadow-glow">
            <Sparkles size={16} className="text-primary-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-primary">Auto-Suggest · Best Meetup</p>
            <h3 className="text-sm font-semibold">Thursday · 3pm – 5pm</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Optimal overlap for all 5 members. AI factored in commute, energy levels, and existing focus blocks.
            </p>
          </div>
          <button className="shrink-0 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow">
            Lock In
          </button>
        </div>
      </div>

      {/* Free Time Overlay */}
      <div className="rounded-xl border border-border bg-card/40 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Free Time Overlay</h3>
            <p className="text-[10px] text-muted-foreground">Brighter = more members available</p>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
            <span className="h-2 w-2 rounded-sm bg-primary/20" /> some
            <span className="ml-2 h-2 w-2 rounded-sm bg-primary shadow-glow" /> all
          </div>
        </div>

        <div className="grid gap-1" style={{ gridTemplateColumns: `40px repeat(${DAYS.length}, 1fr)` }}>
          <div />
          {DAYS.map((d) => (
            <div key={d} className="text-center text-[10px] uppercase tracking-wider text-muted-foreground">{d}</div>
          ))}
          {SLOTS.map((slot, si) => (
            <Fragment key={slot}>
              <div className="text-right text-[10px] text-muted-foreground">{slot}</div>
              {DAYS.map((d, di) => {
                const v = OVERLAY[si][di];
                const cls =
                  v === 2 ? "bg-primary shadow-[0_0_12px_-2px_currentColor] text-primary" :
                    v === 1 ? "bg-primary/30 text-primary" :
                      "bg-card border border-border/60";
                return <div key={`${d}-${slot}`} className={`h-6 rounded ${cls}`} />;
              })}
            </Fragment>
          ))}
        </div>
      </div>

      {/* Poll */}
      <div className="rounded-xl border border-border bg-card/40 p-4">
        <div className="mb-3 flex items-center gap-2">
          <Vote size={14} className="text-accent" />
          <h3 className="text-sm font-semibold">Poll · Hangout Time &amp; Place</h3>
          <span className="ml-auto text-[10px] text-muted-foreground">{total} votes</span>
        </div>

        <div className="space-y-2">
          {[
            { k: "a" as const, title: "Thu 3pm · Rooftop Café", meta: "Downtown · 5 min walk" },
            { k: "b" as const, title: "Fri 7pm · Bowling Alley", meta: "Midtown · 12 min ride" },
            { k: "c" as const, title: "Sat 1pm · Park Picnic", meta: "Riverside · pack snacks" },
          ].map((opt) => {
            const count = votes[opt.k];
            const pct = total ? (count / total) * 100 : 0;
            const isPicked = picked === opt.k;
            return (
              <button
                key={opt.k}
                onClick={() => vote(opt.k)}
                disabled={!!picked}
                className={`relative w-full overflow-hidden rounded-lg border p-3 text-left transition-all ${isPicked ? "border-primary bg-primary/10" : "border-border bg-background/30 hover:border-primary/50"
                  } ${picked && !isPicked ? "opacity-60" : ""}`}
              >
                <div
                  className="absolute inset-y-0 left-0 bg-gradient-primary/20 transition-all"
                  style={{ width: `${pct}%` }}
                />
                <div className="relative flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="flex items-center gap-1.5 text-xs font-semibold">
                      <Clock size={11} className="text-muted-foreground" /> {opt.title}
                    </p>
                    <p className="mt-0.5 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                      <MapPin size={10} /> {opt.meta}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold tabular-nums">{count}</span>
                    {isPicked && <CheckCircle2 size={14} className="text-primary" />}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {picked && (
          <p className="mt-3 text-[10px] text-muted-foreground">Vote locked · AI will notify the group when results close.</p>
        )}
      </div>
    </section>
  );
}
