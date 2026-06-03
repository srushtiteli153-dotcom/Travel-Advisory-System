import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Mail, MapPin, Bell, AlertCircle, CheckCircle2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';
const STATES_API_URL = 'https://raw.githubusercontent.com/sab99r/Indian-States-And-Districts/master/states-and-districts.json';

const SubscribeForm = ({ onSubscribeSuccess, onSubscribeStart }) => {
  const [email, setEmail] = useState('');
  
  const [indianData, setIndianData] = useState([]);
  
  const [originState, setOriginState] = useState('');
  const [originDistrict, setOriginDistrict] = useState('');
  
  const [destState, setDestState] = useState('');
  const [destDistrict, setDestDistrict] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Fetch Indian states and districts dataset
    const fetchStates = async () => {
      try {
        const response = await axios.get(STATES_API_URL);
        setIndianData(response.data.states);
      } catch (err) {
        console.error("Failed to fetch states data", err);
      }
    };
    fetchStates();
  }, []);

  const getDistrictsForState = (stateName) => {
    if (!stateName) return [];
    const stateObj = indianData.find(s => s.state === stateName);
    return stateObj ? stateObj.districts : [];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    if (onSubscribeStart) onSubscribeStart();

    try {
      const response = await axios.post(`${API_BASE_URL}/api/subscribe`, {
        email,
        origin: originDistrict,
        destination: destDistrict
      });
      
      setMessage({ type: 'success', text: response.data.message });
      
      // Reset form
      setEmail('');
      setOriginState('');
      setOriginDistrict('');
      setDestState('');
      setDestDistrict('');
      
      // Notify parent to refresh dashboard for this route
      if (onSubscribeSuccess) onSubscribeSuccess(originDistrict, destDistrict);
      
    } catch (error) {
      const errorMsg = error.response?.data?.error || "An unexpected error occurred.";
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Bell size={24} color="var(--accent-primary)" />
        Get Travel Alerts
      </h2>

      {message && (
        <div className={`alert-message ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
          {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email Address</label>
          <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
            <Mail size={18} style={{ position: 'absolute', left: '1rem', color: 'var(--text-secondary)' }} />
            <input 
              type="email" 
              className="form-control" 
              style={{ paddingLeft: '2.5rem' }}
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required 
            />
          </div>
        </div>

        <div className="form-group">
          <label>Origin State</label>
          <select 
            className="form-control"
            value={originState}
            onChange={e => {
              setOriginState(e.target.value);
              setOriginDistrict(''); // Reset district on state change
            }}
            required
          >
            <option value="">-- Select State --</option>
            {indianData.map((s, i) => (
              <option key={i} value={s.state}>{s.state}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Origin District</label>
          <select 
            className="form-control"
            value={originDistrict}
            onChange={e => setOriginDistrict(e.target.value)}
            required
            disabled={!originState}
          >
            <option value="">-- Select District --</option>
            {getDistrictsForState(originState).map((d, i) => (
              <option key={i} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Destination State</label>
          <select 
            className="form-control"
            value={destState}
            onChange={e => {
              setDestState(e.target.value);
              setDestDistrict('');
            }}
            required
          >
            <option value="">-- Select State --</option>
            {indianData.map((s, i) => (
              <option key={i} value={s.state}>{s.state}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Destination District</label>
          <select 
            className="form-control"
            value={destDistrict}
            onChange={e => setDestDistrict(e.target.value)}
            required
            disabled={!destState}
          >
            <option value="">-- Select District --</option>
            {getDistrictsForState(destState).map((d, i) => (
              <option key={i} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <button type="submit" className="btn" disabled={loading}>
          {loading ? (
            <div className="loader"></div>
          ) : (
            <>Subscribe & Scan Now <MapPin size={18} /></>
          )}
        </button>
      </form>
    </div>
  );
};

export default SubscribeForm;
