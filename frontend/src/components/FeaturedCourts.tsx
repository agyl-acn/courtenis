import './FeaturedCourts.css';

interface Court {
  name: string;
  location: string;
  type: 'clay' | 'hard' | 'grass';
  typeLabel: string;
  price: string;
}

const COURTS: Court[] = [
  { name: 'Baseline Grounds', location: 'South Jakarta', type: 'clay', typeLabel: 'Clay', price: 'Rp85k/hour' },
  { name: 'Net & Rally Club', location: 'Central Jakarta', type: 'hard', typeLabel: 'Hard', price: 'Rp95k/hour' },
  { name: 'Ace Courts', location: 'North Jakarta', type: 'grass', typeLabel: 'Grass', price: 'Rp110k/hour' },
];

export default function FeaturedCourts() {
  return (
    <section className="featured-courts" id="courts">
      <p className="featured-courts-label">Featured Courts</p>
      <h2 className="featured-courts-title">Find Your Perfect Court</h2>
      <div className="featured-courts-grid">
        {COURTS.map((court) => (
          <div key={court.name} className="court-card">
            <div className={`court-card-header ${court.type}`}>
              <span className="court-card-type-badge">{court.typeLabel}</span>
            </div>
            <div className="court-card-body">
              <p className="court-card-name">{court.name}</p>
              <p className="court-card-location">{court.location}</p>
              <div className="court-card-footer">
                <span className="court-card-price">{court.price}</span>
                <span className="court-card-available">Available</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
