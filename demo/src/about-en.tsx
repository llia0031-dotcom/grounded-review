import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './fonts-en'
import './styles/tokens.css'
import './styles/app.css'
import AboutPage from './AboutPage'

// The English about page.
document.documentElement.classList.add('js')
createRoot(document.getElementById('root')!).render(<StrictMode><AboutPage lang="en" /></StrictMode>)
