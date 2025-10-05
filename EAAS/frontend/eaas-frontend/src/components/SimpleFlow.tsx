import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '../store/useStore';
import { registerUser } from '../api/api';
import { generateKeyPair } from '../lib/crypto';
import AnimatedBackground from './AnimatedBackground';

type Step = 'welcome' | 'username' | 'role' | 'room' | 'complete';

interface FlowData {
  username: string;
  role: 'BUYER' | 'SELLER';
  roomPhrase: string;
}

const SimpleFlow: React.FC = () => {
  const navigate = useNavigate();
  const { setUser } = useUserStore();
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [flowData, setFlowData] = useState<FlowData>({
    username: '',
    role: 'BUYER',
    roomPhrase: ''
  });
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [textVisible, setTextVisible] = useState(false);
  const [inputVisible, setInputVisible] = useState(false);
  const [buttonVisible, setButtonVisible] = useState(false);

  // Animation sequence when step changes
  useEffect(() => {
    setTextVisible(false);
    setInputVisible(false);
    setButtonVisible(false);
    
    const timer1 = setTimeout(() => setTextVisible(true), 100);
    const timer2 = setTimeout(() => setInputVisible(true), 800);
    const timer3 = setTimeout(() => setButtonVisible(true), 1200);
    
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [currentStep]);

  const handleNext = async () => {
    if (currentStep === 'welcome') {
      setCurrentStep('username');
    } else if (currentStep === 'username') {
      if (!inputValue.trim()) {
        setError('Username is required');
        return;
      }
      if (inputValue.length < 3) {
        setError('Username must be at least 3 characters');
        return;
      }
      setFlowData(prev => ({ ...prev, username: inputValue.trim().toLowerCase() }));
      setInputValue('');
      setError('');
      setCurrentStep('role');
    } else if (currentStep === 'role') {
      if (!inputValue.trim()) {
        setError('Please select a role');
        return;
      }
      const role = inputValue.toUpperCase() as 'BUYER' | 'SELLER';
      setFlowData(prev => ({ ...prev, role }));
      setInputValue('');
      setError('');
      setCurrentStep('room');
    } else if (currentStep === 'room') {
      if (!inputValue.trim()) {
        setError('Please enter room phrase or amount');
        return;
      }
      
      setLoading(true);
      setError('');
      
      try {
        const { publicKey, publicKeyHex, privateKeyHex } = generateKeyPair();
        const response = await registerUser(
          flowData.username,
          flowData.role,
          publicKey
        );

        setUser({
          user_id: response.data.user_id,
          username: response.data.username,
          role: response.data.role,
          public_key: publicKeyHex,
          private_key: privateKeyHex,
        });

        navigate(`/room/${inputValue.trim().toLowerCase()}`);
      } catch (err: any) {
        console.error('Registration Error:', err);
        setError(err.response?.data?.detail || 'Registration failed');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNext();
    }
  };

  const getStepContent = () => {
    switch (currentStep) {
      case 'welcome':
        return {
          title: 'Welcome to EAAS',
          subtitle: 'Escrow as a Service',
          placeholder: 'Press Enter to continue',
          inputType: 'text',
          disabled: false
        };
      case 'username':
        return {
          title: 'What is your username?',
          subtitle: '',
          placeholder: 'Enter your username',
          inputType: 'text',
          disabled: false
        };
      case 'role':
        return {
          title: 'Are you a buyer or seller?',
          subtitle: '',
          placeholder: 'Type "buyer" or "seller"',
          inputType: 'text',
          disabled: false
        };
      case 'room':
        return {
          title: flowData.role === 'SELLER' ? 'What amount for your transaction?' : 'Enter room phrase to join',
          subtitle: '',
          placeholder: flowData.role === 'SELLER' ? 'Enter amount (e.g., 500)' : 'Enter room phrase',
          inputType: flowData.role === 'SELLER' ? 'number' : 'text',
          disabled: false
        };
      default:
        return {
          title: '',
          subtitle: '',
          placeholder: '',
          inputType: 'text',
          disabled: true
        };
    }
  };

  const getBackgroundStatus = () => {
    switch (currentStep) {
      case 'welcome':
        return 'welcome';
      case 'username':
        return 'username';
      case 'role':
        return 'role';
      case 'room':
        return 'room';
      default:
        return 'welcome';
    }
  };

  const content = getStepContent();

  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground status={getBackgroundStatus()} />
      
      <div className="relative z-10 flex items-center justify-center min-h-screen">
        <div className="text-center space-y-16 max-w-6xl px-8">
          {/* Main Title - Large cursive font that fades in and slides up */}
          <div 
            className={`transition-all duration-1000 ease-out ${
              textVisible 
                ? 'opacity-100 transform translate-y-0' 
                : 'opacity-0 transform translate-y-8'
            }`}
          >
            <h1 
              className="text-8xl md:text-9xl lg:text-[12rem] font-light text-white leading-none tracking-tight"
              style={{ 
                fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
                textShadow: '0 0 30px rgba(255,255,255,0.3)'
              }}
            >
              {content.title}
            </h1>
            {content.subtitle && (
              <p 
                className="text-4xl md:text-5xl text-gray-300 mt-8 font-light"
                style={{ 
                  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
                  textShadow: '0 0 20px rgba(255,255,255,0.2)'
                }}
              >
                {content.subtitle}
              </p>
            )}
          </div>

          {/* Input Field - Fades in below the text */}
          <div 
            className={`transition-all duration-800 ease-out ${
              inputVisible 
                ? 'opacity-100 transform translate-y-0' 
                : 'opacity-0 transform translate-y-4'
            }`}
          >
            <input
              type={content.inputType}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={content.placeholder}
              disabled={content.disabled}
              className="w-full max-w-2xl mx-auto px-8 py-6 text-2xl text-center bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:border-white/60 focus:bg-white/10 focus:ring-4 focus:ring-white/10 transition-all duration-300"
              style={{ 
                fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
                fontWeight: '300'
              }}
              autoFocus
            />
            
            {error && (
              <p 
                className="text-red-400 text-xl mt-6 font-light"
                style={{ 
                  fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
                }}
              >
                {error}
              </p>
            )}
          </div>

           {/* Button - Only show for welcome step */}
           {currentStep === 'welcome' && (
             <div 
               className={`transition-all duration-600 ease-out ${
                 buttonVisible 
                   ? 'opacity-100 transform translate-y-0' 
                   : 'opacity-0 transform translate-y-4'
               }`}
             >
               <button
                 onClick={handleNext}
                 className="px-16 py-6 text-3xl text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300 font-light"
                 style={{ 
                   fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
                 }}
               >
                 {loading ? 'Loading...' : 'Continue'}
               </button>
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default SimpleFlow;
