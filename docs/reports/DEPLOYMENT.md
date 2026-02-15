# Deployment Guide

Guia passo-a-passo para fazer deploy do B2B Dashboard em produção.

## 📋 Pré-requisitos

- [x] Python 3.9+
- [x] Git
- [x] Account em servidor (AWS, Azure, Heroku, etc)
- [x] All tests passing locally (`make test`)
- [x] All checks passing (`make dev`)

## 🚀 Deployment Options

### Opção 1: Heroku (Recomendado para iniciar)

#### 1. Setup Heroku
```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Criar app
heroku create seu-app-name
```

#### 2. Configurar requirements
```bash
pip freeze > requirements.txt
```

#### 3. Criar Procfile
```bash
cat > Procfile << EOF
web: cd dashboards && streamlit run app.py --logger.level=info
EOF
```

#### 4. Deploy
```bash
git push heroku main
```

#### 5. Monitor
```bash
heroku logs --tail
heroku open
```

### Opção 2: AWS (Escalável)

#### 1. Preparar EC2 Instance
```bash
# SSH na instância
ssh -i key.pem ubuntu@your-instance.amazonaws.com

# Instalar Python e dependências
sudo apt-get update
sudo apt-get install python3.9 python3-pip
sudo apt-get install nginx

# Clonar repo
git clone seu-repo
cd B2B_Dashboard
```

#### 2. Setup Python Environment
```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install gunicorn
```

#### 3. Configurar Nginx
```bash
# Criar config
sudo nano /etc/nginx/sites-available/dashboard

# Conteúdo mínimo:
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Ativar
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Rodar App
```bash
# Usando screen para background execution
screen -S streamlit
cd dashboards && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
# Detach: Ctrl+A, Ctrl+D
```

#### 5. Configurar SSL (HTTPS)
```bash
# Usar Certbot para Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

### Opção 3: Docker

#### 1. Criar Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboards/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 2. Build e Run
```bash
# Build
docker build -t b2b-dashboard .

# Run locally
docker run -p 8501:8501 b2b-dashboard

# Push to registry
docker tag b2b-dashboard seu-repo/b2b-dashboard:latest
docker push seu-repo/b2b-dashboard:latest
```

#### 3. Deploy com Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: seu-repo/b2b-dashboard:latest
    ports:
      - "8501:8501"
    environment:
      - DATA_PATH=/data
    volumes:
      - ./data:/data
    restart: always

  # Opcional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

## 🔧 Environment Configuration

### Production .env
```bash
# Data paths
DATA_PATH=/var/data/b2b-dashboard

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/b2b-dashboard/app.log

# Streamlit specific
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Secrets Management
```bash
# Usar AWS Secrets Manager ou similar
export SECRETS_MANAGER=aws

# Ou arquivo .env (NÃO commit!)
# .env (git ignored)
DATABASE_URL=postgres://user:pass@host/db
API_KEY=seu_key_aqui
```

## 📊 Monitoring & Logging

### Logs
```bash
# Local
tail -f logs/app.log

# Production
docker logs -f b2b-dashboard

# AWS CloudWatch
aws logs tail /aws/ec2/b2b-dashboard --follow
```

### Health Check
```bash
# Adicionar endpoint simples
# ou monitorar com:
curl http://localhost:8501/health
```

### Alerting
- [ ] Setup CloudWatch alarms
- [ ] Configure email/Slack notifications
- [ ] Monitor memory/CPU usage
- [ ] Track data freshness

## 🔐 Security Checklist

- [ ] All secrets in environment variables (never in code)
- [ ] HTTPS enabled (SSL certificate)
- [ ] Rate limiting configured
- [ ] Input validation on all user inputs
- [ ] Firewall rules configured
- [ ] Regular security updates
- [ ] Database credentials rotated
- [ ] Logs not exposing sensitive data

## 📈 Performance Optimization

### Caching Strategy
```python
# Already implemented in app.py
@st.cache_resource
def load_data():
    return expensive_operation()
```

### Database Optimization
- [ ] Add indexes to frequently queried columns
- [ ] Implement query result caching
- [ ] Use parquet format for large datasets
- [ ] Consider data warehouse (Redshift, BigQuery)

### CDN & Static Files
- [ ] Serve assets via CDN
- [ ] Compress images
- [ ] Minify JS/CSS

## 🔄 CI/CD Integration

### Automatic Deployment
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.event.push.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Run tests
        run: make test
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: seu-app-name
          heroku_email: seu-email@example.com
```

## 🧪 Pre-deployment Checklist

```bash
# Local checks
[ ] make dev                    # All tests and checks
[ ] make test-cov             # Coverage acceptable
[ ] Review CHANGELOG.md       # Document changes
[ ] Test with sample data     # Functional test
[ ] Update version numbers    # semantic versioning
[ ] Create git tag            # v1.2.3

# Staging environment
[ ] Deploy to staging         # Test in prod-like env
[ ] Run smoke tests           # Basic functionality
[ ] Check data loading        # All data sources
[ ] Verify performance        # Load testing
[ ] Monitor for errors        # 1 hour observation

# Production deployment
[ ] Final review              # Code review
[ ] Backup current version    # Rollback plan
[ ] Deploy to production      # Go!
[ ] Monitor closely           # First 24 hours
[ ] Update status page        # User communication
```

## 🚨 Rollback Procedure

```bash
# Se algo der errado:

# 1. Revert code
git revert <commit-hash>
git push

# 2. Docker rollback
docker run -p 8501:8501 seu-repo/b2b-dashboard:previous

# 3. Database rollback
pg_restore -d db_name db-backup.sql

# 4. Check logs for errors
tail -f logs/error.log

# 5. Notify team
# Send update to #deployments channel
```

## 📝 Maintenance Tasks

### Daily
- [ ] Monitor error logs
- [ ] Check data freshness
- [ ] Verify uptime

### Weekly
- [ ] Review performance metrics
- [ ] Update dependencies (security patches)
- [ ] Backup data

### Monthly
- [ ] Full security audit
- [ ] Update documentation
- [ ] Review and optimize queries
- [ ] Capacity planning

### Quarterly
- [ ] Major version updates
- [ ] Architecture review
- [ ] Performance benchmarking
- [ ] Disaster recovery drill

## 📞 Troubleshooting

### App não inicia
```bash
# Check logs
docker logs app-container

# Verificar Python version
python --version

# Instalar dependências
pip install -e .

# Testar imports
python -c "from src.config import settings"
```

### Data not loading
```bash
# Verificar path
ls -la $DATA_PATH

# Testar data loading
python -c "from src.utils.data_loading import load_parquet_safe; load_parquet_safe('path')"

# Verificar permissions
chmod 755 $DATA_PATH
```

### Performance issues
```bash
# Profile memory
python -m memory_profiler dashboards/app.py

# Profile speed
python -m cProfile -s cumulative dashboards/app.py

# Monitor resources
htop  # Linux/Mac
tasklist  # Windows
```

## 🔗 Resources

- [Streamlit Deployment Guide](https://docs.streamlit.io/library/get-started/installation)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)

---

**Last Updated:** 2024-01
**Status:** Production Ready
