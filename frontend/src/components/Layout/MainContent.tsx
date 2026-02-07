import React from 'react';

interface MainContentProps {
  children: React.ReactNode;
}

const MainContent: React.FC<MainContentProps> = ({ children }) => {
  return (
    <main className="flex-1 overflow-y-auto bg-slate-950 p-6">
      {children}
    </main>
  );
};

export default MainContent;
