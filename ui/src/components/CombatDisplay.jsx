import React from 'react';

const ENEMY_ASSETS = {
  'mutant_warrior': '/assets/mutant_warrior.png',
  'scrap_drone': '/assets/scrap_drone.png',
  'default': '/assets/mutant_warrior.png'
};

const CombatDisplay = ({ combat, isResolved }) => {
  if (!combat || !combat.enemy) return null;

  const enemy = combat.enemy;
  const hpPercent = (enemy.hp / enemy.max_hp) * 100;
  
  // Map enemy engine ID to visual asset
  let assetKey = 'default';
  if (enemy.id.includes('mutant')) assetKey = 'mutant_warrior';
  if (enemy.id.includes('drone') || enemy.id.includes('robot')) assetKey = 'scrap_drone';

  return (
    <div className={`combat-stage ${isResolved ? 'combat-resolved' : ''}`}>
      <div className="enemy-container">
        <img 
          src={ENEMY_ASSETS[assetKey] || ENEMY_ASSETS.default} 
          alt={enemy.name} 
          className="enemy-portrait"
        />
        <div className="enemy-name">{enemy.name}</div>
        <div className="hp-bar-enemy">
          <div className="hp-fill-enemy" style={{ width: `${hpPercent}%` }}></div>
        </div>
        <div className="text-xs mt-2 opacity-50 uppercase tracking-tighter">
          Hostile Signature Detected // HP: {enemy.hp} / {enemy.max_hp}
        </div>
      </div>
      
      {combat.victory ? (
        <div className="text-accent-primary font-black animate-bounce mt-4">VICTORY</div>
      ) : isResolved && !combat.victory ? (
        <div className="text-accent-danger font-black mt-4">TERMINATED</div>
      ) : (
        <div className="text-accent-danger animate-pulse mt-4">ENGAGED IN COMBAT</div>
      )}
    </div>
  );
};

export default CombatDisplay;
