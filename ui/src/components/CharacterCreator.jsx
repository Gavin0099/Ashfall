import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

const CharacterCreator = ({ onComplete, onCancel }) => {
  const [options, setOptions] = useState(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);

  // Selection state
  const [name, setName] = useState('');
  const [selectedBg, setSelectedBg] = useState(null);
  const [selectedTraits, setSelectedTraits] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/character/options`)
      .then(res => res.json())
      .then(data => {
        setOptions(data);
        setLoading(false);
      });
  }, []);

  const handleToggleTrait = (trait) => {
    if (selectedTraits.find(t => t.trait_id === trait.trait_id)) {
      setSelectedTraits(selectedTraits.filter(t => t.trait_id !== trait.trait_id));
    } else if (selectedTraits.length < 2) {
      setSelectedTraits([...selectedTraits, trait]);
    }
  };

  const handleFinish = () => {
    const profile = {
      background_id: selectedBg.background_id,
      display_name: name || 'Survivor',
      special: selectedBg.special_preset,
      traits: selectedTraits.map(t => t.trait_id),
      tags: [...selectedBg.granted_tags, ...selectedTraits.flatMap(t => t.granted_tags || [])]
    };
    onComplete(profile);
  };

  if (loading) return <div className="p-4">LOADING CHARACTER DATA...</div>;

  return (
    <div className="creator-container">
      <header className="flex justify-between items-center border-b border-white border-opacity-10 pb-4">
        <h2 className="font-heading text-2xl font-bold uppercase tracking-widest">Character Creation</h2>
        <div className="text-secondary">Step {step} / 3</div>
      </header>

      {step === 1 && (
        <div className="creator-step">
          <h3 className="mb-4">Assign Identity</h3>
          <p className="text-secondary mb-6">How shall the wastes remember you?</p>
          <input 
            className="name-input" 
            placeholder="Enter Name..." 
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <div className="mt-8 flex justify-end">
            <button className="btn-primary" onClick={() => setStep(2)}>Next: Choose Background</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="creator-step">
          <h3 className="mb-4">Choose Background</h3>
          <p className="text-secondary">Your past shapes your starting capabilities.</p>
          <div className="bg-grid">
            {options.backgrounds.map(bg => (
              <div 
                key={bg.background_id}
                className={`glass selectable-card ${selectedBg?.background_id === bg.background_id ? 'selected' : ''}`}
                onClick={() => setSelectedBg(bg)}
              >
                <div className="font-bold text-lg mb-2">{bg.display_name}</div>
                <div className="text-xs text-secondary mb-4">{bg.description}</div>
                <div className="stat-preview">
                  {Object.entries(bg.special_preset).map(([s, v]) => (
                    <div key={s} className="stat-pill">{s[0].toUpperCase()}:{v}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-8 flex justify-between">
            <button className="btn-action" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary" disabled={!selectedBg} onClick={() => setStep(3)}>Next: Select Traits</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="creator-step">
          <h3 className="mb-4">Select Traits</h3>
          <p className="text-secondary mb-6">Unique quirks that define your survival style (Max 2).</p>
          <div className="bg-grid">
            {options.traits.map(tr => {
              const isSelected = selectedTraits.find(t => t.trait_id === tr.trait_id);
              return (
                <div 
                  key={tr.trait_id}
                  className={`glass selectable-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleToggleTrait(tr)}
                >
                  <div className="font-bold mb-1">{tr.display_name}</div>
                  <div className="text-xs text-secondary">{tr.description}</div>
                </div>
              );
            })}
          </div>
          <div className="mt-8 flex justify-between">
            <button className="btn-action" onClick={() => setStep(2)}>Back</button>
            <button className="btn-primary" onClick={handleFinish}>Confirm & Initialize Mission</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CharacterCreator;
