import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import { store } from '@/store'

export function exportToPDF(title, columns, rows) {
  const doc = new jsPDF('landscape')
  
  // Usar as configurações do sistema se disponíveis
  const logoBase64 = store.appConfig?.logo_url || '' 
  const nomeOrgao = store.appConfig?.nome_orgao || 'NOME DO ÓRGÃO' 
  
  autoTable(doc, {
    startY: 45,
    margin: { top: 45 },
    head: [columns],
    body: rows,
    theme: 'striped',
    headStyles: { fillColor: [24, 103, 192] },
    styles: { fontSize: 9 },
    didDrawPage: function (data) {
      const pageWidth = doc.internal.pageSize.width
      const margin = data.settings.margin.left
      const marginRight = data.settings.margin.right

      // Logo à esquerda
      if (logoBase64) {
        try {
          // jsPDF consegue detectar automaticamente o formato a partir do data URI 
          // se não passarmos o parâmetro de format explicitamente.
          doc.addImage(logoBase64, margin, 10, 20, 20)
        } catch (e) {
          console.error("Erro ao desenhar logo no PDF:", e)
        }
      } else {
        doc.setFontSize(10)
        doc.setTextColor(150)
        doc.setFont('helvetica', 'normal')
        doc.text('[Brasão/Logo]', margin, 20)
      }

      // Nome do órgão à direita
      doc.setFontSize(12)
      doc.setTextColor(50)
      doc.setFont('helvetica', 'bold')
      const textWidth = doc.getTextWidth(nomeOrgao)
      doc.text(nomeOrgao, pageWidth - marginRight - textWidth, 20)

      // Título do Relatório
      doc.setFontSize(16)
      doc.setTextColor(20)
      doc.setFont('helvetica', 'bold')
      doc.text(title, margin, 32)
      
      // Data e hora
      doc.setFontSize(9)
      doc.setTextColor(100)
      doc.setFont('helvetica', 'normal')
      doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, margin, 38)
      
      // Numeração de página no rodapé
      const pageStr = `Página ${doc.internal.getNumberOfPages()}`
      doc.text(pageStr, pageWidth - marginRight - doc.getTextWidth(pageStr), doc.internal.pageSize.height - 10)
    }
  })
  
  doc.save(`${title.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}.pdf`)
}
