import React, { useState } from 'react';
import './Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Handle form submission
    console.log('Form submitted:', formData);
    alert('Thank you for your message! We will get back to you soon.');
    setFormData({ name: '', email: '', company: '', message: '' });
  };

  return (
    <div className="contact">
      <section className="contact-hero">
        <div className="container">
          <h1>Get In Touch</h1>
          <p className="subtitle">Have questions about our circular economy platform? We're here to help.</p>
        </div>
      </section>

      <section className="contact-content">
        <div className="container">
          <div className="contact-grid">
            <div className="contact-form-section">
              <h2>Send us a message</h2>
              <form className="contact-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="name">Full Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">Email Address</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="company">Company</label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="message">Message</label>
                  <textarea
                    id="message"
                    name="message"
                    rows="6"
                    value={formData.message}
                    onChange={handleChange}
                    required
                  ></textarea>
                </div>
                
                <button type="submit" className="btn btn-primary btn-large">
                  Send Message
                </button>
              </form>
            </div>
            
            <div className="contact-info">
              <h2>Contact Information</h2>
              
              <div className="contact-methods">
                <div className="contact-method">
                  <div className="method-icon">📧</div>
                  <div className="method-content">
                    <h3>Email</h3>
                    <p>info@circulareco.com</p>
                    <p>support@circulareco.com</p>
                  </div>
                </div>
                
                <div className="contact-method">
                  <div className="method-icon">📞</div>
                  <div className="method-content">
                    <h3>Phone</h3>
                    <p>+1 (555) 123-4567</p>
                    <p>Mon-Fri, 9:00 AM - 6:00 PM EST</p>
                  </div>
                </div>
                
                <div className="contact-method">
                  <div className="method-icon">📍</div>
                  <div className="method-content">
                    <h3>Office</h3>
                    <p>123 Sustainability Drive</p>
                    <p>Green Valley, CA 90210</p>
                  </div>
                </div>
              </div>
              
              <div className="support-options">
                <h3>Quick Support</h3>
                <div className="support-grid">
                  <div className="support-card">
                    <div className="support-icon">❓</div>
                    <h4>FAQ</h4>
                    <p>Find answers to common questions</p>
                    <button className="btn btn-secondary">Visit FAQ</button>
                  </div>
                  
                  <div className="support-card">
                    <div className="support-icon">💬</div>
                    <h4>Live Chat</h4>
                    <p>Chat with our support team</p>
                    <button className="btn btn-secondary">Start Chat</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="locations-section">
        <div className="container">
          <div className="section-header">
            <h2>Global Presence</h2>
            <p>We're building circular economy solutions worldwide</p>
          </div>
          
          <div className="locations-grid">
            <div className="location-card">
              <div className="location-flag">�🇳</div>
              <h3>Mumbai</h3>
              <p>Headquarters</p>
              <p>Bandra Kurla Complex, Mumbai</p>
              <p>+91 22 4000 1234</p>
            </div>
            
            <div className="location-card">
              <div className="location-flag">🇮🇳</div>
              <h3>New Delhi</h3>
              <p>Regional Office</p>
              <p>Connaught Place, New Delhi</p>
              <p>+91 11 4000 5678</p>
            </div>
            
            <div className="location-card">
              <div className="location-flag">🇮🇳</div>
              <h3>Bengaluru</h3>
              <p>Tech Hub</p>
              <p>Whitefield, Bengaluru</p>
              <p>+91 80 4000 9012</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Contact;