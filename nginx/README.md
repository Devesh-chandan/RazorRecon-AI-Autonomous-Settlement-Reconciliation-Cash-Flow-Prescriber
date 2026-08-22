# Self-Signed SSL Certificate for Local Testing
## ⚠️ Development Only — Replace with Let's Encrypt for Production

### Generate Self-Signed Certificate (Windows PowerShell)

Run the following command once before using `docker-compose.prod.yml`:

```powershell
# Create the ssl directory
New-Item -ItemType Directory -Force -Path ".\nginx\ssl"

# Generate self-signed cert valid for 365 days
# Requires OpenSSL — install via: winget install ShiningLight.OpenSSL.Light
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes `
  -keyout .\nginx\ssl\selfsigned.key `
  -out .\nginx\ssl\selfsigned.crt `
  -subj "/CN=localhost/O=RazorRecon/C=IN"
```

### Alternative: Generate via WSL / Git Bash

```bash
mkdir -p nginx/ssl
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout nginx/ssl/selfsigned.key \
  -out nginx/ssl/selfsigned.crt \
  -subj "/CN=localhost/O=RazorRecon/C=IN"
```

### Production: Let's Encrypt via Certbot

When deploying to a real domain:

```bash
# On your server (Ubuntu/Debian)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Then update nginx/nginx.conf:
#   ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Mount these into the nginx container in docker-compose.prod.yml:
#   - /etc/letsencrypt:/etc/letsencrypt:ro
```

### Expected Files After Generation
```
nginx/
├── nginx.conf         ✅ Already created
└── ssl/
    ├── selfsigned.crt  ← generate this
    └── selfsigned.key  ← generate this
```
