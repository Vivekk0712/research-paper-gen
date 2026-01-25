import { useState, useEffect } from 'react'
import { 
  FileText, Calendar, Users, Tag, ArrowRight, 
  Loader2, AlertCircle, Plus, Eye, Upload, CheckCircle
} from 'lucide-react'
import { apiService } from '../config/api'

const PapersList = ({ onSelectPaper, onCreateNew }) => {
  const [papers, setPapers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [paperFiles, setPaperFiles] = useState({})

  useEffect(() => {
    loadPapers()
  }, [])

  const loadPapers = async () => {
    try {
      setIsLoading(true)
      const papersList = await apiService.listPapers()
      setPapers(papersList)
      
      // Load file counts for each paper
      const filesData = {}
      for (const paper of papersList) {
        try {
          const files = await apiService.getFiles(paper.paper_id)
          filesData[paper.paper_id] = files.length
        } catch (error) {
          filesData[paper.paper_id] = 0
        }
      }
      setPaperFiles(filesData)
      
    } catch (err) {
      setError(`Failed to load papers: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'bg-yellow-500/20 text-yellow-300 border-yellow-300/30'
      case 'in_progress': return 'bg-blue-500/20 text-blue-300 border-blue-300/30'
      case 'completed': return 'bg-green-500/20 text-green-300 border-green-300/30'
      default: return 'bg-gray-500/20 text-gray-300 border-gray-300/30'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Loading your papers...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-500/20 backdrop-blur-sm border border-red-300/30 rounded-xl p-6 text-center">
        <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
        <p className="text-red-300 mb-4">{error}</p>
        <button
          onClick={loadPapers}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Your Papers</h2>
        <button
          onClick={onCreateNew}
          className="flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300"
        >
          <Plus className="w-5 h-5 mr-2" />
          Create New Paper
        </button>
      </div>

      {papers.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Papers Yet</h3>
          <p className="text-gray-300 mb-6">Create your first IEEE research paper to get started</p>
          <button
            onClick={onCreateNew}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300"
          >
            <Plus className="w-5 h-5 mr-2 inline" />
            Create Your First Paper
          </button>
        </div>
      ) : (
        <div className="grid gap-6">
          {papers.map((paper) => (
            <div
              key={paper.paper_id}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 cursor-pointer group"
              onClick={() => onSelectPaper(paper)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <FileText className="w-6 h-6 text-purple-400" />
                    <h3 className="text-xl font-semibold text-white group-hover:text-purple-300 transition-colors">
                      {paper.title}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(paper.status)}`}>
                      {paper.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="grid md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center text-gray-300">
                      <Tag className="w-4 h-4 mr-2 text-purple-400" />
                      <span className="text-sm">{paper.domain}</span>
                    </div>
                    
                    <div className="flex items-center text-gray-300">
                      <Users className="w-4 h-4 mr-2 text-purple-400" />
                      <span className="text-sm">{paper.authors.length} author{paper.authors.length !== 1 ? 's' : ''}</span>
                    </div>
                    
                    <div className="flex items-center text-gray-300">
                      <Upload className="w-4 h-4 mr-2 text-purple-400" />
                      <span className="text-sm">
                        {paperFiles[paper.paper_id] || 0} file{(paperFiles[paper.paper_id] || 0) !== 1 ? 's' : ''}
                        {paperFiles[paper.paper_id] > 0 && <CheckCircle className="w-3 h-3 ml-1 text-green-400 inline" />}
                      </span>
                    </div>
                    
                    <div className="flex items-center text-gray-300">
                      <Calendar className="w-4 h-4 mr-2 text-purple-400" />
                      <span className="text-sm">{formatDate(paper.created_at)}</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    {paper.keywords.slice(0, 3).map((keyword, index) => (
                      <span
                        key={index}
                        className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded-lg text-xs"
                      >
                        {keyword}
                      </span>
                    ))}
                    {paper.keywords.length > 3 && (
                      <span className="text-gray-400 text-xs px-2 py-1">
                        +{paper.keywords.length - 3} more
                      </span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-400">
                    Authors: {paper.authors.join(', ')}
                  </div>
                </div>
                
                <div className="flex items-center text-purple-400 group-hover:text-purple-300 transition-colors">
                  <Eye className="w-5 h-5 mr-2" />
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PapersList