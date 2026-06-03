import React, { useState } from 'react';
import axios from 'axios';
import SubscribeForm from './SubscribeForm';
import { AlertCircle, AlertTriangle, CheckCircle, CloudRain, Wind, Thermometer, MapPin } from 'lucide-react';

const API_BASE_URL = "https://travel-advisory-system.onrender.com";

const Dashboard = () => {
  const [advisories, setAdvisories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeRoute, setActiveRoute] = useState(null);

  const fetchAdvisories = async (origin, destination) => {
    setLoading(true);
    setActiveRoute({ origin, destination });
    try {
      const response = await axios.get(`${API_BASE_URL}/api/advisories`);
      setAdvisories(response.data.advisories);
    } catch (error) {
      console.error("Error fetching advisories:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribeStart = () => {
    setLoading(true);
    setActiveRoute(null); // Clear the previous view to show the loader clearly
  };

  const handleSubscribeSuccess = (origin, destination) => {
    fetchAdvisories(origin, destination);
  };

  const getRiskIcon = (level) => {
    switch (level) {
      case 'High': return <AlertTriangle size={20} />;
      case 'Moderate': return <AlertCircle size={20} />;
      default: return <CheckCircle size={20} />;
    }
  };

  const displayedAdvisories = activeRoute 
    ? advisories.filter(a => a.origin === activeRoute.origin && a.destination === activeRoute.destination)
    : [];

  return (
    <div className="main-layout">
      {/* Left Column: Form */}
      <div>
        <SubscribeForm 
          onSubscribeSuccess={handleSubscribeSuccess} 
          onSubscribeStart={handleSubscribeStart}
        />
      </div>

      {/* Right Column: Cards or Product Info */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {!activeRoute ? (
          <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '1rem', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Real-Time Route Intelligence
            </h2>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              Plan your journey with confidence. Our AI-driven engine analyzes real-time weather, air quality index (AQI), traffic congestion, and severe weather alerts to generate personalized travel advisories for your exact route.
            </p>
            <ul style={{ listStyleType: 'none', padding: 0, margin: 0, color: 'var(--text-primary)' }}>
              <li style={{ marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <CloudRain size={28} color="#3b82f6" /> <span style={{ fontSize: '1.1rem' }}>Live Weather Analysis</span>
              </li>
              <li style={{ marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Wind size={28} color="#10b981" /> <span style={{ fontSize: '1.1rem' }}>Air Quality (AQI) Checks</span>
              </li>
              <li style={{ marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Thermometer size={28} color="#f59e0b" /> <span style={{ fontSize: '1.1rem' }}>Severe Condition Alerts</span>
              </li>
            </ul>
            <p style={{ marginTop: '2rem', fontStyle: 'italic', color: 'var(--text-secondary)', padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '10px', borderLeft: '4px solid var(--accent-primary)' }}>
              Select your origin and destination on the left and subscribe to instantly generate your live risk assessment.
            </p>
          </div>
        ) : loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <div className="loader"></div>
          </div>
        ) : (
          <div className="dashboard-grid">
            {displayedAdvisories.length === 0 ? (
              <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
                <MapPin size={48} style={{ opacity: 0.5, marginBottom: '1rem', display: 'block', margin: '0 auto' }} />
                <h3>Generating advisory...</h3>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Your route has been scheduled for scanning. Please wait a few moments and subscribe again to refresh the card.</p>
              </div>
            ) : (
              displayedAdvisories.map((adv, idx) => (
                <div key={idx} className="glass-card advisory-card">
                  <div className="route-header">
                    <div className="route-title">
                      {adv.origin} <span style={{ color: 'var(--text-secondary)' }}>&rarr;</span> {adv.destination}
                    </div>
                    <div className={`risk-badge risk-${adv.risk_level}`} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {getRiskIcon(adv.risk_level)}
                      {adv.risk_level} Risk
                    </div>
                  </div>

                  <div className="stats-grid">
                    <div className="stat-box">
                      <div className="stat-label">Risk Score</div>
                      <div className="stat-value">{adv.risk_score}/100</div>
                    </div>
                    <div className="stat-box">
                      <div className="stat-label">Weather</div>
                      <div className="stat-value" style={{ textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '6px' }}>
                         {adv.temp ? `${adv.temp}°C` : 'Unknown'}
                      </div>
                    </div>
                    <div className="stat-box">
                      <div className="stat-label">AQI Risk</div>
                      <div className="stat-value">{adv.aqi_label || 'N/A'}</div>
                    </div>
                    <div className="stat-box">
                      <div className="stat-label">Traffic</div>
                      <div className="stat-value">{adv.traffic_score ? `${adv.traffic_score}/100` : 'N/A'}</div>
                    </div>
                  </div>

                  <div className="advisory-text">
                    <strong>Advisory:</strong> {adv.advisory_text}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
