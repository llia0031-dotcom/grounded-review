import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './fonts'
import './styles/tokens.css'
import './styles/app.css'
import AboutPage from './AboutPage'

// The Chinese about page.
document.documentElement.classList.add('js')
createRoot(document.getElementById('root')!).render(<StrictMode><AboutPage lang="zh" /></StrictMode>)
