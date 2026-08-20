"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <nav className={`navbar${scrolled ? " scrolled" : ""}`}>
        <div className="navbar-inner">
          <Link href="/" className="nav-logo">
            DECEPTR<span className="text-orange">IX</span>
          </Link>
          <div className="nav-links">
            <Link href="/#services">Services</Link>
            <Link href="/#portfolio">Work</Link>
            <Link href="/media">Media Audit</Link>
            <Link href="/rumour">Rumour Audit</Link>
          </div>
          <Link href="/media" className="nav-cta">
            Let's Talk <span className="btn-arrow">→</span>
          </Link>
          <button
            className="nav-hamburger"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </nav>
      <div className={`mobile-menu${mobileOpen ? " open" : ""}`}>
        <button className="mobile-close" onClick={() => setMobileOpen(false)}>
          ✕
        </button>
        <Link href="/#services" onClick={() => setMobileOpen(false)}>Services</Link>
        <Link href="/#portfolio" onClick={() => setMobileOpen(false)}>Work</Link>
        <Link href="/media" onClick={() => setMobileOpen(false)}>Media Audit</Link>
        <Link href="/rumour" onClick={() => setMobileOpen(false)}>Rumour Audit</Link>
        <Link href="/media" className="btn-primary" onClick={() => setMobileOpen(false)}>
          Let's Talk <span className="btn-arrow">→</span>
        </Link>
      </div>
    </>
  );
}
