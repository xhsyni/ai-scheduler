type Props = { size?: number; withWordmark?: boolean; className?: string };

export function CogniLogo({ size = 36, withWordmark = false, className = "" }: Props) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        className="animate-pulse-glow"
        aria-label="CogniPlan logo"
      >
        <defs>
          <linearGradient id="cp-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="oklch(0.82 0.2 195)" />
            <stop offset="100%" stopColor="oklch(0.7 0.22 305)" />
          </linearGradient>
        </defs>
        {/* Calendar body */}
        <rect x="6" y="10" width="30" height="30" rx="6" stroke="url(#cp-grad)" strokeWidth="2" fill="oklch(0.2 0.03 262 / 0.6)" />
        <line x1="6" y1="18" x2="36" y2="18" stroke="url(#cp-grad)" strokeWidth="1.5" />
        <line x1="13" y1="6" x2="13" y2="13" stroke="url(#cp-grad)" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="29" y1="6" x2="29" y2="13" stroke="url(#cp-grad)" strokeWidth="2.5" strokeLinecap="round" />
        {/* Grid dots */}
        <circle cx="14" cy="25" r="1.4" fill="oklch(0.82 0.2 195)" />
        <circle cx="21" cy="25" r="1.4" fill="oklch(0.82 0.2 195 / 0.6)" />
        <circle cx="14" cy="32" r="1.4" fill="oklch(0.82 0.2 195 / 0.6)" />
        <circle cx="21" cy="32" r="2.2" fill="url(#cp-grad)" />
        {/* AI aura spark */}
        <path
          d="M30 22 Q38 24 42 32 T44 44"
          stroke="url(#cp-grad)"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
        <circle cx="42" cy="14" r="2.5" fill="url(#cp-grad)" />
        <circle cx="42" cy="14" r="5" fill="url(#cp-grad)" opacity="0.25" />
      </svg>
      {withWordmark && (
        <div className="flex flex-col leading-none">
          <span className="font-display text-lg font-bold tracking-tight text-foreground">
            Cogni<span className="text-gradient-primary">Plan</span>
          </span>
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            AI Scheduler
          </span>
        </div>
      )}
    </div>
  );
}
