import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { createTask, updateTask, addUserToTask, deleteUserFromTask, deleteTask, checkTaskConflict, type TaskPayload } from "@/api/tasks";
import { toast } from "sonner";
import { showErrorToast } from "@/utils/errors";
import { AlertCircle, Calendar, Clock, MapPin, Sparkles, Tag, Check, Loader2, Users, UserPlus, Trash2 } from "lucide-react";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTaskCreated: (date?: Date) => void;
  initialDate?: string; // e.g. "2026-05-13"
  taskToEdit?: any; // Passed when editing an existing task
  weekStart?: Date; // The active week start date
}

const CATEGORIES = ["Work", "Study", "Personal", "Social", "Travel", "Focus", "Others"] as const;
const PRIORITIES = ["low", "mid", "high"] as const;

function getStartOfWeek(date: Date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d.setDate(diff));
  monday.setHours(0, 0, 0, 0);
  return monday;
}

export function CreateTaskModal({
  isOpen,
  onClose,
  onTaskCreated,
  initialDate,
  taskToEdit,
  weekStart,
}: CreateTaskModalProps) {
  const fallbackInitialDate = React.useMemo(() => {
    const ws = weekStart || getStartOfWeek(new Date());
    const today = new Date();
    const checkDate = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    const wsDate = new Date(ws.getFullYear(), ws.getMonth(), ws.getDate());
    const diffTime = checkDate - wsDate.getTime();
    const diffDays = Math.round(diffTime / (24 * 60 * 60 * 1000));
    const targetDate = (diffDays >= 0 && diffDays < 7) ? today : ws;

    const yyyy = targetDate.getFullYear();
    const mm = String(targetDate.getMonth() + 1).padStart(2, "0");
    const dd = String(targetDate.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }, [weekStart]);

  const dateOptions = React.useMemo(() => {
    const options = [];
    const start = weekStart ? new Date(weekStart) : getStartOfWeek(new Date());
    for (let i = 0; i < 7; i++) {
      const d = new Date(start.getTime() + i * 24 * 60 * 60 * 1000);
      const value = d.getFullYear() + "-" +
        String(d.getMonth() + 1).padStart(2, "0") + "-" +
        String(d.getDate()).padStart(2, "0");
      const label = d.toLocaleDateString("en-US", {
        weekday: "long",
        month: "short",
        day: "numeric",
        year: "numeric",
      });
      options.push({ value, label });
    }
    return options;
  }, [weekStart]);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<"low" | "mid" | "high">("low");
  const [category, setCategory] = useState<string>("Work");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState(initialDate || "");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [reminder, setReminder] = useState(false);
  const [loading, setLoading] = useState(false);

  // Collaborator sub-form states
  const [collabEmail, setCollabEmail] = useState("");
  const [collabRole, setCollabRole] = useState<string>("editor");
  const [pendingCollaborators, setPendingCollaborators] = useState<{ email: string; role: string }[]>([]);

  // Conflict warning state
  const [conflictData, setConflictData] = useState<any>(null);

  // Link states
  const [links, setLinks] = useState<string[]>([]);
  const [newLink, setNewLink] = useState("");

  // Description ref for auto-expand
  const descriptionRef = React.useRef<HTMLTextAreaElement>(null);

  const handleAddLink = () => {
    if (!newLink.trim()) return;
    let formatted = newLink.trim();
    if (!/^https?:\/\//i.test(formatted)) {
      formatted = "https://" + formatted;
    }
    try {
      new URL(formatted);
      if (links.includes(formatted)) {
        toast.error("Link already added");
        return;
      }
      setLinks(prev => [...prev, formatted]);
      setNewLink("");
    } catch (err) {
      toast.error("Invalid URL format");
    }
  };

  const dynamicDuration = React.useMemo(() => {
    if (!startTime || !endTime) return null;
    const [sh, sm] = startTime.split(":").map(Number);
    const [eh, em] = endTime.split(":").map(Number);
    if (isNaN(sh) || isNaN(sm) || isNaN(eh) || isNaN(em)) return null;
    let diffMinutes = (eh * 60 + em) - (sh * 60 + sm);
    if (diffMinutes < 0) return null;

    const hours = Math.floor(diffMinutes / 60);
    const mins = diffMinutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ""}`;
    }
    return `${mins}m`;
  }, [startTime, endTime]);

  // Auto-expand description textarea
  useEffect(() => {
    if (descriptionRef.current) {
      descriptionRef.current.style.height = "auto";
      descriptionRef.current.style.height = `${descriptionRef.current.scrollHeight}px`;
    }
  }, [description, isOpen]);

  // Populate form state when editing a task
  useEffect(() => {
    if (taskToEdit && isOpen) {
      setTitle(taskToEdit.title || "");
      setDescription(taskToEdit.description || "");
      setPriority(taskToEdit.priority || "low");
      setCategory(taskToEdit.category || "Work");
      setLocation(taskToEdit.location || "");
      setReminder(!!taskToEdit.reminder);
      setLinks(taskToEdit.link || []);

      const parseLocalTime = (isoString: string) => {
        const d = new Date(isoString);
        const mytTime = d.getTime() + (d.getTimezoneOffset() + 480) * 60 * 1000;
        const mytDate = new Date(mytTime);
        const hh = String(mytDate.getHours()).padStart(2, "0");
        const mm = String(mytDate.getMinutes()).padStart(2, "0");
        return `${hh}:${mm}`;
      };

      const parseLocalDate = (isoString: string) => {
        const d = new Date(isoString);
        const mytTime = d.getTime() + (d.getTimezoneOffset() + 480) * 60 * 1000;
        const mytDate = new Date(mytTime);
        const yyyy = mytDate.getFullYear();
        const mm = String(mytDate.getMonth() + 1).padStart(2, "0");
        const dd = String(mytDate.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
      };

      if (taskToEdit.start_time) {
        setDate(parseLocalDate(taskToEdit.start_time));
        setStartTime(parseLocalTime(taskToEdit.start_time));
      }
      if (taskToEdit.end_time) {
        setEndTime(parseLocalTime(taskToEdit.end_time));
      }
    } else if (isOpen) {
      // Clear form for creating new task
      setTitle("");
      setDescription("");
      setPriority("low");
      setCategory("Work");
      setLocation("");
      setDate(initialDate || fallbackInitialDate);
      setStartTime("09:00");
      setEndTime("10:00");
      setReminder(false);
      setLinks([]);
    }
    setPendingCollaborators([]);
    setCollabEmail("");
    setCollabRole("editor");
    setConflictData(null);
    setNewLink("");
  }, [taskToEdit, isOpen, initialDate, fallbackInitialDate]);

  // Trigger on-the-fly conflict check
  useEffect(() => {
    if (!isOpen) return;

    const checkConflictsOnTheFly = async () => {
      if (!date || !startTime || !endTime) return;
      try {
        const startIso = `${date}T${startTime}:00+08:00`;
        const endIso = `${date}T${endTime}:00+08:00`;

        if (new Date(startIso) >= new Date(endIso)) {
          return;
        }

        const res = await checkTaskConflict({
          start_time: startIso,
          end_time: endIso,
          task_id: taskToEdit ? (taskToEdit.task_id || taskToEdit.id) : undefined
        });

        if (res && res.has_conflict) {
          setConflictData(res.conflict_data);
        } else {
          setConflictData(null);
        }
      } catch (err) {
        console.error("Error checking task conflict:", err);
      }
    };

    const delayDebounceFn = setTimeout(() => {
      checkConflictsOnTheFly();
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [date, startTime, endTime, isOpen, taskToEdit]);

  const handleAddCollaborator = async () => {
    if (!collabEmail.trim()) {
      toast.error("Please enter a collaborator's email");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(collabEmail.trim())) {
      toast.error("Invalid email format");
      return;
    }

    if (taskToEdit) {
      // Directly add to task in backend when editing
      try {
        setLoading(true);
        const result = await addUserToTask(taskToEdit.task_id || taskToEdit.id, collabEmail.trim(), collabRole);

        if (result.status_code === 400 || result.detail === "User not found") {
          toast.error(result.detail || "User not found");
        } else {
          toast.success("Collaborator added successfully!");
          onTaskCreated(); // refresh parent
          setCollabEmail("");
        }
      } catch (err: any) {
        console.error(err);
        showErrorToast(err, "Failed to add collaborator. Make sure user exists.");
      } finally {
        setLoading(false);
      }
    } else {
      // Queue locally when creating a task
      if (pendingCollaborators.some(c => c.email === collabEmail.trim())) {
        toast.error("Collaborator already added to list");
        return;
      }
      setPendingCollaborators(prev => [...prev, { email: collabEmail.trim(), role: collabRole }]);
      setCollabEmail("");
      toast.success("Collaborator queued!");
    }
  };

  const handleRemoveCollaborator = async (userId: string) => {
    if (!taskToEdit) return;
    try {
      setLoading(true);
      await deleteUserFromTask(taskToEdit.task_id || taskToEdit.id, userId);
      toast.success("Collaborator removed successfully!");
      onTaskCreated();
    } catch (err: any) {
      console.error(err);
      showErrorToast(err, "Failed to remove collaborator");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTask = async () => {
    if (!taskToEdit) return;
    if (!window.confirm("Are you sure you want to delete this schedule block?")) {
      return;
    }
    setLoading(true);
    try {
      await deleteTask(taskToEdit.task_id || taskToEdit.id);
      toast.success("Task deleted successfully!");
      onTaskCreated();
      onClose();
    } catch (err: any) {
      console.error(err);
      showErrorToast(err, "Failed to delete task");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Please enter a task title");
      return;
    }

    const startIso = `${date}T${startTime}:00+08:00`;
    const endIso = `${date}T${endTime}:00+08:00`;

    if (new Date(startIso) >= new Date(endIso)) {
      toast.error("Start time must be before end time");
      return;
    }

    setLoading(true);
    setConflictData(null);

    try {
      const payload: TaskPayload = {
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        category,
        location: location.trim() || undefined,
        link: links,
        start_time: startIso,
        end_time: endIso,
        reminder,
        status: taskToEdit ? taskToEdit.status : "pending",
      };

      const result = taskToEdit
        ? await updateTask(taskToEdit.task_id || taskToEdit.id, payload)
        : await createTask(payload);

      if (result.status_code === 400 && result.detail !== "Time conflict") {
        toast.error(result.detail || "Failed to save task");
        setLoading(false);
        return;
      }

      // If creating a new task, add queued collaborators
      if (!taskToEdit && result.task_id && pendingCollaborators.length > 0) {
        for (const c of pendingCollaborators) {
          try {
            await addUserToTask(result.task_id, c.email, c.role);
          } catch (collabErr) {
            console.error(`Failed to add collaborator ${c.email}:`, collabErr);
          }
        }
      }

      toast.success(taskToEdit ? "Task updated successfully!" : "Task created successfully!");
      onTaskCreated(new Date(startIso));
      onClose();
    } catch (err: any) {
      console.error(err);
      showErrorToast(err, "Failed to save task");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="glass border-border/80 max-w-4xl w-[90vw] text-foreground flex flex-col max-h-[95vh] sm:max-h-[90vh] p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-4 border-b border-border/40 shrink-0">
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <Sparkles className="text-primary h-5 w-5 animate-pulse-glow" />
            {taskToEdit ? "Edit Plan Block" : "Add New Plan Block"}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-xs">
            {taskToEdit
              ? "Modify details of your scheduled plan block."
              : "Schedule a focus session, work task, or study block into your calendar."}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
          {/* Main Form Fields (Left Column) */}
          <form onSubmit={handleSubmit} className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {conflictData && (
                <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3.5 text-xs text-amber-300">
                  <div className="flex items-center gap-2 font-bold mb-1.5">
                    <AlertCircle size={15} /> Time Conflict Detected
                  </div>
                  <p className="mb-2 opacity-90">
                    The selected time overlaps with existing schedule items:
                  </p>
                  <ul className="space-y-1 bg-black/20 p-2 rounded-lg">
                    {Object.entries(conflictData).map(([userLabel, tasks]: [string, any]) =>
                      tasks.map((task: any) => (
                        <li key={task.task_id || task.id} className="flex justify-between items-center">
                          <span className="font-semibold">{userLabel}: {task.title}</span>
                          <span className="opacity-80">
                            ({new Date(task.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })} - {new Date(task.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })})
                          </span>
                        </li>
                      ))
                    )}
                  </ul>
                  <p className="mt-2 text-[10px] opacity-70">
                    Please adjust your date or times to avoid conflicts.
                  </p>
                </div>
              )}

              {/* Title */}
              <div className="space-y-1">
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Title</label>
                <input
                  required
                  type="text"
                  placeholder="e.g. Review FYP Literature"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              {/* Description */}
              <div className="space-y-1">
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Description</label>
                <textarea
                  ref={descriptionRef}
                  placeholder="Optional notes or subtasks..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary min-h-[60px] resize-none overflow-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Category */}
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                    <Tag size={10} /> Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-lg border border-border bg-popover px-3 py-2 text-sm outline-none focus:border-primary"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c} className="bg-background text-foreground">
                        {c}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Priority */}
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Priority</label>
                  <div className="flex gap-1.5 h-[38px] items-center">
                    {PRIORITIES.map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPriority(p)}
                        className={`flex-1 rounded-md py-1.5 text-xs font-semibold capitalize border transition-all ${priority === p
                          ? "bg-gradient-primary border-primary/50 text-primary-foreground shadow-glow"
                          : "border-border bg-input/40 text-muted-foreground hover:text-foreground"
                          }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {/* Date Picker */}
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                    <Calendar size={10} /> Date
                  </label>
                  <input type="date"
                    className="rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                  />
                </div>
                {/* Start Time */}
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                    <Clock size={10} /> Start Time
                  </label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
                {/* End Time */}
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between gap-1">
                    <span className="flex items-center gap-1"><Clock size={10} /> End Time</span>
                    {dynamicDuration && <span className="text-[10px] text-primary font-bold">({dynamicDuration})</span>}
                  </label>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
              </div>

              {/* Location */}
              <div className="space-y-1">
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                  <MapPin size={10} /> Location
                </label>
                <input
                  type="text"
                  placeholder="e.g. Remote, Library, Room 402"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input/60 px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              {/* Links list */}
              <div className="space-y-2">
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                  <Sparkles size={10} className="text-primary animate-pulse" /> Links
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    placeholder="e.g. google.com"
                    value={newLink}
                    onChange={(e) => setNewLink(e.target.value)}
                    className="flex-1 rounded-lg border border-border bg-input/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    onClick={handleAddLink}
                    className="rounded-lg bg-primary/10 border border-primary px-3 text-xs font-semibold text-primary hover:bg-primary/20 transition-all"
                  >
                    Add
                  </button>
                </div>
                {links.length > 0 && (
                  <ul className="space-y-1.5 max-h-24 overflow-y-auto bg-black/10 p-2 rounded-lg border border-border/40">
                    {links.map((lnk, index) => (
                      <li key={index} className="flex items-center justify-between text-xs text-muted-foreground bg-[#0d0f14]/40 px-2 py-1 rounded">
                        <a href={lnk} target="_blank" rel="noopener noreferrer" className="truncate hover:text-primary hover:underline max-w-[80%]">
                          {lnk}
                        </a>
                        <button
                          type="button"
                          onClick={() => setLinks(prev => prev.filter((_, idx) => idx !== index))}
                          className="text-muted-foreground hover:text-red-400 cursor-pointer transition-colors"
                        >
                          <Trash2 size={12} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Reminder */}
              <div className="flex items-center justify-between rounded-lg border border-border bg-input/20 p-3">
                <div>
                  <p className="text-xs font-semibold">Enable Reminder</p>
                  <p className="text-[10px] text-muted-foreground">Receive a ping 10 minutes before the block starts.</p>
                </div>
                <input
                  type="checkbox"
                  checked={reminder}
                  onChange={(e) => setReminder(e.target.checked)}
                  className="h-4.5 w-4.5 rounded border-border bg-input accent-primary"
                />
              </div>
            </div>

            <div className="p-6 pt-4 border-t border-border bg-[#0d0f14]/80 backdrop-blur-sm flex gap-2 justify-between shrink-0">
              <div>
                {taskToEdit && (
                  <button
                    type="button"
                    onClick={handleDeleteTask}
                    disabled={loading}
                    className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/20 transition-all"
                  >
                    Delete Block
                  </button>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-border bg-card/60 px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-1.5 rounded-lg bg-gradient-primary px-5 py-2 text-xs font-semibold text-primary-foreground shadow-glow disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 size={13} className="animate-spin" /> Saving...
                    </>
                  ) : (
                    <>
                      <Check size={13} /> {taskToEdit ? "Save Changes" : "Add Block"}
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {/* Collaborator Sidebar (Right Column) */}
          <div className="w-full md:w-80 shrink-0 border-t md:border-t-0 md:border-l border-border/40 flex flex-col min-h-0 bg-white/[0.02] overflow-hidden">
            <div className="p-6 pb-4 border-b border-border/40 shrink-0 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-white/[0.01]">
              <Users size={14} className="text-primary" /> Collaborators
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {((taskToEdit?.users || []).length === 0 && pendingCollaborators.length === 0) ? (
                <div className="text-center py-8 text-xs text-muted-foreground">
                  No collaborators added yet. Add one below to share this block.
                </div>
              ) : (
                <ul className="space-y-2">
                  {/* Existing collaborators */}
                  {(taskToEdit?.users || []).map((u: any, idx: number) => (
                    <li key={`ex-${idx}`} className="flex items-center justify-between rounded-md border border-border/60 bg-background/40 px-2.5 py-1.5 text-xs">
                      <span className="font-medium truncate max-w-[150px]">{u.name || u.user_id}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="rounded-full border border-primary/30 bg-primary/5 px-2 py-0.5 text-[10px] uppercase font-bold text-primary">
                          {u.role}
                        </span>
                        {u.role !== "owner" && (
                          <button
                            type="button"
                            onClick={() => handleRemoveCollaborator(u.user_id)}
                            className="text-muted-foreground hover:text-red-400 cursor-pointer transition-colors"
                            title="Remove Collaborator"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    </li>
                  ))}

                  {/* Pending collaborators */}
                  {pendingCollaborators.map((c, idx) => (
                    <li key={`pend-${idx}`} className="flex items-center justify-between rounded-md border border-amber-500/20 bg-amber-500/5 px-2.5 py-1.5 text-xs">
                      <span className="text-amber-300 font-medium truncate max-w-[150px]">{c.email}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] uppercase font-bold text-amber-300">
                          {c.role}
                        </span>
                        <button
                          type="button"
                          onClick={() => setPendingCollaborators(prev => prev.filter((_, i) => i !== idx))}
                          className="text-muted-foreground hover:text-red-400 cursor-pointer transition-colors"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Sticky Collaborator Controls at bottom */}
            <div className="p-6 pt-4 border-t border-border bg-[#0d0f14]/80 backdrop-blur-sm shrink-0 flex flex-col gap-2.5">
              <div className="space-y-1">
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Email Address</label>
                <input
                  type="email"
                  placeholder="collaborator@email.com"
                  value={collabEmail}
                  onChange={(e) => setCollabEmail(e.target.value)}
                  className="w-full rounded-lg border border-border bg-input/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Access Role</label>
                  <select
                    value={collabRole}
                    onChange={(e) => setCollabRole(e.target.value)}
                    className="w-full rounded-lg border border-border bg-popover px-2 py-1.5 text-xs outline-none focus:border-primary"
                  >
                    <option value="viewer" className="bg-background text-foreground">Viewer</option>
                    <option value="editor" className="bg-background text-foreground">Editor</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={handleAddCollaborator}
                    className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-primary bg-primary/10 h-[34px] text-xs font-semibold text-primary hover:bg-primary/15 transition-all cursor-pointer"
                  >
                    <UserPlus size={13} /> Add User
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

