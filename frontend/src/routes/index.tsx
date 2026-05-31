import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AuthScreen } from "@/components/AuthScreen";
import { Dashboard } from "@/components/Dashboard";
import { getMe } from "@/api/auth";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CogniPlan — AI Scheduler & Life Planning Assistant" },
      { name: "description", content: "CogniPlan is your AI co-pilot for scheduling, focus, and group planning. Optimize your day with intelligent automation." },
      { property: "og:title", content: "CogniPlan — AI Scheduler" },
      { property: "og:description", content: "Plan smarter with AI-powered Personal Time Optimization" },
    ],
  }),
  component: App,
});

function App() {
  const [user, setUser] = useState<string | null>(null);

  if (!user) {
    getMe().then((res) => {
      setUser(res.user.name);
    });
  }

  return user
    ? <Dashboard name={user} onLogout={() => setUser(null)} />
    : <AuthScreen onAuthed={setUser} />;
}
