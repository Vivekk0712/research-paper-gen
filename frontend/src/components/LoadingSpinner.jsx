import React from 'react'
import { Loader2, Brain, Sparkles } from 'lucide-react'

const LoadingSpinner = ({ 
  size = 'md', 
  variant = 'default', 
  text = 'Loading...', 
  showText = true 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  }

  if (variant === 'ai') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="relative">
          <div className={`${sizeClasses[size]} border-4 border-purple-200 border-t-purple-500 rounded-full animate-spin`}></div>
          <Brain className={`${sizeClasses[size === 'xl' ? 'md' : 'sm']} text-purple-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2`} />
        </div>
        {showText && (
          <div className="text-center">
            <p className={`${textSizeClasses[size]} text-white font-medium`}>{text}</p>
            <div className="flex items-center justify-center mt-2 space-x-1">
              <Sparkles className="w-3 h-3 text-purple-400 animate-pulse" />
              <span className="text-xs text-purple-300">AI Processing</span>
              <Sparkles className="w-3 h-3 text-purple-400 animate-pulse" style={{ animationDelay: '0.5s' }} />
            </div>
          </div>
        )}
      </div>
    )
  }

  if (variant === 'dots') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="flex space-x-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={`${size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'} bg-purple-500 rounded-full animate-bounce`}
              style={{ animationDelay: `${i * 0.2}s` }}
            ></div>
          ))}
        </div>
        {showText && (
          <p className={`${textSizeClasses[size]} text-white font-medium`}>{text}</p>
        )}
      </div>
    )
  }

  if (variant === 'pulse') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className={`${sizeClasses[size]} bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse`}></div>
        {showText && (
          <p className={`${textSizeClasses[size]} text-white font-medium`}>{text}</p>
        )}
      </div>
    )
  }

  // Default spinner
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <Loader2 className={`${sizeClasses[size]} text-purple-500 animate-spin`} />
      {showText && (
        <p className={`${textSizeClasses[size]} text-white font-medium`}>{text}</p>
      )}
    </div>
  )
}

export default LoadingSpinner