import Link from "next/link";
import { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  currentPath?: string;
};

const navItems = [
  { href: "/", label: "Radar" },
  { href: "/evidence", label: "Evidence" },
  { href: "/simulator", label: "Scenario Lab" },
  { href: "/action-plan", label: "Action Plan" },
];

export function AppShell({ children, currentPath = "/" }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <span className="eyebrow">SmartBuy Signal OS</span>
          <div>
            <h1>Procurement decision cockpit</h1>
            <p>
              Signals, barley market data, and scenario stress tests aligned in
              one command center.
            </p>
          </div>
        </div>
        <nav className="nav-chips" aria-label="Primary">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={currentPath === item.href ? "nav-chip active" : "nav-chip"}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="page-frame">{children}</main>
    </div>
  );
}

