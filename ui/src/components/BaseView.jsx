import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

const BaseView = ({ onStartRun }) => {
  const [profile, setProfile] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [activeTab, setActiveTab] = useState('upgrades');
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [profRes, metaRes] = await Promise.all([
        fetch(`${API_BASE}/meta/profile`),
        fetch(`${API_BASE}/meta/metadata`)
      ]);
      const profData = await profRes.json();
      const metaData = await metaRes.json();
      setProfile(profData);
      setMetadata(metaData);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch meta data', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpgrade = async (upgradeId) => {
    try {
      const res = await fetch(`${API_BASE}/meta/upgrade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ upgrade_id: upgradeId })
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data.profile);
      } else {
        alert('Upgrade failed: Insufficient scrap or max level');
      }
    } catch (err) {
      console.error('Upgrade request failed', err);
    }
  };

  const handleUnlock = async (archetypeId) => {
    try {
      const res = await fetch(`${API_BASE}/meta/unlock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ archetype_id: archetypeId })
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data.profile);
      } else {
        alert('Unlock failed: Insufficient scrap or already owned');
      }
    } catch (err) {
      console.error('Unlock request failed', err);
    }
  };

  if (loading) return <div className="p-4">LOADING BASE SYSTEMS...</div>;

  return (
    <div className="base-layout">
      <header className="base-header">
        <div>
          <h1 className="font-heading text-3xl font-black uppercase tracking-widest">Forward Operating Base</h1>
          <p className="text-secondary">Sector 7-G // Ashfall Reclamation Project</p>
        </div>
        <div className="scrap-display">
          <span className="text-sm uppercase tracking-tighter opacity-50">Available Scrap</span>
          <span>⚙ {profile.total_scrap}</span>
        </div>
      </header>

      <div className="base-content">
        <div className="shop-container">
          <div className="shop-tabs">
            <button 
              className={`tab-btn ${activeTab === 'upgrades' ? 'active' : ''}`}
              onClick={() => setActiveTab('upgrades')}
            >
              Base Upgrades
            </button>
            <button 
              className={`tab-btn ${activeTab === 'archetypes' ? 'active' : ''}`}
              onClick={() => setActiveTab('archetypes')}
            >
              Archetype Recruitment
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'upgrades' && (
              <div className="upgrade-list">
                {Object.entries(metadata.upgrades).map(([id, meta]) => {
                  const currentLvl = profile.unlock_levels[id] || 0;
                  const cost = metadata.upgrade_costs[currentLvl];
                  const isMax = currentLvl >= meta.max_level;

                  return (
                    <div key={id} className="glass upgrade-card">
                      <div className="upgrade-info">
                        <h3>{meta.name}</h3>
                        <p>{meta.desc}</p>
                      </div>
                      <div className="upgrade-controls">
                        <div className="lvl-indicator">Level {currentLvl} / {meta.max_level}</div>
                        <button 
                          className="btn-primary" 
                          disabled={isMax || profile.total_scrap < cost}
                          onClick={() => handleUpgrade(id)}
                        >
                          {isMax ? 'MAXED' : `Upgrade (⚙ ${cost})`}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {activeTab === 'archetypes' && (
              <div className="upgrade-list">
                {Object.entries(metadata.archetypes).map(([id, meta]) => {
                  const isUnlocked = profile.unlocked_archetypes.includes(id);

                  return (
                    <div key={id} className="glass upgrade-card">
                      <div className="upgrade-info">
                        <h3>{meta.name}</h3>
                        <p>{meta.desc}</p>
                      </div>
                      <div className="upgrade-controls">
                        <button 
                          className="btn-primary" 
                          disabled={isUnlocked || profile.total_scrap < meta.cost}
                          onClick={() => handleUnlock(id)}
                        >
                          {isUnlocked ? 'RECRUITED' : `Recruit (⚙ ${meta.cost})`}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <aside className="base-sidebar">
          <div className="glass stat-box">
             <div className="stat-label">Lifetime Earned</div>
             <div className="stat-value">⚙ {profile.lifetime_scrap_earned}</div>
          </div>
          <div className="glass stat-box">
             <div className="stat-label">Missions Completed</div>
             <div className="stat-value">0</div>
          </div>
          
          <button className="btn-primary start-btn" onClick={onStartRun}>
            Initialize Mission Protocol
          </button>
        </aside>
      </div>
    </div>
  );
};

export default BaseView;
