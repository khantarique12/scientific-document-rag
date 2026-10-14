import { NavLink } from "react-router"
import {
  BookOpenText,
  LayoutDashboard,
  Files,
  MessageSquareText,
} from "lucide-react"

const navigation = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
    end: true,
  },
  {
    label: "Documents",
    path: "/documents",
    icon: Files,
    end: false,
  },
  {
    label: "AI Assistant",
    path: "/assistant",
    icon: MessageSquareText,
    end: false,
  },
]

export function Sidebar() {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r bg-card">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <BookOpenText className="size-5" />
        </div>

        <div>
          <p className="text-sm font-semibold">Scientific RAG</p>
          <p className="text-xs text-muted-foreground">
            Research workspace
          </p>
        </div>
      </div>

      <nav aria-label="Main navigation" className="flex flex-1 flex-col gap-1 p-3">
        {navigation.map(({ label, path, icon: Icon, end }) => (
          <NavLink
            key={path}
            to={path}
            end={end}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-accent font-medium text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
              ].join(" ")
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">
          Scientific Document Intelligence
        </p>
      </div>
    </aside>
  )
}