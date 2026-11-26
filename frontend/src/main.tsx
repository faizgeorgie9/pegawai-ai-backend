import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/dm-sans/400.css'
import '@fontsource/dm-sans/500.css'
import '@fontsource/dm-sans/600.css'
import '@fontsource/dm-sans/700.css'
import './styles.css'
import './chat.css'
import './pages.css'
import './workspace.css'
import App from './App'

// A tab left open across a deploy asks for a chunk name that no longer exists. Reload once per tab so
// it picks up the new build; a second failure falls through to the page boundary instead of looping.
window.addEventListener('vite:preloadError', (e) => {
  e.preventDefault()
  try {
    if (sessionStorage.getItem('pa.reloaded')) return
    sessionStorage.setItem('pa.reloaded', '1')
  } catch {
    return // no sessionStorage: the page boundary still explains the failure
  }
  location.reload()
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
