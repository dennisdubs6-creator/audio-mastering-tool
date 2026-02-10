import React, { useEffect, useState } from 'react';
import Modal from '@/components/common/Modal';
import Button from '@/components/common/Button';
import ReferenceCard from './ReferenceCard';
import type { ReferenceTrackResponse, SimilarityMatchResponse } from '@/api/types';
import { AudioAnalysisAPI } from '@/api/client';

interface ReferenceSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: string;
  onSelectReference: (ref: ReferenceTrackResponse) => void;
  apiClient: AudioAnalysisAPI;
}

const ReferenceSelectionModal: React.FC<ReferenceSelectionModalProps> = ({
  isOpen,
  onClose,
  analysisId,
  onSelectReference,
  apiClient,
}) => {
  const [matches, setMatches] = useState<SimilarityMatchResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setSelectedId(null);
      return;
    }

    setLoading(true);
    setError(null);

    apiClient
      .findSimilarTracks(analysisId)
      .then((response) => {
        setMatches(response.matches);
      })
      .catch((err) => {
        setError(err.message || 'Failed to find similar tracks');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, analysisId, apiClient]);

  const handleCompare = () => {
    const match = matches.find((m) => m.reference_id === selectedId);
    if (!match) return;

    const ref: ReferenceTrackResponse = {
      id: match.reference_id,
      track_name: match.track_name,
      artist: match.artist,
      genre: match.genre,
      year: match.year,
      is_builtin: true,
      created_at: new Date().toISOString(),
    };

    onSelectReference(ref);
    onClose();
  };

  return (
    <Modal open={isOpen} onClose={onClose}>
      <h2 className="text-lg font-semibold text-slate-200 mb-4">
        Find Similar Tracks
      </h2>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          <span className="ml-3 text-slate-400">Searching...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && matches.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
          No matching reference tracks found.
        </p>
      )}

      {!loading && matches.length > 0 && (
        <div className="flex flex-col gap-2 max-h-80 overflow-y-auto pr-1">
          {matches.map((match) => (
            <ReferenceCard
              key={match.reference_id}
              reference={match}
              isSelected={selectedId === match.reference_id}
              onSelect={() => setSelectedId(match.reference_id)}
            />
          ))}
        </div>
      )}

      <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="primary"
          disabled={!selectedId}
          onClick={handleCompare}
        >
          Compare
        </Button>
      </div>
    </Modal>
  );
};

export default ReferenceSelectionModal;
