# EAAS - Escrow as a Service

A decentralized escrow platform with AI-powered dispute resolution, built with FastAPI and React.

## Features

### Core Functionality
- **User Registration & Authentication**: Secure user registration with cryptographic key generation
- **Wallet System**: Built-in wallet with balance tracking and transaction history
- **Room Creation**: Sellers can create escrow rooms with custom amounts
- **Real-time Communication**: WebSocket-based chat and status updates
- **Smart Contracts**: Cryptographically secure 2-of-3 multi-signature contracts
- **AI Dispute Resolution**: Automated evidence analysis and decision making

### Transaction Flow
1. **Seller creates room** with transaction amount
2. **Buyer joins room** using 4-word phrase
3. **Description negotiation** between parties
4. **Fund locking** by buyer into escrow
5. **Product delivery** confirmation by seller
6. **Release or dispute** by buyer
7. **AI arbitration** if dispute occurs

### AI Arbitration System
- **Transaction Classification**: Automatically categorizes transaction types
- **Evidence Requirements**: Dynamic evidence requirements based on transaction type
- **Multi-modal Analysis**: Supports text, images, and file uploads
- **Confidence Scoring**: Transparent confidence levels for decisions
- **Final Verdict**: Binding decisions with detailed reasoning

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Database (easily switchable to PostgreSQL)
- **WebSockets**: Real-time communication
- **Redis**: Connection management (optional)
- **OpenAI GPT-4**: AI arbitration
- **Cryptography**: RSA digital signatures

### Frontend
- **React 19**: Modern React with hooks
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **Zustand**: State management
- **Axios**: HTTP client
- **jsrsasign**: Cryptographic operations

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis (optional, for production)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd EAAS
```

2. **Create virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

5. **Initialize database**
```bash
python setup_db.py
```

6. **Run the server**
```bash
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend/eaas-frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Documentation

### Authentication
- `POST /api/register` - Register new user
- `GET /api/wallet/{user_id}` - Get wallet information

### Rooms
- `POST /api/rooms/create/{user_id}` - Create new escrow room
- `GET /api/rooms` - List available rooms
- `GET /api/rooms/{room_phrase}` - Get room details

### Evidence
- `POST /api/rooms/{room_phrase}/{user_id}/upload_evidence` - Upload evidence

### WebSocket
- `WS /api/ws/{room_phrase}/{user_id}` - Real-time room communication

## Usage

### For Sellers
1. Register with role "SELLER"
2. Create a new escrow room with desired amount
3. Wait for buyer to join
4. Negotiate transaction description
5. Confirm readiness to proceed
6. Deliver product/service when funds are locked
7. Respond to disputes if they arise

### For Buyers
1. Register with role "BUYER"
2. Browse available rooms or join with room phrase
3. Propose transaction description
4. Lock funds when ready
5. Confirm delivery or initiate dispute
6. Review AI arbitration results

## Security Features

### Cryptographic Security
- **RSA 2048-bit keys**: Strong encryption for all signatures
- **Digital Signatures**: All contract actions require valid signatures
- **Multi-signature Contracts**: 2-of-3 signature requirement for fund release
- **No Private Key Storage**: Private keys never leave the client

### Smart Contract Logic
- **Timeout Protection**: Automatic resolution after 24 hours
- **Dispute Resolution**: AI-powered arbitration system
- **Evidence Verification**: Multi-modal evidence analysis
- **Transparent Decisions**: All AI decisions include reasoning

## Development

### Project Structure
```
EAAS/
├── backend/
│   ├── database/          # Database models and connection
│   ├── routes/            # API endpoints
│   │   ├── utils/         # Utility functions and smart contracts
│   │   └── websockets/    # WebSocket handlers
│   ├── utils/             # Logging and utilities
│   └── main.py           # FastAPI application
├── frontend/
│   └── eaas-frontend/     # React application
│       ├── src/
│       │   ├── components/    # React components
│       │   ├── pages/         # Page components
│       │   ├── api/           # API client
│       │   ├── store/         # State management
│       │   └── lib/           # Utilities
│       └── package.json
└── README.md
```

### Key Components

#### Backend
- **Smart Contract System**: Handles cryptographic signatures and fund release
- **AI Arbiter**: Processes evidence and makes binding decisions
- **WebSocket Manager**: Manages real-time connections
- **Database Models**: User, Room, Wallet, Transaction entities

#### Frontend
- **Wallet Display**: Shows balance and transaction history
- **Room Interface**: Real-time transaction management
- **Evidence Uploader**: Multi-file upload with progress tracking
- **Status Tracker**: Visual transaction state management
- **AI Verdict Display**: Shows arbitration results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

## Roadmap

- [ ] Multi-currency support
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Integration with external payment systems
- [ ] Enhanced AI models
- [ ] Multi-language support
