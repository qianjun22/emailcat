# EmailCat

A smart email categorization and management system powered by AI.

## Description

EmailCat is an intelligent email management system that helps users automatically categorize, prioritize, and organize their emails using advanced AI technology. It provides daily inbox summaries and smart email management for both Gmail and Outlook users.

## Project Structure

```
emailcat/
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend application
├── .github/          # GitHub Actions workflows
└── docs/             # Project documentation
```

## Features

- AI-powered email categorization
- Smart email prioritization
- Automated email organization
- Natural language processing for email content analysis
- Customizable categorization rules
- Daily inbox summaries
- Gmail and Outlook integration
- Secure OAuth2 authentication

## Tech Stack

### Frontend
- Next.js (TypeScript)
- Tailwind CSS
- Shadcn UI
- Auth0 for authentication

### Backend
- Python FastAPI
- OpenAI GPT-4
- Gmail API
- Microsoft Graph API
- Auth0 for authentication

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Auth0 account
- Google Cloud Console account
- Microsoft Azure account
- OpenAI API key

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/qianjun22/emailcat.git
cd emailcat
```

2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

3. Backend Setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

4. Environment Variables:
Create `.env` files in both frontend and backend directories with the following variables:

Frontend (.env):
```
AUTH0_SECRET='your-auth0-secret'
AUTH0_BASE_URL='http://localhost:3000'
AUTH0_ISSUER_BASE_URL='your-auth0-domain'
AUTH0_CLIENT_ID='your-auth0-client-id'
AUTH0_CLIENT_SECRET='your-auth0-client-secret'
```

Backend (.env):
```
OPENAI_API_KEY='your-openai-api-key'
AUTH0_DOMAIN='your-auth0-domain'
AUTH0_AUDIENCE='your-auth0-audience'
GOOGLE_CLIENT_ID='your-google-client-id'
GOOGLE_CLIENT_SECRET='your-google-client-secret'
MICROSOFT_CLIENT_ID='your-microsoft-client-id'
MICROSOFT_CLIENT_SECRET='your-microsoft-client-secret'
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License 