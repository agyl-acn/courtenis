import Navbar from '../components/Navbar';
import BookingCard from '../components/BookingCard';
import FeaturedCourts from '../components/FeaturedCourts';
import Chatbot from '../components/Chatbot';
import './HomePage.css';

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-overlay" />
        <Navbar />
        <div className="hero-content">
          <div className="hero-left">
            <span className="hero-badge">Welcome to Courtenis</span>
            <h1 className="hero-headline">
              <span className="hero-headline-strikethrough">Your Premier Tennis</span>
              <br />
              Court Booking
              <br />
              Experience
            </h1>
            <p className="hero-subtitle">
              Reserve your favourite tennis court in seconds. Choose from clay,
              hard, and grass surfaces across Jakarta's top venues.
            </p>
            <div className="hero-court-indicator">
              <span className="hero-court-indicator-label">01. &nbsp; Baseline Grounds</span>
              <div className="hero-court-indicator-line" />
            </div>
          </div>

          <div className="hero-right">
            <BookingCard />
          </div>
        </div>
      </section>

      <FeaturedCourts />
      <Chatbot />
    </>
  );
}
