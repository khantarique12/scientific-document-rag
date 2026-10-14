import { BrowserRouter, Route, Routes } from "react-router"

import { AppLayout } from "@/components/layout/AppLayout"
import { DashboardPage } from "@/pages/DashboardPage"
import { DocumentsPage } from "@/pages/DocumentsPage"
import { DocumentDetailPage } from "@/pages/DocumentDetailPage"
import { AssistantPage } from "@/pages/AssistantPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route
            path="documents/:id"
            element={<DocumentDetailPage />}
          />
          <Route path="assistant" element={<AssistantPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App