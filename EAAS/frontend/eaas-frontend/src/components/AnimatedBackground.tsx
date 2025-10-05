import React from 'react';
import LiquidEther from './LiquidEther';

interface AnimatedBackgroundProps {
  status?: 'welcome' | 'username' | 'role' | 'room' | 'transaction' | 'dispute' | 'complete';
  className?: string;
}

const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ 
  status = 'welcome', 
  className = '' 
}) => {
  const getColorsForStatus = (status: string) => {
    switch (status) {
      case 'welcome':
        return ['#5227FF', '#FF9FFC', '#B19EEF']; // Purple to pink gradient
      case 'username':
        return ['#00D4FF', '#0099CC', '#0066FF']; // Blue gradient
      case 'role':
        return ['#FF6B6B', '#4ECDC4', '#45B7D1']; // Coral to teal
      case 'room':
        return ['#A8E6CF', '#88D8A3', '#FFD93D']; // Green to yellow
      case 'transaction':
        return ['#FF9A9E', '#FECFEF', '#FECFEF']; // Pink gradient
      case 'dispute':
        return ['#FF6B6B', '#FF8E53', '#FF6B6B']; // Red to orange
      case 'complete':
        return ['#4ECDC4', '#44A08D', '#093637']; // Teal to dark green
      default:
        return ['#5227FF', '#FF9FFC', '#B19EEF'];
    }
  };

  const colors = getColorsForStatus(status);

  return (
    <div 
      className={`fixed inset-0 z-0 ${className}`}
      style={{ 
        width: '100%', 
        height: '100vh', 
        position: 'fixed',
        top: 0,
        left: 0
      }}
    >
      <LiquidEther
        colors={colors}
        mouseForce={20}
        cursorSize={100}
        isViscous={false}
        viscous={30}
        iterationsViscous={32}
        iterationsPoisson={32}
        resolution={0.5}
        isBounce={false}
        autoDemo={true}
        autoSpeed={0.5}
        autoIntensity={2.2}
        takeoverDuration={0.25}
        autoResumeDelay={3000}
        autoRampDuration={0.6}
      />
    </div>
  );
};

export default AnimatedBackground;
