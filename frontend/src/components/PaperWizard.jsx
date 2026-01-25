import { useState, useRef, useEffect } from 'react'
import { 
  ArrowLeft, Upload, FileText, Brain, 
  CheckCircle, AlertCircle, Loader2, Download, Eye,
  X, Plus, Trash2, FileDown
} from 'lucide-react'
import { apiService } from '../config/api'
import { validateFiles, formatFileSize } from '../utils/fileValidation'
import { IEEE_SECTIONS } from '../config/constants'

const PaperWizard = ({ onBack, existingPaper }) => {
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [latexAvailable, setLatexAvailable] = useState(false)
  const fileInputRef = useRef(null)
  
  // Form data - initialize with existing paper if provided
  const [paperData, setPaperData] = useState({
    title: existingPaper?.title || '',
    domain: existingPaper?.domain || '',
    authors: existingPaper?.authors || [''],
    affiliations: existingPaper?.affiliations || [''],
    keywords: existingPaper?.keywords || ['']
  })
  
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [generatedSections, setGeneratedSections] = useState({})
  const [selectedSections, setSelectedSections] = useState(['Abstract', 'Introduction', 'Literature Review'])
  const [paperId, setPaperId] = useState(existingPaper?.paper_id || null)
  const [processingStatus, setProcessingStatus] = useState(null)
  const [generationProgress, setGenerationProgress] = useState({
    isGenerating: false,
    currentSection: '',
    progress: 0,
    sectionsCompleted: 0,
    totalSections: 11
  })

  // Check LaTeX availability and load existing data on component mount
  useEffect(() => {
    const checkLatexStatus = async () => {
      try {
        const status = await apiService.getLatexStatus()
        setLatexAvailable(status.latex_available)
      } catch (error) {
        console.error('Failed to check LaTeX status:', error)
      }
    }
    
    const loadExistingData = async () => {
      if (existingPaper && existingPaper.paper_id) {
        try {
          // Load uploaded files
          const files = await apiService.getFiles(existingPaper.paper_id)
          setUploadedFiles(files)
          
          // Load existing sections
          const sections = await apiService.getSections(existingPaper.paper_id)
          const sectionsMap = {}
          sections.forEach(section => {
            sectionsMap[section.section_name] = section
          })
          setGeneratedSections(sectionsMap)
          
          // Load processing status
          if (files.length > 0) {
            const status = await apiService.getProcessingStatus(existingPaper.paper_id)
            setProcessingStatus(status)
          }
          
          // Determine which step to start at
          if (sections.length > 0) {
            // Has sections, go to step 4 (Generate & Review)
            setCurrentStep(4)
          } else if (files.length > 0) {
            // Has files, go to step 3 (Select Sections)
            setCurrentStep(3)
          } else {
            // No files, go to step 2 (Upload References)
            setCurrentStep(2)
          }
          
        } catch (error) {
          console.error('Failed to load existing paper data:', error)
          // If loading fails, start from step 2
          setCurrentStep(2)
        }
      }
    }
    
    checkLatexStatus()
    loadExistingData()
  }, [existingPaper])

  const steps = [
    { id: 1, title: 'Paper Details', icon: FileText },
    { id: 2, title: 'Upload References', icon: Upload },
    { id: 3, title: 'Select Sections', icon: Brain },
    { id: 4, title: 'Generate & Review', icon: Eye }
  ]

  const handleInputChange = (field, value) => {
    setPaperData(prev => ({ ...prev, [field]: value }))
  }

  const handleArrayChange = (field, index, value) => {
    setPaperData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }))
  }

  const addArrayItem = (field) => {
    setPaperData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }))
  }

  const removeArrayItem = (field, index) => {
    setPaperData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }))
  }

  const handleFileUpload = async (event) => {
    const files = event.target.files
    const { validFiles, errors } = validateFiles(files)
    
    if (errors.length > 0) {
      setError(errors.join(', '))
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      if (!paperId) {
        // Create paper first
        const paper = await apiService.createPaper(paperData)
        setPaperId(paper.paper_id)
        
        // Upload files (now returns immediately)
        const uploadedFileData = await apiService.uploadFiles(paper.paper_id, validFiles)
        setUploadedFiles(prev => [...prev, ...uploadedFileData])
        
        // Start polling for processing status
        pollProcessingStatus(paper.paper_id)
      } else {
        const uploadedFileData = await apiService.uploadFiles(paperId, validFiles)
        setUploadedFiles(prev => [...prev, ...uploadedFileData])
        
        // Start polling for processing status
        pollProcessingStatus(paperId)
      }
    } catch (err) {
      setError(`Upload failed: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const pollProcessingStatus = async (paperIdToCheck) => {
    const checkStatus = async () => {
      try {
        const status = await apiService.getProcessingStatus(paperIdToCheck)
        setProcessingStatus(status)
        
        if (!status.processing_complete) {
          setTimeout(checkStatus, 2000) // Check every 2 seconds
        }
      } catch (error) {
        console.error('Error checking processing status:', error)
      }
    }
    
    checkStatus()
  }

  const generateSection = async (sectionName) => {
    if (!paperId) return

    setIsLoading(true)
    setError(null)

    try {
      const result = await apiService.generateContent({
        paper_id: paperId,
        section_name: sectionName
      })
      
      setGeneratedSections(prev => ({
        ...prev,
        [sectionName]: result
      }))
    } catch (err) {
      setError(`Generation failed: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const exportPaper = async (format) => {
    if (!paperId) return

    setIsLoading(true)
    try {
      if (format === 'text') {
        const result = await apiService.exportPaper(paperId)
        downloadTextFile(result.paper, `${paperData.title}.txt`)
      } else if (format === 'latex') {
        const result = await apiService.exportPaperLatex(paperId)
        downloadTextFile(result.latex, result.filename)
      } else if (format === 'pdf') {
        // Check if we have any sections
        if (Object.keys(generatedSections).length === 0) {
          setError('No sections generated yet. Please generate some content first.')
          return
        }
        
        try {
          console.log('Starting PDF export...')
          const blob = await apiService.exportPaperPdf(paperId)
          console.log('PDF blob received:', blob.size, 'bytes')
          downloadBlob(blob, `${paperData.title}.pdf`)
          console.log('PDF download initiated')
        } catch (pdfError) {
          console.error('PDF export error:', pdfError)
          if (pdfError.response?.status === 503) {
            setError('PDF generation requires LaTeX to be installed on the server. Please contact your administrator.')
          } else {
            setError(`PDF generation failed: ${pdfError.message}`)
          }
        }
      }
    } catch (err) {
      setError(`Export failed: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const downloadTextFile = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    downloadBlob(blob, filename)
  }

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  // Add resume generation function
  const resumeGeneration = async () => {
    if (!paperId) return

    setIsLoading(true)
    setError(null)

    try {
      const result = await apiService.resumeGeneration(paperId)
      
      if (result.status === 'resumed') {
        alert(`Paper generation resumed!\n\nContinuing from where it left off. This may take a few more minutes.`)
        pollGenerationProgress()
      } else {
        alert(result.message)
        setIsLoading(false)
      }
      
    } catch (err) {
      setError(`Resume generation failed: ${err.message}`)
      setIsLoading(false)
    }
  }

  const generateCompletePaper = async () => {
    if (!paperId) return

    setIsLoading(true)
    setError(null)

    try {
      // Start the background generation
      const result = await apiService.generateCompletePaper(paperId)
      
      if (result.status === 'started') {
        // Show initial message
        alert(`Paper generation started in background!\n\nThis will take 4-8 minutes. The page will update automatically as sections are generated.`)
        
        // Start polling for progress
        pollGenerationProgress()
      } else {
        // Handle immediate completion (shouldn't happen with new system)
        handleGenerationComplete(result)
      }
      
    } catch (err) {
      setError(`Complete paper generation failed: ${err.message}`)
      setIsLoading(false)
    }
  }

  const pollGenerationProgress = async () => {
    setGenerationProgress(prev => ({ ...prev, isGenerating: true }))
    
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiService.getProcessingStatus(paperId)
        
        // Update sections as they're generated
        const sections = await apiService.getSections(paperId)
        const sectionsMap = {}
        sections.forEach(section => {
          sectionsMap[section.section_name] = section
        })
        setGeneratedSections(sectionsMap)
        
        // Update progress state
        const progress = status.generation_status
        setGenerationProgress({
          isGenerating: true,
          currentSection: progress.current_section || '',
          progress: progress.progress_percentage || 0,
          sectionsCompleted: progress.sections_generated || 0,
          totalSections: 11
        })
        
        // Check if generation is complete
        if (status.overall_status === 'completed') {
          clearInterval(pollInterval)
          setIsLoading(false)
          setGenerationProgress(prev => ({ ...prev, isGenerating: false }))
          
          const finalStats = status.generation_status
          alert(`Complete paper generated successfully!\n\nSections: ${finalStats.sections_generated}\nTotal words: ${finalStats.total_words}\nEstimated pages: ${finalStats.estimated_pages}`)
          
        } else if (status.overall_status === 'error') {
          clearInterval(pollInterval)
          setIsLoading(false)
          setGenerationProgress(prev => ({ ...prev, isGenerating: false }))
          setError('Paper generation failed. Please try again.')
          
        } else if (status.generation_status.status.startsWith('generating')) {
          // Continue polling - progress is already updated above
          console.log(`Generating: ${progress.current_section} (${progress.progress_percentage}%)`)
        }
        
      } catch (err) {
        console.error('Error polling status:', err)
        // Continue polling even if one request fails
      }
    }, 3000) // Poll every 3 seconds

    // Stop polling after 15 minutes (safety timeout)
    setTimeout(() => {
      clearInterval(pollInterval)
      if (isLoading) {
        setIsLoading(false)
        setGenerationProgress(prev => ({ ...prev, isGenerating: false }))
        setError('Generation timeout. Please check the sections - some may have been generated.')
      }
    }, 15 * 60 * 1000)
  }

  const handleGenerationComplete = async (result) => {
    // Refresh sections to show all generated content
    const sections = await apiService.getSections(paperId)
    const sectionsMap = {}
    sections.forEach(section => {
      sectionsMap[section.section_name] = section
    })
    setGeneratedSections(sectionsMap)
    
    // Show success message with metrics
    setError(null)
    setIsLoading(false)
    alert(`Complete paper generated successfully!\n\nSections: ${result.sections_generated || 'undefined'}\nTotal words: ${result.total_words || 'undefined'}\nEstimated pages: ${result.estimated_pages || 'undefined'}`)
  }

  const generateAllSections = async () => {
    for (const section of selectedSections) {
      await generateSection(section)
    }
  }

  const nextStep = async () => {
    if (currentStep === 1) {
      // Validate paper details
      if (!paperData.title || !paperData.domain || !paperData.authors[0]) {
        setError('Please fill in all required fields')
        return
      }
      
      setIsLoading(true)
      try {
        if (!paperId) {
          // Create new paper
          const paper = await apiService.createPaper(paperData)
          setPaperId(paper.paper_id)
        }
        setCurrentStep(2)
      } catch (err) {
        setError(`Failed to create paper: ${err.message}`)
      } finally {
        setIsLoading(false)
      }
    } else if (currentStep === 2) {
      if (uploadedFiles.length === 0) {
        setError('Please upload at least one reference file')
        return
      }
      setCurrentStep(3)
    } else if (currentStep === 3) {
      if (selectedSections.length === 0) {
        setError('Please select at least one section to generate')
        return
      }
      setCurrentStep(4)
    }
    setError(null)
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
      setError(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="flex items-center text-white hover:text-purple-300 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </button>
            
            {existingPaper && (
              <div className="text-center">
                <h2 className="text-lg font-semibold text-white">Editing: {existingPaper.title}</h2>
                <p className="text-sm text-purple-300">Continue working on your paper</p>
              </div>
            )}
            
            <div className="flex items-center space-x-4">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                    currentStep >= step.id 
                      ? 'bg-purple-500 border-purple-500 text-white' 
                      : 'border-white/30 text-white/50'
                  }`}>
                    {currentStep > step.id ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-12 h-0.5 mx-2 ${
                      currentStep > step.id ? 'bg-purple-500' : 'bg-white/20'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Error Display */}
          {error && (
            <div className="bg-red-500/20 backdrop-blur-sm border border-red-300/30 rounded-xl p-4 mb-8 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-400 mr-3 flex-shrink-0" />
              <p className="text-red-300">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-400 hover:text-red-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Step Content */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8">
            {currentStep === 1 && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-white mb-2">Paper Details</h2>
                  <p className="text-gray-300">Tell us about your research paper</p>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <label className="block text-white font-medium mb-2">Paper Title *</label>
                    <input
                      type="text"
                      value={paperData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Enter your paper title..."
                    />
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Research Domain *</label>
                    <input
                      type="text"
                      value={paperData.domain}
                      onChange={(e) => handleInputChange('domain', e.target.value)}
                      className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="e.g., Machine Learning, IoT, Cybersecurity..."
                    />
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Authors *</label>
                    {paperData.authors.map((author, index) => (
                      <div key={index} className="flex items-center mb-2">
                        <input
                          type="text"
                          value={author}
                          onChange={(e) => handleArrayChange('authors', index, e.target.value)}
                          className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          placeholder="Author name..."
                        />
                        {paperData.authors.length > 1 && (
                          <button
                            onClick={() => removeArrayItem('authors', index)}
                            className="ml-2 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => addArrayItem('authors')}
                      className="flex items-center text-purple-400 hover:text-purple-300 text-sm"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Author
                    </button>
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Affiliations</label>
                    {paperData.affiliations.map((affiliation, index) => (
                      <div key={index} className="flex items-center mb-2">
                        <input
                          type="text"
                          value={affiliation}
                          onChange={(e) => handleArrayChange('affiliations', index, e.target.value)}
                          className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          placeholder="Institution/Organization..."
                        />
                        {paperData.affiliations.length > 1 && (
                          <button
                            onClick={() => removeArrayItem('affiliations', index)}
                            className="ml-2 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => addArrayItem('affiliations')}
                      className="flex items-center text-purple-400 hover:text-purple-300 text-sm"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Affiliation
                    </button>
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Keywords</label>
                    {paperData.keywords.map((keyword, index) => (
                      <div key={index} className="flex items-center mb-2">
                        <input
                          type="text"
                          value={keyword}
                          onChange={(e) => handleArrayChange('keywords', index, e.target.value)}
                          className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          placeholder="Research keyword..."
                        />
                        {paperData.keywords.length > 1 && (
                          <button
                            onClick={() => removeArrayItem('keywords', index)}
                            className="ml-2 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => addArrayItem('keywords')}
                      className="flex items-center text-purple-400 hover:text-purple-300 text-sm"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Keyword
                    </button>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-white mb-2">Upload References</h2>
                  <p className="text-gray-300">Upload research papers and references for AI analysis</p>
                </div>

                <div className="border-2 border-dashed border-white/20 rounded-2xl p-12 text-center hover:border-purple-400 transition-colors">
                  <Upload className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Drop files here or click to browse</h3>
                  <p className="text-gray-300 mb-6">Supports PDF and DOCX files up to 10MB each</p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                        Uploading...
                      </>
                    ) : (
                      'Select Files'
                    )}
                  </button>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-white">Uploaded Files</h3>
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="bg-white/10 rounded-xl p-4 flex items-center justify-between">
                        <div className="flex items-center">
                          <FileText className="w-8 h-8 text-purple-400 mr-3" />
                          <div>
                            <p className="text-white font-medium">{file.filename}</p>
                            <p className="text-gray-300 text-sm">{formatFileSize(file.file_size)}</p>
                          </div>
                        </div>
                        <CheckCircle className="w-6 h-6 text-green-400" />
                      </div>
                    ))}
                    
                    {processingStatus && (
                      <div className="bg-blue-500/20 backdrop-blur-sm border border-blue-300/30 rounded-xl p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-blue-300 font-medium">Processing Files</span>
                          <span className="text-blue-200 text-sm">
                            {processingStatus.processed_files}/{processingStatus.total_files} files
                          </span>
                        </div>
                        <div className="w-full bg-blue-900/30 rounded-full h-2">
                          <div 
                            className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${processingStatus.progress_percentage}%` }}
                          ></div>
                        </div>
                        <p className="text-blue-200 text-xs mt-2">
                          {processingStatus.processing_complete 
                            ? "✅ All files processed and ready for generation"
                            : "🔄 Processing files in background..."
                          }
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-white mb-2">Select Sections</h2>
                  <p className="text-gray-300">Choose which sections to generate for your paper</p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {IEEE_SECTIONS.map((section) => (
                    <div
                      key={section}
                      onClick={() => {
                        setSelectedSections(prev => 
                          prev.includes(section) 
                            ? prev.filter(s => s !== section)
                            : [...prev, section]
                        )
                      }}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedSections.includes(section)
                          ? 'bg-purple-500/20 border-purple-400 text-white'
                          : 'bg-white/5 border-white/20 text-gray-300 hover:border-purple-400/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{section}</span>
                        {selectedSections.includes(section) && (
                          <CheckCircle className="w-5 h-5 text-purple-400" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="text-center">
                  <p className="text-gray-300">
                    Selected {selectedSections.length} section{selectedSections.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-white mb-2">Generate & Review</h2>
                  <p className="text-gray-300">AI is generating your paper sections</p>
                </div>

                <div className="flex justify-center mb-8 space-x-4">
                  <button
                    onClick={generateAllSections}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Brain className="w-5 h-5 mr-2 inline" />
                        Generate Selected Sections
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={generateCompletePaper}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 disabled:opacity-50"
                  >
                    {isLoading ? (
                      generationProgress.isGenerating ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                          {generationProgress.currentSection ? 
                            `Generating ${generationProgress.currentSection} (${generationProgress.sectionsCompleted}/${generationProgress.totalSections})` :
                            'Starting generation...'
                          }
                        </>
                      ) : (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                          Generating Complete Paper...
                        </>
                      )
                    ) : (
                      <>
                        <FileText className="w-5 h-5 mr-2 inline" />
                        Generate Complete Paper (10+ pages)
                      </>
                    )}
                  </button>
                  
                  {/* Resume Generation Button */}
                  {Object.keys(generatedSections).length > 0 && Object.keys(generatedSections).length < 11 && (
                    <button
                      onClick={resumeGeneration}
                      disabled={isLoading}
                      className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 disabled:opacity-50"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                          Resuming...
                        </>
                      ) : (
                        <>
                          <FileText className="w-5 h-5 mr-2 inline" />
                          Resume Generation ({Object.keys(generatedSections).length}/11 done)
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Progress indicator for complete paper generation */}
                {generationProgress.isGenerating && (
                  <div className="bg-white/10 rounded-xl p-6 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">
                        {generationProgress.currentSection ? 
                          `Currently generating: ${generationProgress.currentSection}` :
                          'Preparing generation...'
                        }
                      </span>
                      <span className="text-white/70">
                        {generationProgress.sectionsCompleted}/{generationProgress.totalSections} sections
                      </span>
                    </div>
                    <div className="w-full bg-white/20 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-emerald-400 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${generationProgress.progress}%` }}
                      ></div>
                    </div>
                    <div className="text-center text-white/70 text-sm mt-2">
                      {generationProgress.progress}% complete
                    </div>
                  </div>
                )}

                <div className="space-y-6">
                  {selectedSections.map((section) => (
                    <div key={section} className="bg-white/10 rounded-xl p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-semibold text-white">{section}</h3>
                        <div className="flex items-center space-x-2">
                          {generatedSections[section] ? (
                            <CheckCircle className="w-6 h-6 text-green-400" />
                          ) : (
                            <button
                              onClick={() => generateSection(section)}
                              disabled={isLoading}
                              className="text-purple-400 hover:text-purple-300"
                            >
                              <Brain className="w-6 h-6" />
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {generatedSections[section] ? (
                        <div className="bg-white/5 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <CheckCircle className="w-5 h-5 text-green-400" />
                              <span className="text-green-400 font-medium">Generated successfully</span>
                            </div>
                            <div className="text-gray-400 text-sm">
                              {generatedSections[section].metadata?.word_count || 'N/A'} words
                            </div>
                          </div>
                          <p className="text-gray-400 text-sm mt-2">
                            Content available in export. Click export buttons above to download the full paper.
                          </p>
                        </div>
                      ) : (
                        <div className="bg-white/5 rounded-lg p-4 text-center">
                          <p className="text-gray-400">Click the brain icon to generate this section</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-12">
              <button
                onClick={prevStep}
                disabled={currentStep === 1}
                className="flex items-center text-white hover:text-purple-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Previous
              </button>

              {currentStep < 4 ? (
                <button
                  onClick={nextStep}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                      Processing...
                    </>
                  ) : (
                    'Next Step'
                  )}
                </button>
              ) : (
                <div className="flex space-x-4">
                  <button
                    onClick={() => exportPaper('text')}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50"
                  >
                    <FileDown className="w-5 h-5 mr-2 inline" />
                    Export Text
                  </button>
                  
                  <button
                    onClick={() => exportPaper('latex')}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50"
                  >
                    <FileDown className="w-5 h-5 mr-2 inline" />
                    Export LaTeX
                  </button>
                  
                  {latexAvailable ? (
                    <button
                      onClick={() => exportPaper('pdf')}
                      disabled={isLoading || Object.keys(generatedSections).length === 0}
                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50"
                    >
                      <Download className="w-5 h-5 mr-2 inline" />
                      Export PDF
                    </button>
                  ) : (
                    <div className="bg-gray-600 text-gray-300 font-semibold px-6 py-3 rounded-xl cursor-not-allowed" title="LaTeX is required for PDF generation. Please install TeX Live or MiKTeX on the server.">
                      <Download className="w-5 h-5 mr-2 inline" />
                      PDF (LaTeX not available)
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaperWizard