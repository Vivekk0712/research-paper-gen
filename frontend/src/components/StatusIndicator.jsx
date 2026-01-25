import React from 'react'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'

const StatusIndicator = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          bgColor: 'bg-green-500/20',
          borderColor: 'border-green-300/30',
          textColor: 'text-green-300',
          iconColor: 'text-green-400',
          pulseColor: 'bg-green-400'
        }
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          bgColor: 'bg-red-500/20',
          borderColor: 'border-red-300/30',
          textColor: 'text-red-300',
          iconColor: 'text-red-400',
          pulseColor: 'bg-red-400'
        }
      default:
        return {
          icon: Loader2,
          text: 'Connecting...',
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-300/30',
          textColor: 'text-yellow-300',
          iconColor: 'text-yellow-400',
          pulseColor: 'bg-yellow-400'
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <div className={`flex items-center space-x-3 ${config.bgColor} backdrop-blur-sm border ${config.borderColor} rounded-full px-4 py-2`}>
      <div className="relative">
        <Icon className={`w-4 h-4 ${config.iconColor} ${status === 'checking' ? 'animate-spin' : ''}`} />
        {status === 'connected' && (
          <div className={`absolute -top-1 -right-1 w-2 h-2 ${config.pulseColor} rounded-full animate-pulse`}></div>
        )}
      </div>
      <span className={`text-sm font-medium ${config.textColor}`}>
        {config.text}
      </span>
    </div>
  )
}

export default StatusIndicator