import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "wsb-theme";
// Product decision: the app opens in dark mode (deep navy/slate glass — see
// CLAUDE.md and the design brief); light is available via the sidebar toggle.
// A saved preference wins over the default.
const DEFAULT_THEME: Theme = "dark";

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return DEFAULT_THEME;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "dark" || stored === "light" ? stored : DEFAULT_THEME;
}

/** Reflect the theme onto <html> so Tailwind's `dark:` variants and the
 *  `.dark` CSS-variable block in index.css take effect. */
function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
}

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    applyTheme(theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const value: ThemeContextValue = {
    theme,
    setTheme: setThemeState,
    toggleTheme: () => setThemeState((t) => (t === "dark" ? "light" : "dark")),
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Tests that render a component in isolation without the provider still
    // get a usable no-op rather than a crash.
    return {
      theme: DEFAULT_THEME,
      setTheme: () => {},
      toggleTheme: () => {},
    };
  }
  return ctx;
}
