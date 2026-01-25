# Security Guidelines for IEEE Paper Generator

## 🔐 Environment Security

### ❌ What GitGuardian Detected
GitGuardian flagged our repository because `.env.docker` contained a hardcoded password:
```bash
DB_PASSWORD=postgres123  # ❌ NEVER do this!
```

### ✅ Security Fixes Applied

1. **Removed Hardcoded Passwords**
   - Changed default password to `CHANGE_ME_SECURE_PASSWORD`
   - Added clear warnings in comments
   - Created secure password generation scripts

2. **Secure Environment Generation**
   - `scripts/generate-secure-env.sh` (Linux/Mac)
   - `scripts/generate-secure-env.ps1` (Windows)
   - Generates cryptographically secure random passwords

3. **Updated Documentation**
   - Clear security warnings
   - Step-by-step secure setup instructions
   - Best practices documentation

## 🛡️ Security Best Practices

### Environment Variables
```bash
# ✅ Good - Use secure random passwords
DB_PASSWORD=x7K9mN2pQ8vR5wE3tY6uI1oP4sA7dF0g

# ❌ Bad - Predictable passwords
DB_PASSWORD=password123
DB_PASSWORD=postgres
```

### File Security
```bash
# ✅ Always in .gitignore
.env
.env.local
.env.production

# ✅ Proper file permissions
chmod 600 .env  # Owner read/write only
```

### API Keys
```bash
# ✅ Use environment variables
GEMINI_API_KEY=your_actual_api_key_here

# ❌ Never hardcode in source code
api_key = "AIzaSyC-hardcoded-key-bad"  # DON'T DO THIS
```

## 🔧 Secure Setup Instructions

### Option 1: Automatic Secure Setup (Recommended)
```bash
# Generates secure random passwords automatically
make setup-secure

# Or run directly:
./scripts/generate-secure-env.sh        # Linux/Mac
./scripts/generate-secure-env.ps1       # Windows
```

### Option 2: Manual Setup
```bash
# Copy template
cp .env.docker .env

# Edit .env and change ALL default values:
# 1. Generate secure password: openssl rand -base64 32
# 2. Add your real API keys
# 3. Never use default passwords
```

## 🚨 Security Checklist

### Before Committing Code
- [ ] No hardcoded passwords in any files
- [ ] No API keys in source code
- [ ] `.env` files are in `.gitignore`
- [ ] All secrets use environment variables
- [ ] Default passwords are changed

### Production Deployment
- [ ] Use strong, unique passwords (25+ characters)
- [ ] Enable database SSL/TLS
- [ ] Use secrets management (Docker secrets, K8s secrets)
- [ ] Regular security updates
- [ ] Monitor for exposed credentials

### Docker Security
- [ ] No secrets in Dockerfiles
- [ ] Use multi-stage builds
- [ ] Run containers as non-root user
- [ ] Limit container resources
- [ ] Use official base images

## 🔍 Security Scanning

### GitGuardian Integration
GitGuardian automatically scans commits for:
- API keys and tokens
- Database passwords
- Private keys
- Cloud credentials

### Local Security Scanning
```bash
# Install git-secrets
git secrets --install
git secrets --register-aws

# Scan repository
git secrets --scan
```

### Docker Security Scanning
```bash
# Scan Docker images
docker scout cves ieee-paper-backend
docker scout cves ieee-paper-frontend
```

## 🚨 Incident Response

### If Credentials Are Exposed
1. **Immediately rotate all exposed credentials**
2. **Check access logs for unauthorized usage**
3. **Update all systems using the compromised credentials**
4. **Review and improve security practices**

### Emergency Contacts
- Security Team: security@yourcompany.com
- DevOps Team: devops@yourcompany.com

## 📚 Security Resources

### Password Generation
```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
[System.Web.Security.Membership]::GeneratePassword(32, 8)

# Online (use with caution)
# https://passwordsgenerator.net/
```

### Environment Management Tools
- **direnv**: Automatic environment loading
- **sops**: Encrypted secrets management
- **Vault**: Enterprise secrets management
- **AWS Secrets Manager**: Cloud secrets management

### Security Scanning Tools
- **GitGuardian**: Automated secret detection
- **TruffleHog**: Git history secret scanning
- **git-secrets**: Pre-commit secret prevention
- **Snyk**: Dependency vulnerability scanning

## 🔐 Encryption Standards

### Passwords
- Minimum 16 characters
- Use cryptographically secure random generation
- Include uppercase, lowercase, numbers, symbols
- Unique for each service

### API Keys
- Store in environment variables only
- Use key rotation when possible
- Monitor usage and access patterns
- Implement rate limiting

### Database
- Enable SSL/TLS connections
- Use connection encryption
- Regular security updates
- Access logging enabled

## 📋 Security Audit Checklist

### Monthly Reviews
- [ ] Rotate database passwords
- [ ] Review API key usage
- [ ] Check for exposed credentials
- [ ] Update dependencies
- [ ] Review access logs

### Quarterly Reviews
- [ ] Security penetration testing
- [ ] Dependency vulnerability assessment
- [ ] Infrastructure security review
- [ ] Incident response plan testing
- [ ] Security training updates

Remember: **Security is everyone's responsibility!** 🛡️