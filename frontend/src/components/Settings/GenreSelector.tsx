import React from 'react';

const GENRES = [
  { value: 'rock', label: 'Rock' },
  { value: 'pop', label: 'Pop' },
  { value: 'hip_hop', label: 'Hip-Hop' },
  { value: 'electronic', label: 'Electronic' },
  { value: 'jazz', label: 'Jazz' },
  { value: 'classical', label: 'Classical' },
  { value: 'r_and_b', label: 'R&B' },
  { value: 'country', label: 'Country' },
  { value: 'metal', label: 'Metal' },
  { value: 'folk', label: 'Folk' },
  { value: 'blues', label: 'Blues' },
  { value: 'reggae', label: 'Reggae' },
  { value: 'latin', label: 'Latin' },
  { value: 'ambient', label: 'Ambient' },
  { value: 'indie', label: 'Indie' },
  { value: 'punk', label: 'Punk' },
  { value: 'soul', label: 'Soul' },
  { value: 'funk', label: 'Funk' },
  { value: 'world', label: 'World' },
  { value: 'other', label: 'Other' },
];

interface GenreSelectorProps {
  value: string;
  onChange: (genre: string) => void;
}

const GenreSelector: React.FC<GenreSelectorProps> = ({ value, onChange }) => {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-300">Genre</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-slate-800 border border-slate-600 text-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="">Select a genre...</option>
        {GENRES.map((g) => (
          <option key={g.value} value={g.value}>
            {g.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default GenreSelector;
