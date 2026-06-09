import { useState } from "react";
import { ListTodo, Calendar as CalendarIcon, MapPin, Tag, AlertCircle, Plus, Sparkles, Clock } from "lucide-react";
import { type Category, type Priority } from "./CalendarView";
import { Calendar } from "@/components/ui/calendar";

interface Task {
  task_id?: string;
  id?: string;
  title: string;
  description?: string;
  priority: Priority;
  category: Category;
  location?: string;
  start_time: string;
  end_time: string;
  reminder?: boolean;
}

interface TasksViewProps {
  tasks: Task[];
  weekStart?: Date;
  onWeekChange?: (date: Date) => void;
  onOpenCreateModal: () => void;
  onEditTask?: (task: Task) => void;
}

const CATEGORY_STYLE: Record<Category, string> = {
  Study: "bg-primary/15 border-primary/40 text-primary",
  Travel: "bg-amber-500/15 border-amber-500/40 text-amber-300",
  Personal: "bg-emerald-500/15 border-emerald-500/40 text-emerald-300",
  Social: "bg-accent/15 border-accent/40 text-accent",
  Focus: "bg-cyan-400/15 border-cyan-400/50 text-cyan-200",
  Work: "bg-indigo-400/15 border-indigo-400/40 text-indigo-200",
  Others: "bg-gray-400/15 border-gray-400/40 text-gray-200",
};

const PRIORITY_STYLE: Record<Priority, string> = {
  high: "bg-red-500/15 border-red-500/40 text-red-300",
  med: "bg-amber-500/15 border-amber-500/40 text-amber-300",
  low: "bg-blue-500/15 border-blue-500/40 text-blue-300",
};

export function TasksView({ tasks = [], weekStart, onWeekChange, onOpenCreateModal, onEditTask }: TasksViewProps) {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());

  const handleSelectDate = (date: Date | undefined) => {
    setSelectedDate(date);
    if (date && onWeekChange && weekStart) {
      const newWeekStart = getStartOfWeek(date);
      if (newWeekStart.getTime() !== getStartOfWeek(weekStart).getTime()) {
        onWeekChange(newWeekStart);
      }
    }
  };

  function getStartOfWeek(date: Date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(d.setDate(diff));
    monday.setHours(0, 0, 0, 0);
    return monday;
  }

  // Enforce MYT alignment when displaying dates on the list
  const formatTaskDate = (isoString: string) => {
    const d = new Date(isoString);
    // Convert to MYT UTC+8
    const mytTime = d.getTime() + (d.getTimezoneOffset() + 480) * 60 * 1000;
    const mytDate = new Date(mytTime);
    return mytDate.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTaskTime = (isoString: string) => {
    const d = new Date(isoString);
    const mytTime = d.getTime() + (d.getTimezoneOffset() + 480) * 60 * 1000;
    const mytDate = new Date(mytTime);
    return mytDate.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  // Check if a date has tasks scheduled
  const hasTasksOnDate = (date: Date) => {
    return tasks.some((task) => {
      const taskDate = new Date(task.start_time);
      const mytTime = taskDate.getTime() + (taskDate.getTimezoneOffset() + 480) * 60 * 1000;
      const mytDate = new Date(mytTime);
      return (
        mytDate.getFullYear() === date.getFullYear() &&
        mytDate.getMonth() === date.getMonth() &&
        mytDate.getDate() === date.getDate()
      );
    });
  };

  // Filter tasks based on selected date
  const filteredTasks = selectedDate
    ? tasks.filter((task) => {
        const taskDate = new Date(task.start_time);
        const mytTime = taskDate.getTime() + (taskDate.getTimezoneOffset() + 480) * 60 * 1000;
        const mytDate = new Date(mytTime);
        return (
          mytDate.getFullYear() === selectedDate.getFullYear() &&
          mytDate.getMonth() === selectedDate.getMonth() &&
          mytDate.getDate() === selectedDate.getDate()
        );
      })
    : tasks;

  // Group filtered tasks by date
  const groupedTasks: Record<string, Task[]> = {};

  // Sort tasks chronologically
  const sortedTasks = [...filteredTasks].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  sortedTasks.forEach((task) => {
    const dateStr = formatTaskDate(task.start_time);
    if (!groupedTasks[dateStr]) {
      groupedTasks[dateStr] = [];
    }
    groupedTasks[dateStr].push(task);
  });

  const dates = Object.keys(groupedTasks);

  return (
    <div className="flex flex-col lg:flex-row gap-5 h-full min-h-0 overflow-hidden text-foreground">
      {/* Calendar Filter Panel (Left Column) */}
      <div className="glass flex flex-col items-center rounded-2xl p-4 bg-card/25 border border-border/80 w-full lg:w-fit self-start shrink-0">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground self-start pl-2 flex items-center gap-1.5">
          <CalendarIcon size={12} className="text-primary" />
          Filter by Date
        </h3>
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={handleSelectDate}
          className="rounded-xl border border-border/60 bg-background/30 shadow-glow"
          modifiers={{
            hasTasks: (date) => hasTasksOnDate(date),
          }}
          modifiersClassNames={{
            hasTasks: "relative after:content-['•'] after:absolute after:bottom-1 after:left-1/2 after:-translate-x-1/2 after:text-primary after:text-[14px] after:font-black",
          }}
        />
        {selectedDate && (
          <button
            onClick={() => setSelectedDate(undefined)}
            className="mt-3 w-full rounded-lg border border-border bg-input/60 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-input hover:text-foreground transition-all"
          >
            Show All Tasks
          </button>
        )}
      </div>

      {/* Task List Panel (Right Column) */}
      <section className="glass flex-1 flex flex-col overflow-hidden rounded-2xl p-5 bg-card/30 border border-border/80">
        {/* Header */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <ListTodo size={18} className="text-primary" />
              {selectedDate ? (
                <span>
                  Tasks for{" "}
                  {selectedDate.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              ) : (
                <span>All Tasks</span>
              )}
            </h2>
            <p className="text-xs text-muted-foreground">
              {filteredTasks.length} {filteredTasks.length === 1 ? "plan block" : "plan blocks"} found
            </p>
          </div>
          <button
            onClick={onOpenCreateModal}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-glow transition-transform hover:scale-[1.01] active:scale-[0.99]"
          >
            <Plus size={13} /> Add Block
          </button>
        </div>

        {/* Scrollable Task List */}
        <div className="flex-1 overflow-y-auto space-y-5 pr-1">
          {dates.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center p-8 text-center">
              <div className="relative mb-4">
                <div className="absolute inset-0 bg-primary/10 rounded-full blur-xl animate-pulse" />
                <div className="relative grid h-16 w-16 place-items-center rounded-2xl border border-primary/20 bg-card/60">
                  <ListTodo size={28} className="text-primary animate-pulse-glow" />
                </div>
              </div>
              <h3 className="text-base font-semibold">No plan blocks</h3>
              <p className="mt-1 max-w-[280px] text-xs text-muted-foreground leading-relaxed">
                {selectedDate
                  ? "You don't have any plan blocks scheduled for this day."
                  : "Plan your week, block focus sessions, or manage squad hangouts. Your calendar is clean!"}
              </p>
              <button
                onClick={onOpenCreateModal}
                className="mt-4 flex items-center gap-1.5 rounded-lg border border-primary bg-primary/10 px-4 py-2 text-xs font-semibold text-primary hover:bg-primary/15 transition-all shadow-glow"
              >
                <Plus size={13} /> Create Plan Block
              </button>
            </div>
          ) : (
            dates.map((dateStr) => (
              <div key={dateStr} className="space-y-2.5">
                {/* Date Header */}
                <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground/80 sticky top-0 bg-background/5 py-1 backdrop-blur-sm z-10">
                  <CalendarIcon size={12} /> {dateStr}
                </h3>

                {/* Tasks for this date */}
                <div className="grid gap-3">
                  {groupedTasks[dateStr].map((task) => {
                    const cat = task.category || "Work";
                    const pri = task.priority || "low";
                    return (
                      <div
                        key={task.task_id || task.id}
                        onClick={() => onEditTask?.(task)}
                        className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-border bg-card/30 p-4 transition-all hover:border-primary/45 hover:bg-card/50 cursor-pointer"
                      >
                        <div className="space-y-1.5 min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-sm font-semibold leading-snug truncate">
                              {task.title}
                            </h4>

                            {/* Category Badge */}
                            <span
                              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold ${
                                CATEGORY_STYLE[cat as Category] || CATEGORY_STYLE["Work"]
                              }`}
                            >
                              <span className="h-1 w-1 rounded-full bg-current" />
                              {cat}
                            </span>

                            {/* Priority Badge */}
                            <span
                              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] uppercase tracking-wider font-semibold ${
                                PRIORITY_STYLE[pri as Priority] || PRIORITY_STYLE["low"]
                              }`}
                            >
                              {pri}
                            </span>
                          </div>

                          {task.description && (
                            <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 max-w-2xl">
                              {task.description}
                            </p>
                          )}

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
                            <span className="flex items-center gap-1.5">
                              <Clock size={11} className="text-primary/75" />
                              {formatTaskTime(task.start_time)} – {formatTaskTime(task.end_time)}
                            </span>

                            {task.location && (
                              <span className="flex items-center gap-1">
                                <MapPin size={11} className="text-primary/75" />
                                {task.location}
                              </span>
                            )}

                            {task.reminder && (
                              <span className="flex items-center gap-1 font-medium text-emerald-400">
                                <AlertCircle size={11} />
                                Ping active
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Right Action placeholder (or decoration) */}
                        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                          <span className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                            <Sparkles size={11} className="text-primary" /> Active schedule block
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
