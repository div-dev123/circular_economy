import React, { useState } from 'react';
import './Marketplace.css';

const Marketplace = () => {
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const wasteListings = [
    {
      id: 1,
      title: "Industrial Plastic Waste",
      type: "plastic",
      quantity: "500 tons",
      location: "Chicago, IL",
      price: "$150/ton",
      description: "High-density polyethylene from manufacturing process",
      company: "Plastic Manufacturing Co.",
      posted: "2 days ago",
      image: "📦"
    },
    {
      id: 2,
      title: "Textile Scraps",
      type: "textile",
      quantity: "200 tons",
      location: "Los Angeles, CA",
      price: "$80/ton",
      description: "Cotton and polyester fabric remnants from apparel production",
      company: "Fashion Industries Ltd.",
      posted: "1 day ago",
      image: "👕"
    },
    {
      id: 3,
      title: "Metal Shavings",
      type: "metal",
      quantity: "150 tons",
      location: "Detroit, MI",
      price: "$200/ton",
      description: "Steel and aluminum machining waste from automotive parts",
      company: "Auto Parts Manufacturing",
      posted: "3 days ago",
      image: "⚙️"
    },
    {
      id: 4,
      title: "Food Processing Waste",
      type: "organic",
      quantity: "50 tons",
      location: "Portland, OR",
      price: "$50/ton",
      description: "Organic waste from food processing facility, suitable for composting",
      company: "Pacific Food Processors",
      posted: "1 week ago",
      image: "🍎"
    },
    {
      id: 5,
      title: "Construction Debris",
      type: "construction",
      quantity: "1000 tons",
      location: "Austin, TX",
      price: "$75/ton",
      description: "Concrete and masonry materials from construction site",
      company: "Texas Construction Group",
      posted: "5 days ago",
      image: "🏗️"
    },
    {
      id: 6,
      title: "Electronic Components",
      type: "electronic",
      quantity: "50 tons",
      location: "San Jose, CA",
      price: "$300/ton",
      description: "Recyclable electronic components and circuit boards",
      company: "Tech Electronics Inc.",
      posted: "4 days ago",
      image: "💻"
    }
  ];

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
              <h3>No listings found</h3>
              <p>Try adjusting your search or filter criteria</p>
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