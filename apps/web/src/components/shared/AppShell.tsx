"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  const navItems = [
    {
      label: "Home",
      href: "/",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "20px", height: "20px" }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
      ),
    },
    {
      label: "Media Audit",
      href: "/media",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "20px", height: "20px" }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 2.25-4.5 2.25V9.75z" />
        </svg>
      ),
    },
    {
      label: "Rumour Audit",
      href: "/rumour",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "20px", height: "20px" }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      ),
    },
  ];

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      {/* Mobile Drawer Backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(4px)",
            zIndex: 99,
          }}
        />
      )}

      {/* LEFT SIDEBAR (SHRINKABLE) */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""} ${collapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          {!collapsed ? (
            <Link href="/" className="sidebar-logo">
              DECEPTR<span>IX</span>
            </Link>
          ) : (
            <Link href="/" className="sidebar-logo" style={{ fontSize: "16px", color: "var(--accent)" }}>
              DX
            </Link>
          )}

          {/* Desktop Collapse / Shrink Toggle Button */}
          <button
            className="sidebar-collapse-btn desktop-only-btn"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expand sidebar" : "Shrink sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Shrink sidebar"}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              style={{
                width: "16px",
                height: "16px",
                transform: collapsed ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.25s ease",
              }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
            </svg>
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer" title={collapsed ? "DECEPTRIX Engine v2.0 (Online)" : undefined}>
          <div className="sidebar-avatar" style={{ background: "rgba(255, 90, 36, 0.15)", color: "var(--accent)", fontWeight: 800 }}>
            DX
          </div>
          {!collapsed && (
            <>
              <div className="sidebar-user-info">
                <div className="sidebar-username">DECEPTRIX Engine</div>
                <div className="sidebar-userstatus">Cluster v2.0 · Live</div>
              </div>
              <div
                className="sidebar-status-dot"
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: "#00d68f",
                  boxShadow: "0 0 8px #00d68f",
                  flexShrink: 0,
                }}
              />
            </>
          )}
        </div>
      </aside>

      {/* TOP HEADER */}
      <header className="top-header">
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Mobile hamburger */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="icon-btn mobile-hamburger-btn"
            aria-label="Open navigation menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "22px", height: "22px" }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          {/* Header shrink toggle for desktop */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="icon-btn desktop-only-btn"
            title={collapsed ? "Expand sidebar" : "Shrink sidebar"}
            style={{ width: "36px", height: "36px" }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              style={{ width: "18px", height: "18px" }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
            </svg>
          </button>

          <Link href="/" className="header-brand sidebar-logo">
            DECEPTR<span>IX</span>
          </Link>
        </div>

        <div className="header-controls">
          <div className="pill-outline" style={{ border: "1px solid rgba(0, 214, 143, 0.3)", backgroundColor: "rgba(0, 214, 143, 0.05)", color: "#00d68f", fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#00d68f", display: "inline-block" }} />
            NODE ONLINE
          </div>
        </div>
      </header>

      {/* MAIN WORKSPACE */}
      <main className="main-workspace">
        <div className="workspace-content">{children}</div>
      </main>

      {/* Global Responsive & Sidebar Styles */}
      <style jsx global>{`
        .sidebar-collapse-btn {
          width: 28px;
          height: 28px;
          border-radius: 6px;
          border: 1px solid var(--border-light);
          background: rgba(255, 255, 255, 0.03);
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .sidebar-collapse-btn:hover {
          background: rgba(255, 255, 255, 0.08);
          color: var(--text-primary);
          border-color: var(--border-hover);
        }
        .mobile-hamburger-btn {
          display: none !important;
        }
        @media (max-width: 1024px) {
          .mobile-hamburger-btn {
            display: flex !important;
          }
          .desktop-only-btn {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
