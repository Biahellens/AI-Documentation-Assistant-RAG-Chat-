import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function SidebarDocuments({ docs, activeDoc, setActiveDoc }: any) {
  return (
    <div className="space-y-2">
      {docs.map((doc: any) => (
        <Card
          key={doc.doc_id}
          className={`p-3 cursor-pointer ${
            activeDoc === doc.doc_id ? "border-primary" : ""
          }`}
          onClick={() => setActiveDoc(doc.doc_id)}
        >
          <div className="flex justify-between items-center">
            <span className="text-sm">{doc.filename}</span>
            <Badge variant="secondary">PDF</Badge>
          </div>
        </Card>
      ))}
    </div>
  )
}