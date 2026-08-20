export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-col">
            <div className="footer-logo">
              DECEPTR<span className="text-orange">IX</span>
            </div>
            <p>
              Design That Builds Brands. A premium studio approach
              to independent creative work.
            </p>
          </div>

          <div className="footer-col">
            <div className="footer-col-title">Quick Links</div>
            <a href="#about">About</a>
            <a href="#services">Services</a>
            <a href="#portfolio">Work</a>
            <a href="#contact">Contact</a>
          </div>

          <div className="footer-col">
            <div className="footer-col-title">Services</div>
            <a href="#">UI/UX Design</a>
            <a href="#">Web Design</a>
            <a href="#">Brand Identity</a>
            <a href="#">Graphic Design</a>
          </div>

          <div className="footer-col">
            <div className="footer-col-title">Contact</div>
            <a href="mailto:hello@example.com">hello@example.com</a>
            <a href="#">+1 (555) 000-0000</a>
            <a href="#">Twitter</a>
            <a href="#">LinkedIn</a>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© 2026 DECEPTRIX. All rights reserved.</span>
          <div style={{ display: "flex", gap: "24px" }}>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms</a>
            <a href="#">Refund Policy</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
