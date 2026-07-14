import './Navbar.css';

interface NavLink {
  label: string;
  href: string;
  active?: boolean;
}

const links: NavLink[] = [
  { label: 'Home', href: '/', active: true },
  { label: 'Courts', href: '#courts' },
  { label: 'Bookings', href: '#bookings' },
  { label: 'About', href: '#about' },
];

export default function Navbar() {
  return (
    <div className="navbar-wrapper">
      <nav className="navbar">
        <a href="/" className="navbar-logo">
          <div className="navbar-logo-icon">
            <div className="navbar-logo-icon-left" />
            <div className="navbar-logo-icon-right" />
          </div>
          <span className="navbar-wordmark">Courtenis</span>
        </a>

        <ul className="navbar-links">
          {links.map((link) => (
            <li key={link.label}>
              <a
                href={link.href}
                className={`navbar-link${link.active ? ' active' : ''}`}
              >
                {link.active && <span className="navbar-link-dot" />}
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <button className="navbar-cta" type="button">
          Join Our Membership
        </button>
      </nav>
    </div>
  );
}
