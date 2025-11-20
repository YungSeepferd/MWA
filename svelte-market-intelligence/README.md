# MWA Market Intelligence Dashboard

A mobile-compatible Svelte/SvelteKit application for managing market intelligence contacts, deployed on GitHub Pages.

## Features

- 📱 **Mobile-First Design**: Optimized for touch interactions and mobile devices
- 🚀 **Real-time Updates**: WebSocket integration for live data synchronization
- 📊 **Market Intelligence**: Advanced contact scoring and analytics
- 🔍 **Search & Filter**: Powerful contact management with filtering capabilities
- 📈 **Analytics Dashboard**: Visual insights into market trends
- 📲 **PWA Support**: Installable as a mobile app with offline capabilities
- 🌐 **GitHub Pages**: Static site deployment with automatic CI/CD

## Tech Stack

- **Frontend**: SvelteKit with TypeScript
- **Styling**: Mobile-first CSS with custom design system
- **State Management**: Svelte stores and reactive programming
- **API Integration**: RESTful API client with WebSocket support
- **Build Tool**: Vite with optimized bundling
- **Deployment**: GitHub Pages with GitHub Actions

## Prerequisites

- Node.js 18+
- npm or yarn
- Git

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd svelte-market-intelligence
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:5173`

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - TypeScript type checking
- `npm run lint` - ESLint code linting
- `npm run test` - Run unit tests

### Project Structure

```
src/
├── components/          # Reusable components
│   ├── layout/         # Layout components
│   └── ui/             # UI components
├── lib/
│   ├── services/       # API and WebSocket services
│   ├── types/          # TypeScript definitions
│   └── utils/          # Utility functions
├── routes/             # SvelteKit pages
└── app.css            # Global styles
```

### API Integration

The app connects to a FastAPI backend. Configure the API URL in `src/lib/services/api.ts`:

```typescript
const apiClient = new ApiClient('http://localhost:8000/api');
```

### Mobile Optimization

- Touch-friendly buttons (minimum 44px)
- Swipe gestures for navigation
- Responsive grid system
- Mobile-optimized typography
- PWA manifest for mobile installation

## Deployment

### GitHub Pages

The app is configured for automatic deployment to GitHub Pages:

1. **Enable GitHub Pages** in repository settings
2. **Set source** to "GitHub Actions"
3. **Push to main branch** to trigger deployment

### Manual Deployment

```bash
npm run build
# Upload 'build' folder to your hosting service
```

### Environment Variables

Create a `.env` file for local development:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

## API Endpoints

The app expects the following API endpoints:

### Contacts
- `GET /api/contacts` - List contacts
- `GET /api/contacts/:id` - Get contact details
- `POST /api/contacts` - Create contact
- `PUT /api/contacts/:id` - Update contact
- `DELETE /api/contacts/:id` - Delete contact
- `POST /api/contacts/:id/approve` - Approve contact
- `POST /api/contacts/:id/reject` - Reject contact

### Analytics
- `GET /api/analytics` - Get analytics data

### WebSocket
- `/ws` - Real-time updates

## Mobile Features

### Touch Interactions
- Swipe gestures for navigation
- Touch-optimized button sizes
- Mobile-friendly form inputs

### PWA Capabilities
- Offline functionality
- Mobile installation
- Push notifications
- Background sync

### Performance Optimizations
- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation
- Review the architecture document

## Roadmap

- [ ] Contact import/export functionality
- [ ] Advanced filtering and search
- [ ] Real-time collaboration
- [ ] Advanced analytics charts
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Advanced PWA features