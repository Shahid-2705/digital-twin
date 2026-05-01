import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, Brain, MessageSquare, Activity,
  AlertTriangle, Send, Loader2, CheckCircle2, Circle
} from 'lucide-react';

/* 
  =============================================================================
  TAILWIND CONFIGURATION REQUIRED
  Add this to your tailwind.config.js to enable the custom design system tokens:
  =============================================================================

  module.exports = {
    theme: {
      extend: {
        colors: {
          dash: {
            bg: '#07070f',
            surface: '#0f0e1a',
            elevated: '#161428',
            border: '#1e1c35',
            active: '#3a3665',
            text: '#e2e0ff',
            muted: '#6b6890',
            accent: '#7c5cfc'
          }
        },
        fontFamily: {
          display: ['"Space Grotesk"', 'sans-serif'],
          mono: ['"JetBrains Mono"', 'monospace'],
          body: ['Inter', 'sans-serif']
        }
      }
    }
  }
*/

const COMPANIES = [
  { id: '1', name: 'Acme Corp', role: 'CEO', cssVar: '#4f8cff' },
  { id: '2', name: 'Wayne Enterprises', role: 'Board', cssVar: '#2dd4bf' },
  { id: '3', name: 'Stark Industries', role: 'Investor', cssVar: '#f59e0b' },
  { id: '4', name: 'Cyberdyne', role: 'Founder', cssVar: '#7c5cfc' },
];

const MODES = [
  { id: 'ceo', label: 'CEO Brain', icon: Brain, color: '#f59e0b' },
  { id: 'advisor', label: 'Advisor Mode', icon: Activity, color: '#4f8cff' },
  { id: 'casual', label: 'Casual Self', icon: MessageSquare, color: '#2dd4bf' },
  { id: 'reflective', label: 'Reflective Self', icon: Terminal, color: '#7c5cfc' },
];

const PIPELINE = [
  { id: 'input', label: 'Input' },
  { id: 'rag', label: 'RAG Retrieval' },
  { id: 'inject', label: 'Context Inject' },
  { id: 'llm', label: 'LLM Stream' },
  { id: 'verdict', label: 'Verdict' },
  { id: 'pnl', label: 'P&L Score' }
];

const VERDICTS = [
  { label: 'GOOD', color: '#2dd4bf' },
  { label: 'RISKY', color: '#f59e0b' },
  { label: 'BAD', color: '#ef4444' }
];

const GlassPanel = ({ children, className = '' }) => (
  <div className={`bg-dash-surface/80 backdrop-blur-xl border border-dash-border rounded-xl flex flex-col ${className}`}>
    {children}
  </div>
);

export default function AiCloneDashboard() {
  const [activeCompany, setActiveCompany] = useState(COMPANIES[0].id);
  const [activeMode, setActiveMode] = useState(MODES[0].id);
  
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  
  const [pipelineState, setPipelineState] = useState('idle');
  const [currentStep, setCurrentStep] = useState(-1);
  const [verdict, setVerdict] = useState(null);
  
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = () => {
    if (!query.trim() || pipelineState === 'running') return;
    
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setQuery('');
    setPipelineState('running');
    setCurrentStep(0);
    setVerdict(null);
    
    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (step < PIPELINE.length) {
        setCurrentStep(step);
        if (PIPELINE[step].id === 'llm') {
          setMessages(prev => [...prev, { role: 'ai', content: '' }]);
          simulateStreaming();
        }
      } else {
        clearInterval(interval);
        setPipelineState('done');
        setVerdict(VERDICTS[Math.floor(Math.random() * VERDICTS.length)]);
      }
    }, 1200);
  };
  
  const simulateStreaming = () => {
    const text = "Based on our cross-reference of recent Q3 data and the provided market conditions, the strategic projection indicates significant alignment. The risk profile is within acceptable variance bounds.";
    let i = 0;
    const streamInt = setInterval(() => {
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg && lastMsg.role === 'ai') {
           lastMsg.content = text.slice(0, i);
        }
        return newMsgs;
      });
      i++;
      if (i > text.length) clearInterval(streamInt);
    }, 30);
  };

  return (
    <div className="w-screen h-screen bg-dash-bg text-dash-text font-body overflow-hidden flex relative selection:bg-dash-accent/30">
      {/* Cinematic Grain Overlay */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.15] mix-blend-overlay"
        style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}
      />
      
      {/* Background Glows */}
      <div className="absolute top-0 left-[20%] w-[500px] h-[500px] bg-dash-accent/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-[10%] w-[400px] h-[400px] bg-[#4f8cff]/10 blur-[100px] rounded-full pointer-events-none" />

      {/* LEFT PANEL: Entities & Modes */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-[240px] flex-shrink-0 p-4 flex flex-col gap-8 z-10 border-r border-dash-border/50 bg-dash-bg/50 backdrop-blur-sm"
      >
        <div>
          <div className="text-dash-muted text-[10px] font-mono tracking-[0.2em] mb-4 font-semibold">ENTITIES</div>
          <div className="flex flex-col gap-3">
            {COMPANIES.map(company => {
              const isActive = activeCompany === company.id;
              return (
                <motion.div
                  key={company.id}
                  whileHover={{ scale: 1.01 }}
                  onClick={() => setActiveCompany(company.id)}
                  className={`relative p-3.5 rounded-lg cursor-pointer border bg-dash-elevated transition-colors overflow-hidden ${
                    isActive ? 'border-dash-active shadow-lg' : 'border-dash-border hover:border-dash-muted'
                  }`}
                  style={{ '--role-color': company.cssVar }}
                >
                  <div 
                    className="absolute left-0 top-0 bottom-0 w-[3px] transition-all duration-300"
                    style={{ 
                      backgroundColor: 'var(--role-color)', 
                      boxShadow: isActive ? '0 0 12px var(--role-color)' : 'none',
                      opacity: isActive ? 1 : 0.5
                    }}
                  />
                  {isActive && (
                    <div 
                      className="absolute inset-0 opacity-[0.08]"
                      style={{ backgroundColor: 'var(--role-color)' }}
                    />
                  )}
                  <div className="font-display font-semibold text-[14px] ml-2 tracking-wide">{company.name}</div>
                  <div 
                    className="mt-1.5 ml-2 text-[10px] font-mono px-2 py-0.5 rounded-full inline-flex border"
                    style={{ 
                      backgroundColor: 'color-mix(in srgb, var(--role-color) 10%, transparent)', 
                      color: 'var(--role-color)',
                      borderColor: 'color-mix(in srgb, var(--role-color) 20%, transparent)'
                    }}
                  >
                    {company.role}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div>
          <div className="text-dash-muted text-[10px] font-mono tracking-[0.2em] mb-4 font-semibold">PERSONALITY MODE</div>
          <div className="flex flex-col gap-2">
            {MODES.map(mode => {
              const isActive = activeMode === mode.id;
              const Icon = mode.icon;
              return (
                <motion.div
                  key={mode.id}
                  onClick={() => setActiveMode(mode.id)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer border transition-all ${
                    isActive ? 'bg-dash-elevated border-dash-active' : 'border-transparent hover:border-dash-border'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={16} color={isActive ? mode.color : '#6b6890'} />
                    <span className={`text-[13px] font-medium ${isActive ? 'text-dash-text' : 'text-dash-muted'}`}>
                      {mode.label}
                    </span>
                  </div>
                  {isActive && (
                    <div className="flex items-center gap-2">
                      <div className="text-[9px] font-mono tracking-wider" style={{ color: mode.color }}>ACTIVE</div>
                      <motion.div 
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: mode.color, boxShadow: `0 0 8px ${mode.color}` }}
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* CENTER PANEL: Query Interface */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
        className="w-[380px] flex-shrink-0 p-4 z-10 flex flex-col"
      >
        <GlassPanel className="flex-1 overflow-hidden shadow-2xl shadow-black/50">
          <div className="p-4 border-b border-dash-border flex items-center justify-between bg-dash-bg/40">
            <div className="text-[10px] font-mono tracking-widest text-dash-muted">QUERY INTERFACE</div>
            <div className="flex items-center gap-2 text-[10px] font-mono px-2 py-1 rounded bg-dash-elevated border border-dash-border">
               <span className="w-2 h-2 rounded-full bg-dash-accent animate-pulse" />
               <span className="text-dash-accent">{MODES.find(m => m.id === activeMode)?.label}</span>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6">
            {messages.length === 0 ? (
              <div className="m-auto flex flex-col items-center gap-4 text-dash-muted">
                <div className="p-4 rounded-full bg-dash-elevated border border-dash-border">
                  <Terminal size={24} opacity={0.5} />
                </div>
                <div className="text-[13px] font-mono">Awaiting input...</div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  key={i} 
                  className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}
                >
                  <div className={`text-[9px] font-mono mb-1.5 tracking-wider ${msg.role === 'user' ? 'text-dash-muted text-right' : 'text-dash-accent'}`}>
                    {msg.role === 'user' ? 'USER' : 'AI ADVISOR'}
                  </div>
                  <div className={`p-3.5 rounded-xl text-[13.5px] leading-relaxed shadow-lg ${
                    msg.role === 'user' 
                      ? 'bg-dash-elevated border border-dash-border text-dash-text rounded-tr-sm' 
                      : 'bg-dash-accent/10 border border-dash-accent/20 text-[#f8f9fa] rounded-tl-sm'
                  }`}>
                    {msg.content || <span className="animate-pulse flex items-center h-4"><span className="w-1.5 h-1.5 bg-dash-accent rounded-full mr-1"/><span className="w-1.5 h-1.5 bg-dash-accent rounded-full mr-1"/><span className="w-1.5 h-1.5 bg-dash-accent rounded-full"/></span>}
                  </div>
                </motion.div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 bg-dash-surface/90 border-t border-dash-border">
            <div className="relative flex items-end bg-dash-elevated border border-dash-border rounded-xl focus-within:border-dash-accent/50 focus-within:shadow-[0_0_15px_rgba(124,92,252,0.1)] transition-all p-2">
              <textarea 
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => {
                  if(e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder="Initialize query sequence..."
                className="w-full bg-transparent resize-none outline-none text-[13px] max-h-[120px] min-h-[44px] px-3 py-2 placeholder-dash-muted"
                disabled={pipelineState === 'running'}
              />
              <button 
                onClick={handleSubmit}
                disabled={!query.trim() || pipelineState === 'running'}
                className="p-2.5 ml-2 rounded-lg bg-dash-accent/20 text-dash-accent hover:bg-dash-accent hover:text-white hover:shadow-[0_0_15px_rgba(124,92,252,0.4)] transition-all disabled:opacity-50 flex-shrink-0"
              >
                {pipelineState === 'running' ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </GlassPanel>
      </motion.div>

      {/* RIGHT PANEL: Pipeline & Output */}
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
        className="flex-1 p-4 z-10 flex flex-col gap-4 overflow-y-auto"
      >
        <GlassPanel className="p-6 flex-shrink-0 shadow-lg">
          <div className="flex justify-between items-center mb-8 border-b border-dash-border/50 pb-4">
            <div className="text-[14px] font-display font-bold tracking-widest text-dash-text flex items-center gap-3">
              <Activity size={18} className="text-dash-accent" />
              PIPELINE
            </div>
            <div className={`px-3 py-1 rounded-sm text-[10px] font-mono tracking-widest border ${
              pipelineState === 'idle' ? 'bg-dash-elevated border-dash-border text-dash-muted' :
              pipelineState === 'running' ? 'bg-dash-accent/10 border-dash-accent/30 text-dash-accent animate-pulse' :
              'bg-[#2dd4bf]/10 border-[#2dd4bf]/30 text-[#2dd4bf]'
            }`}>
              {pipelineState.toUpperCase()}
            </div>
          </div>

          <div className="relative pl-5 flex flex-col gap-7">
            <div className="absolute left-[27px] top-4 bottom-4 w-[2px] bg-dash-border" />
            
            {PIPELINE.map((step, idx) => {
              const status = pipelineState === 'idle' ? 'idle' :
                             currentStep > idx ? 'done' :
                             currentStep === idx ? 'active' : 'idle';
              
              return (
                <div key={step.id} className="relative flex items-center gap-6 z-10">
                  <div className="bg-dash-surface p-1 rounded-full relative">
                    {status === 'done' ? <CheckCircle2 size={18} className="text-[#2dd4bf]" /> :
                     status === 'active' ? <Loader2 size={18} className="text-dash-accent animate-spin" /> :
                     <Circle size={18} className="text-dash-muted" />}
                  </div>
                  
                  <motion.div 
                    animate={{
                      borderColor: status === 'active' ? 'rgba(124,92,252,0.5)' : 'rgba(30,28,53,1)',
                      backgroundColor: status === 'active' ? 'rgba(22,20,40,1)' : 'rgba(15,14,26,0.5)',
                      boxShadow: status === 'active' ? '0 0 20px rgba(124,92,252,0.15)' : 'none',
                      x: status === 'active' ? 5 : 0
                    }}
                    className="flex-1 p-3.5 rounded-lg border flex items-center justify-between"
                  >
                    <div className="font-mono text-[12px] text-dash-text tracking-wide">{step.label}</div>
                    {status === 'active' && (
                      <div className="text-[10px] font-mono text-dash-accent flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-dash-accent rounded-full animate-ping" />
                        PROCESSING
                      </div>
                    )}
                  </motion.div>
                </div>
              );
            })}
          </div>
        </GlassPanel>

        <div className="flex gap-4 min-h-[180px] flex-1">
          {/* VERDICT */}
          <GlassPanel className="flex-1 p-6 relative overflow-hidden flex flex-col justify-center items-center group shadow-lg">
            <div className="absolute top-5 left-5 text-[10px] font-mono tracking-widest text-dash-muted">VERDICT</div>
            <AnimatePresence mode="wait">
              {verdict ? (
                <motion.div
                  key="verdict"
                  initial={{ scale: 0.8, filter: 'blur(10px)', opacity: 0 }}
                  animate={{ scale: 1, filter: 'blur(0px)', opacity: 1 }}
                  transition={{ type: "spring", bounce: 0.4 }}
                  className="flex flex-col items-center gap-4"
                >
                  <motion.div 
                    className="px-10 py-4 rounded-xl border-2 font-display font-bold text-3xl tracking-widest relative"
                    style={{ 
                      borderColor: verdict.color,
                      color: verdict.color,
                      backgroundColor: `${verdict.color}15`,
                    }}
                    animate={{ boxShadow: [`0 0 20px ${verdict.color}40`, `0 0 40px ${verdict.color}60`, `0 0 20px ${verdict.color}40`] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    {verdict.label}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                  </motion.div>
                  <div className="text-[11px] text-dash-muted font-mono flex items-center gap-2 border border-dash-border px-3 py-1 rounded-full bg-dash-elevated">
                    <CheckCircle2 size={12} style={{ color: verdict.color }} /> VERIFIED OUTPUT
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="idle"
                  exit={{ opacity: 0 }}
                  className="text-dash-muted text-[11px] font-mono tracking-widest flex flex-col items-center gap-3 opacity-50"
                >
                  <AlertTriangle size={24} />
                  AWAITING ANALYSIS
                </motion.div>
              )}
            </AnimatePresence>
          </GlassPanel>

          {/* PNL SCORE */}
          <GlassPanel className="flex-[1.5] p-6 flex flex-col justify-center shadow-lg">
             <div className="absolute top-5 left-5 text-[10px] font-mono tracking-widest text-dash-muted">SCENARIO PROJECTIONS</div>
             <div className="w-full flex flex-col gap-5 mt-6">
                {[
                  { label: 'BEST CASE', val: '+24.5%', pct: 85, color: '#2dd4bf' },
                  { label: 'REALISTIC', val: '+12.0%', pct: 60, color: '#4f8cff' },
                  { label: 'WORST CASE', val: '-5.2%', pct: 30, color: '#ef4444' }
                ].map((row, i) => (
                  <div key={i} className="flex items-center gap-5">
                    <div className="w-24 text-[11px] font-mono text-dash-muted tracking-wide">{row.label}</div>
                    <div className="flex-1 h-2 bg-dash-elevated border border-dash-border rounded-full overflow-hidden relative">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: verdict ? `${row.pct}%` : '0%' }}
                        transition={{ duration: 1.2, delay: verdict ? i * 0.15 : 0, ease: "easeOut" }}
                        className="absolute top-0 left-0 bottom-0 rounded-full"
                        style={{ 
                          background: `linear-gradient(90deg, transparent, ${row.color})`,
                          boxShadow: `0 0 10px ${row.color}80` 
                        }}
                      />
                    </div>
                    <div className="w-16 text-right text-[13px] font-mono font-bold" style={{ color: verdict ? row.color : '#3a3665' }}>
                      {verdict ? row.val : '---'}
                    </div>
                  </div>
                ))}
             </div>
          </GlassPanel>
        </div>
      </motion.div>
    </div>
  );
}
