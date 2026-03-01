import React, { useState } from 'react';
import './Marketplace.css';

const Marketplace = () => {
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [wasteListings, setWasteListings] = useState([]);
  const [loading, setLoading] = useState(false);

  // Authentication is now handled by ProtectedRoute

  // In a real application, fetch listings from the backend
  // useEffect(() => {
  //   fetchListings();
  // }, []);

  // const fetchListings = async () => {
  //   setLoading(true);
  //   try {
  //     const response = await fetch('/api/search');
  //     const data = await response.json();
  //     setWasteListings(data.results || []);
  //   } catch (error) {
  //     console.error('Error fetching listings:', error);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const filters = [
    { id: 'all', label: 'All Waste Types', icon: '🗑️' },
    { id: 'plastic', label: 'Plastic', icon: '🥤' },
    { id: 'metal', label: 'Metal', icon: '🔧' },
    { id: 'textile', label: 'Textile', icon: '🧵' },
    { id: 'organic', label: 'Organic', icon: '🌱' },
    { id: 'construction', label: 'Construction', icon: '🏗️' },
    { id: 'electronic', label: 'Electronic', icon: '🔌' }
  ];

  const filteredListings = wasteListings.filter(listing => {
    const matchesFilter = activeFilter === 'all' || listing.type === activeFilter;
    const matchesSearch = listing.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                         listing.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="marketplace">
      <section className="marketplace-hero">
        <div className="container">
          <h1>Waste Marketplace</h1>
          <p className="subtitle">Connect with partners to transform waste into valuable resources</p>
        </div>
      </section>

      <section className="marketplace-content">
        <div className="container">
          <div className="marketplace-header">
            <div className="search-bar">
              <input
                type="text"
                placeholder="Search waste types, companies, or locations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
              <button className="search-button">🔍</button>
            </div>
            
            <div className="filters">
              {filters.map(filter => (
                <button
                  key={filter.id}
                  className={`filter-button ${activeFilter === filter.id ? 'active' : ''}`}
                  onClick={() => setActiveFilter(filter.id)}
                >
                  <span className="filter-icon">{filter.icon}</span>
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          <div className="listings-grid">
            {filteredListings.map(listing => (
              <div key={listing.id} className="listing-card">
                <div className="listing-header">
                  <div className="listing-icon">{listing.image}</div>
                  <div className="listing-meta">
                    <span className="listing-type">{listing.type}</span>
                    <span className="listing-time">{listing.posted}</span>
                  </div>
                </div>
                
                <h3 className="listing-title">{listing.title}</h3>
                <p className="listing-description">{listing.description}</p>
                
                <div className="listing-details">
                  <div className="detail-item">
                    <span className="detail-label">Quantity:</span>
                    <span className="detail-value">{listing.quantity}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Location:</span>
                    <span className="detail-value">{listing.location}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Price:</span>
                    <span className="detail-value price">{listing.price}</span>
                  </div>
                </div>
                
                <div className="listing-footer">
                  <div className="company-info">
                    <span className="company-name">{listing.company}</span>
                  </div>
                  <div className="listing-actions">
                    <button className="btn btn-secondary">View Details</button>
                    <button className="btn btn-primary">Contact Seller</button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredListings.length === 0 && (
            <div className="no-results">
              <div className="no-results-icon">🔍</div>
              <h3>No listings yet</h3>
              <p>Be the first to list your waste materials on the marketplace!</p>
            </div>
          )}
        </div>
      </section>

      <section className="create-listing-cta">
        <div className="container">
          <div className="cta-content">
            <h2>Have Waste to List?</h2>
            <p>Join our network of businesses transforming waste into opportunity</p>
            <button className="btn btn-primary btn-large">Create Listing</button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Marketplace;