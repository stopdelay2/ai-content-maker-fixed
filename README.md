# 🤖 AI Content Articles Maker

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com)

An automated, AI-powered content creation microservice that generates SEO-optimized articles and publishes them to WordPress blogs. The system integrates with multiple AI services and content management platforms to create high-quality, optimized content at scale.

## 🚀 Features

### Content Generation
- **Automated Article Creation**: Generate full articles from keywords using AI
- **SEO Optimization**: Neuron Writer integration for SEO scoring and optimization  
- **Multi-language Support**: Create content in multiple languages
- **Smart Headlines**: AI-powered H1/H2 optimization with anchor text integration

### AI Image Generation
- **Featured Images**: Automatic main image creation with OpenAI/Midjourney
- **In-Article Images**: Generate and embed contextual images within articles
- **WordPress Integration**: Direct upload and embedding of images

### Publishing & Automation
- **WordPress Publishing**: Direct publishing to WordPress with featured images
- **Scheduled Processing**: APScheduler for automated daily content creation
- **Google Sheets Queue**: Process keywords from Google Sheets automatically
- **Batch Processing**: Handle multiple articles with rate limiting

## 📋 API Endpoints

### POST `/seo/create-article`
Create an SEO-optimized article from a keyword

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
- `project_id` - Neuron Writer project ID
- `keyword` - Target keyword for article generation
- `engine` - Search engine optimization target
- `language` - Content language
- `wordpress_site` - Target site for anchor optimization

### POST `/seo/create-article/publish-to-wordpress-blog`
Create article and publish directly to WordPress

## 🐳 Quick Start with Docker

```bash
# Clone and setup
git clone https://github.com/stopdelay2/ai-content-articles-maker.git
cd ai-content-articles-maker
cp .env.example .env

# Edit .env with your API keys

# Run with Docker
docker build -t ai-content-maker .
docker run -d -p 5002:5002 --env-file .env ai-content-maker
```

## ⚙️ Environment Variables

See `.env.example` for all required configuration variables.

---
**Built with ❤️ using Flask, OpenAI, and modern AI technologies**
