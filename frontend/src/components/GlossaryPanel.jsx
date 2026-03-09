import { GLOSSARY } from '../constants/glossary.js';

export default function GlossaryPanel() {
  return (
    <div className="glass-panel panel-glossary">
      <h2 className="panel-header">Glossario — Sigle e Termini Tecnici</h2>
      <div className="glossary-grid">
        {Object.entries(GLOSSARY).map(([term, def]) => (
          <div key={term} className="glossary-entry">
            <span className="glossary-entry-term">{term}</span>
            <span className="glossary-entry-def">{def}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
