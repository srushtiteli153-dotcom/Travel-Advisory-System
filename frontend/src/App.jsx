import React from 'react';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  return (
    <div className="container">
      <header className="header">
        <img src="/logo.png" alt="Logo" className="logo-icon" />
        <h1>Travel Advisory System</h1>
      </header>
      
      <main>
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
