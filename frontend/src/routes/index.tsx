import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { AuthScreen } from "@/components/AuthScreen";
import { Dashboard } from "@/components/Dashboard";
import { getMe } from "@/api/auth";
import Cookies from "js-cookie";

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((res) => {
        setUser(res.user.name);
      })
      .catch((err) => {
        console.error("Not authenticated:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return user ? (
    <Dashboard
      name={user}
      onLogout={() => {
        setUser(null);
        Cookies.remove("access_token");
      }}
    />
  ) : (
    <AuthScreen onAuthed={setUser} />
  );
}
