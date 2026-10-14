import { Outlet } from "react-router"
import { Sidebar } from "./Sidebar"

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center border-b px-6">
          <div>
            <p className="text-sm font-semibold">
              Scientific Document RAG Assistant
            </p>
            <p className="text-xs text-muted-foreground">
              Research documents and evidence-backed answers
            </p>
          </div>
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}