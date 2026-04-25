import { Card, CardContent, CardHeader } from "@/components/ui/card";

const invoices = [
  ["INV-1024", "AndesPay", "USD 1,240", "Pagada"],
  ["INV-1025", "RioBank", "USD 830", "Pendiente"],
  ["INV-1026", "CobreHub", "USD 2,410", "En disputa"]
];

export default function BillingPage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Billing</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Facturacion</h1>
      </div>
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Invoices recientes</h2>
        </CardHeader>
        <CardContent>
          <table className="w-full text-left text-sm">
            <tbody>
              {invoices.map((row) => (
                <tr key={row[0]} className="border-t border-border first:border-t-0">
                  {row.map((cell) => (
                    <td key={cell} className="py-4">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </section>
  );
}
