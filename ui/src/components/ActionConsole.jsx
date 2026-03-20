import React from 'react';

const ActionConsole = ({ event, map, run, outcome, onSelect, onMove, onCamp, onRefine }) => {
  if (outcome) {
    return (
      <div className="glass p-4 mt-auto">
        <div className="flex justify-between items-center">
          <div className="text-secondary text-sm italic">Action resolved. Review the log above.</div>
          <button className="btn-primary" onClick={() => onSelect(-1)}>Acknowledge</button>
        </div>
      </div>
    );
  }

  const isCampNode = run.current_node_type === 'camp';
  const isEventMode = event && event.options && event.options.length > 0;

  return (
    <div className="glass p-4 mt-auto">
      <div className="flex flex-col gap-3">
        {isEventMode ? (
          <>
            <div className="text-secondary text-xs uppercase tracking-widest mb-2">Decision Required:</div>
            {event.options.map((opt, i) => (
              <button 
                key={i} 
                className="btn-action" 
                onClick={() => onSelect(i)}
                disabled={!opt.is_met}
              >
                <span>{opt.text}</span>
                {!opt.is_met && <span className="text-danger text-xs">[INSUFFICIENT RESOURCES]</span>}
              </button>
            ))}
          </>
        ) : isCampNode ? (
          <>
            <div className="text-secondary text-xs uppercase tracking-widest mb-2">Camp Activities:</div>
            <div className="grid grid-cols-2 gap-3">
              <button className="btn-action" onClick={() => onCamp(0)}>Rest (Restore HP, Consumes Food)</button>
              <button className="btn-action" onClick={() => onCamp(1)}>Forage (Find Food, Consumes Ammo)</button>
            </div>
            <div className="text-secondary text-xs uppercase tracking-widest mt-4 mb-2">Workshop:</div>
            <div className="grid grid-cols-3 gap-3">
              {['weapon', 'armor', 'tool'].map(slot => (
                <button key={slot} className="btn-action text-xs" onClick={() => onRefine(slot, 'repair')}>
                  Repair {slot.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-white border-opacity-10">
               <div className="text-secondary text-xs uppercase mb-2">Prepare for Departure:</div>
               <div className="grid grid-cols-2 gap-3">
                  {map.connections.map((nodeId) => (
                    <button key={nodeId} className="btn-action border-secondary" onClick={() => onMove(nodeId)}>
                      GO TO {nodeId}
                    </button>
                  ))}
               </div>
            </div>
          </>
        ) : (
          <>
            <div className="text-secondary text-xs uppercase tracking-widest mb-2">Path Selection:</div>
            <div className="grid grid-cols-2 gap-3">
              {map.connections.map((nodeId) => (
                <button 
                  key={nodeId} 
                  className="btn-action border-secondary"
                  onClick={() => onMove(nodeId)}
                >
                   <span>GO TO {nodeId}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ActionConsole;
