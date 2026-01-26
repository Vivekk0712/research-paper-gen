import React, { useState, useEffect } from 'react'
import { 
  FileText, Upload, Download, Wifi, WifiOff, Sparkles, 
  Brain, Zap, Shield, Clock, Users, ChevronRight,
  Play, Pause, RotateCcw, CheckCircle, AlertCircle
} from 'lucide-react'
import { logConnectionStatus } from './utils/connectionTest'
import { APP_CONFIG } from './config/constants'
import PaperWizard from './components/PaperWizard'
import PapersList from './components/PapersList'
import StatusIndicator from './components/StatusIndicator'
import FeatureCard from './components/FeatureCard'
import AnimatedBackground from './components/AnimatedBackground'

function App() {
  const [currentView, setCurrentView] = useState('home')
  const [connectionStatus, setConnectionStatus] = useState('checking')
  const [isLoading, setIsLoading] = useState(true)
  const [selectedPaper, setSelectedPaper] = useState(null)
  const [embeddingModelReady, setEmbeddingModelReady] = useState(false)

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Quick connection test
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/`)
        
        if (response.ok) {
          setConnectionStatus('connected')
          console.log('✅ Backend connected')
          
          // Check embedding model status in background (non-blocking)
          fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/system/status`)
            .then(res => res.json())
            .then(data => {
              if (data.embedding_model_ready) {
                setEmbeddingModelReady(true)
                console.log('✅ Embedding model is ready!')
              }
            })
            .catch(() => {
              // Silently fail, will poll later
            })
        } else {
          setConnectionStatus('disconnected')
        }
      } catch (error) {
        console.error('Connection test failed:', error)
        setConnectionStatus('disconnected')
      } finally {
        // Show UI after connection check completes
        setIsLoading(false)
      }
    }

    // Start initialization
    initializeApp()
    
    // Poll for embedding model readiness if not ready yet (non-blocking)
    const pollInterval = setInterval(async () => {
      if (!embeddingModelReady) {
        try {
          const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/system/status`)
          const data = await response.json()
          if (data.embedding_model_ready) {
            setEmbeddingModelReady(true)
            console.log('✅ Embedding model is now ready!')
            clearInterval(pollInterval)
          }
        } catch (error) {
          // Silently fail, will retry
        }
      } else {
        clearInterval(pollInterval)
      }
    }, 2000) // Check every 2 seconds
    
    return () => clearInterval(pollInterval)
  }, [embeddingModelReady])

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Generation",
      description: "Advanced RAG system with Gemini AI for intelligent content generation",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: Shield,
      title: "IEEE Compliant",
      description: "Automatically formatted according to IEEE publication standards",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Generate comprehensive papers in minutes, not hours",
      color: "from-yellow-500 to-orange-500"
    },
    {
      icon: Users,
      title: "Collaborative",
      description: "Multi-author support with real-time collaboration features",
      color: "from-green-500 to-emerald-500"
    }
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-purple-200 border-t-purple-500 rounded-full animate-spin mx-auto mb-3"></div>
            <Sparkles className="w-6 h-6 text-purple-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
          </div>
          <h2 className="text-xl font-bold text-white">Loading...</h2>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden transition-all duration-500">
      <AnimatedBackground />
      
      {/* Embedding Model Loading Banner (non-blocking, glassy transparent) */}
      {!embeddingModelReady && connectionStatus === 'connected' && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-purple-500/20 backdrop-blur-md border-b border-purple-400/20 py-2 px-4 animate-fade-in">
          <div className="container mx-auto flex items-center justify-center space-x-3">
            <div className="w-4 h-4 border-2 border-purple-300 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-purple-100 text-sm font-medium drop-shadow-lg">
              AI Engine initializing... (You can use the app now, generation will be ready in a moment)
            </span>
          </div>
        </div>
      )}
      
      {/* Navigation */}
      <nav className="relative z-10 bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">{APP_CONFIG.name}</h1>
                <p className="text-xs text-purple-200">AI Research Assistant</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {!embeddingModelReady && connectionStatus === 'connected' && (
                <div className="flex items-center space-x-2 bg-yellow-500/20 backdrop-blur-sm border border-yellow-300/30 rounded-full px-3 py-1">
                  <Brain className="w-4 h-4 text-yellow-400 animate-pulse" />
                  <span className="text-yellow-300 text-xs font-medium">AI Loading...</span>
                </div>
              )}
              {embeddingModelReady && connectionStatus === 'connected' && (
                <div className="flex items-center space-x-2 bg-green-500/20 backdrop-blur-sm border border-green-300/30 rounded-full px-3 py-1">
                  <Brain className="w-4 h-4 text-green-400" />
                  <span className="text-green-300 text-xs font-medium">AI Ready</span>
                </div>
              )}
              <StatusIndicator status={connectionStatus} />
            </div>
          </div>
        </div>
      </nav>

      {currentView === 'home' && (
        <div className="relative z-10 animate-fade-in">
          {/* Hero Section */}
          <section className="container mx-auto px-6 py-20 text-center">
            <div className="max-w-4xl mx-auto">
              <div className="inline-flex items-center bg-purple-500/20 backdrop-blur-sm border border-purple-300/30 rounded-full px-4 py-2 mb-8">
                <Sparkles className="w-4 h-4 text-purple-300 mr-2" />
                <span className="text-purple-200 text-sm font-medium">Powered by Advanced AI</span>
              </div>
              
              <h1 className="text-6xl font-bold text-white mb-6 leading-tight">
                Generate
                <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"> IEEE Papers </span>
                with AI
              </h1>
              
              <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto leading-relaxed">
                Transform your research ideas into publication-ready IEEE papers using cutting-edge AI technology. 
                Upload references, define your scope, and watch as our AI crafts comprehensive, well-structured papers.
              </p>

              {connectionStatus === 'connected' ? (
                <div className="space-y-4">
                  <button
                    onClick={() => setCurrentView('wizard')}
                    className="group inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl"
                  >
                    <Play className="w-5 h-5 mr-2 group-hover:translate-x-1 transition-transform" />
                    Start Creating Paper
                    <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </button>
                  
                  <button
                    onClick={() => setCurrentView('papers')}
                    className="group inline-flex items-center bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 ml-4"
                  >
                    <FileText className="w-5 h-5 mr-2" />
                    View My Papers
                  </button>
                </div>
              ) : (
                <div className="bg-red-500/20 backdrop-blur-sm border border-red-300/30 rounded-xl p-6 max-w-md mx-auto">
                  <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
                  <h3 className="text-red-300 font-semibold mb-2">Backend Disconnected</h3>
                  <p className="text-red-200 text-sm mb-4">
                    Please start the backend server to begin generating papers.
                  </p>
                  <code className="bg-red-900/30 text-red-200 px-3 py-1 rounded text-xs">
                    python backend/start.py
                  </code>
                </div>
              )}
            </div>
          </section>

          {/* Features Section */}
          <section className="container mx-auto px-6 py-20">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4">Why Choose Our AI Platform?</h2>
              <p className="text-gray-300 text-lg max-w-2xl mx-auto">
                Experience the future of academic writing with our advanced AI-powered research assistant
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <FeatureCard key={index} {...feature} delay={index * 100} />
              ))}
            </div>
          </section>

          {/* Process Section */}
          <section className="container mx-auto px-6 py-20">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4">How It Works</h2>
              <p className="text-gray-300 text-lg">Simple, powerful, and intelligent</p>
            </div>
            
            <div className="max-w-4xl mx-auto">
              <div className="grid md:grid-cols-3 gap-8">
                {[
                  {
                    step: "01",
                    title: "Upload References",
                    description: "Upload your research papers and references in PDF or DOCX format",
                    icon: Upload
                  },
                  {
                    step: "02", 
                    title: "Define Scope",
                    description: "Specify your paper title, domain, authors, and key research areas",
                    icon: FileText
                  },
                  {
                    step: "03",
                    title: "Generate Paper",
                    description: "Our AI analyzes your references and generates IEEE-compliant sections",
                    icon: Sparkles
                  }
                ].map((item, index) => (
                  <div key={index} className="text-center group">
                    <div className="relative mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto group-hover:scale-110 transition-transform duration-300">
                        <item.icon className="w-8 h-8 text-white" />
                      </div>
                      <div className="absolute -top-2 -right-2 w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                        <span className="text-xs font-bold text-white">{item.step}</span>
                      </div>
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                    <p className="text-gray-300">{item.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Stats Section */}
          <section className="container mx-auto px-6 py-20">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-12">
              <div className="grid md:grid-cols-4 gap-8 text-center">
                {[
                  { number: "10K+", label: "Papers Generated" },
                  { number: "95%", label: "Accuracy Rate" },
                  { number: "50+", label: "Research Domains" },
                  { number: "24/7", label: "AI Availability" }
                ].map((stat, index) => (
                  <div key={index} className="group">
                    <div className="text-4xl font-bold text-white mb-2 group-hover:scale-110 transition-transform">
                      {stat.number}
                    </div>
                    <div className="text-gray-300">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}

      {currentView === 'papers' && (
        <div className="relative z-10 container mx-auto px-6 py-20 animate-fade-in">
          <div className="max-w-6xl mx-auto">
            <PapersList 
              onSelectPaper={(paper) => {
                setSelectedPaper(paper)
                setCurrentView('wizard')
              }}
              onCreateNew={() => {
                setSelectedPaper(null)
                setCurrentView('wizard')
              }}
            />
          </div>
        </div>
      )}

      {currentView === 'wizard' && (
        <div className="animate-fade-in">
          <PaperWizard 
            onBack={() => setCurrentView('home')} 
            existingPaper={selectedPaper}
          />
        </div>
      )}
    </div>
  )
}

export default App
