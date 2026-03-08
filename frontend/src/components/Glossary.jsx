import { GLOSSARY } from '../constants/glossary.js';

export default function Glossary({ term, children }) {
  const def = GLOSSARY[term];
  if (!def) return <>{children}</>;
  return (
    <span className="glossary-term" data-tip={def}>
      {children}
    </span>
  );
}
