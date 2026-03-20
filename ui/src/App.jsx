import React, { useState, useEffect } from 'react';
import ResourcePanel from './components/ResourcePanel';
import StoryViewport from './components/StoryViewport';
import ActionConsole from './components/ActionConsole';
import BaseView from './components/BaseView';
import CharacterCreator from './components/CharacterCreator';
import LevelUpModal from './components/LevelUpModal';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [view, setView] = useState('base'); // 'base' | 'creator' | 'run'
  const [gameState, setGameState] = useState(null);
  const [lastOutcome, setLastOutcome] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [showLevelUp, setShowLevelUp] = useState(false);

  const fetchState = async () => {
    try {
      const res = await fetch(`${API_BASE}/run/state`);
      if (res.ok) {
        const data = await res.json();
        setGameState(data);
        setView('run');
      }
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  const startNewRun = async (profileData = null) => {
    setLoading(true);
    setLastOutcome(null);
    try {
      const seed = Math.floor(Math.random() * 1000);
      const res = await fetch(`${API_BASE}/run/start?seed=${seed}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: profileData ? JSON.stringify(profileData) : null
      });
      const data = await res.json();
      setGameState(data);
      setView('run');
      setLoading(false);
      setError(null);
    } catch (err) {
      setError('Failed to start run');
      setLoading(false);
    }
  };

  const handleSelect = async (index) => {
    try {
      const res = await fetch(`${API_BASE}/run/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ option_index: index })
      });
      const data = await res.json();
      setGameState(data.state);
      setLastOutcome(data.outcome);
      if (data.state.player.character?.can_level_up) {
        setShowLevelUp(true);
      }
    } catch (err) {
      console.error('Action failed', err);
    }
  };

  const handlePerkSelect = async (perkId) => {
    try {
      const res = await fetch(`${API_BASE}/run/level_up/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ perk_id: perkId })
      });
      const data = await res.json();
      if (data.success) {
        setGameState(data.state);
        setShowLevelUp(false);
      }
    } catch (err) {
      console.error('Perk selection failed', err);
    }
  };

  const handleMove = async (nodeId) => {
    setLastOutcome(null);
    try {
      const res = await fetch(`${API_BASE}/run/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ next_node_id: nodeId })
      });
      const data = await res.json();
      setGameState(data);
      if (data.player.character?.can_level_up) {
        setShowLevelUp(true);
      }
    } catch (err) {
      console.error('Movement failed', err);
    }
  };

  const handleCampAction = async (option) => {
    try {
      const res = await fetch(`${API_BASE}/run/camp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ option })
      });
      const data = await res.json();
      setGameState(data.state);
      setLastOutcome({ log: data.detail.log, message: data.detail.outcome });
    } catch (err) {
      console.error('Camp action failed', err);
    }
  };

  const handleRefineAction = async (slot, action) => {
    try {
      const res = await fetch(`${API_BASE}/run/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot, action })
      });
      const data = await res.json();
      setGameState(data.state);
      setLastOutcome({ log: data.detail.log, message: data.detail.outcome });
    } catch (err) {
      console.error('Refine action failed', err);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  if (loading) return <div className="loading-screen">INITIALIZING HUD...</div>;

  if (view === 'base') {
    return <BaseView onStartRun={() => setView('creator')} />;
  }

  if (view === 'creator') {
    return <CharacterCreator onComplete={startNewRun} onCancel={() => setView('base')} />;
  }

  if (!gameState) {
    return (
      <div className="terminal-container">
        <h1 className="typewriter">ASHFALL v1.0</h1>
        <p>SYSTEM OFFLINE. NO ACTIVE RUN DETECTED.</p>
        <button className="btn-primary" onClick={() => setView('base')}>Return to Base</button>
      </div>
    );
  }

  return (
    <div className="dashboard-grid">
      <header className="main-header glass">
        <div className="logo">ASHFALL // EXPLORATION HUD</div>
        <div className="system-status flex gap-4 items-center">
          <span className="text-xs opacity-50">SEED: {gameState.run.map_seed}</span>
          <button className="btn-primary" onClick={() => setShowHelp(!showHelp)} style={{padding: '4px 12px', fontSize: '0.7rem', background: 'var(--accent-secondary)'}}>Help</button>
          <button className="btn-primary" onClick={() => setView('base')} style={{padding: '4px 12px', fontSize: '0.7rem'}}>Abort Mission</button>
        </div>
      </header>

      {showHelp && (
        <div className="glass p-6 fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md border-accent-secondary">
          <h2 className="text-accent-secondary font-black mb-4">SURVIVAL HANDBOOK</h2>
          <ul className="text-sm space-y-2 mb-6 opacity-80">
            <li>• Use <strong className="text-accent-primary">SCRAP</strong> at the Base to upgrade your permanent stats.</li>
            <li>• <strong className="text-accent-warning">FOOD</strong> is consumed every move. Ran out = Death.</li>
            <li>• Combat results are shown in the <strong>Action Log</strong>. Look for durability alerts.</li>
            <li>• Use <strong>Camp</strong> nodes to repair equipment and rest.</li>
          </ul>
          <button className="btn-primary w-full" onClick={() => setShowHelp(false)}>CLOSE</button>
        </div>
      )}

      <aside className="left-sidebar">
        <ResourcePanel player={gameState.player} />
      </aside>

      <main className="center-content">
        <StoryViewport event={gameState.event} outcome={lastOutcome} />
        <ActionConsole 
          event={gameState.event} 
          map={gameState.map}
          run={gameState.run}
          outcome={lastOutcome}
          onSelect={handleSelect} 
          onMove={handleMove}
          onCamp={handleCampAction}
          onRefine={handleRefineAction}
        />
        {gameState.run.ended && (
          <div className="glass p-4 mt-4 text-center border-danger">
            <h3 className="text-danger">MISSION ENDED: {gameState.run.end_reason}</h3>
            <button className="btn-primary mt-4" onClick={() => setView('base')}>Return to Base</button>
          </div>
        )}
      </main>

      {showLevelUp && <LevelUpModal onSelect={handlePerkSelect} />}

      <aside className="right-sidebar">
        <div className="glass h-full flex flex-col">
           <div className="glass-header">Loadout & Status</div>
           <div className="p-4 flex-1">
              {['weapon', 'armor', 'tool'].map(slot => {
                const item = gameState.player[`${slot}_slot`];
                return (
                  <div key={slot} className="item-slot mb-4">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-secondary uppercase text-xs font-bold">{slot}</span>
                      <span className={`text-xs ${item ? 'text-accent-primary' : 'text-danger'}`}>{item ? item.rarity : 'EMPTY'}</span>
                    </div>
                    <div className="font-bold">{item ? item.id.replace(/_/g, ' ') : 'NONE'}</div>
                    {item && (
                      <div className="mt-2">
                         <div className="flex justify-between text-xs mb-1">
                           <span>Durability</span>
                           <span>{item.durability} / {item.max_durability}</span>
                         </div>
                         <div className="resource-bar">
                           <div 
                             className="resource-fill" 
                             style={{
                               width: `${(item.durability / item.max_durability) * 100}%`,
                               backgroundColor: item.durability < 3 ? 'var(--accent-danger)' : 'var(--accent-secondary)'
                             }}
                           ></div>
                         </div>
                      </div>
                    )}
                  </div>
                );
              })}
           </div>
           {gameState.player.character && (
             <div className="p-4 border-t border-white border-opacity-10">
                <div className="text-xs text-secondary uppercase mb-2">Character Bio</div>
                <div className="font-heading font-bold text-lg">{gameState.player.character.display_name}</div>
                <div className="text-xs text-accent-primary mt-1">Level {gameState.player.character.level} {gameState.player.character.background_id.replace(/_/g, ' ')}</div>
             </div>
           )}
        </div>
      </aside>
    </div>
  );
}

export default App;
