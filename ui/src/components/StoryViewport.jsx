import React, { useEffect, useRef } from 'react';

const StoryViewport = ({ event, outcome }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [outcome, event]);

  return (
    <div className="glass p-6 flex-1 overflow-y-auto min-h-[300px] relative">
      {!outcome ? (
        <article className="prose prose-invert max-w-none">
          <h2 className="font-heading text-xl font-bold text-accent-secondary mb-4">{event.title}</h2>
          <div className="text-lg leading-relaxed opacity-90 whitespace-pre-wrap">{event.description}</div>
        </article>
      ) : (
        <div className="log-container">
          <h2 className="font-heading text-xl font-bold text-accent-primary mb-4">Action Summary</h2>
          <p className="mb-6 text-lg italic">{outcome.message}</p>
          
          {outcome.log && outcome.log.length > 0 && (
            <div className="combat-log font-mono text-xs bg-black bg-opacity-30 p-4 rounded-lg border border-white border-opacity-5">
              <div className="text-secondary uppercase mb-2 opacity-50 tracking-widest">Detail Log:</div>
              {outcome.log.map((line, i) => (
                <div key={i} className="mb-1 py-1 border-b border-white border-opacity-5 last:border-0">
                  {line}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StoryViewport;
