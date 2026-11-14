import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './fonts'
import './styles/tokens.css'
import './styles/app.css'
import App from './App'

// The Chinese page. The reveal's hidden starting state applies only once the script is running.
document.documentElement.classList.add('js')

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App lang="zh" />
  </StrictMode>,
)
