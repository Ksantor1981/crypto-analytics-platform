import React from 'react';
import { 
  ColumnDef, 
  flexRender, 
  getCoreRowModel, 
  useReactTable,
} from '@tanstack/react-table';

// Простой интерфейс для базового Table
export interface TableProps<TData> {
  data: TData[];
  columns: ColumnDef<TData, unknown>[];
}

export function Table<TData>({ data, columns }: TableProps<TData>) {
  const table = useReactTable<TData>({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <table className="w-full border-collapse">
      <thead className="bg-gray-50">
        {table.getHeaderGroups().map(headerGroup => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <th 
                key={header.id} 
                className="text-left py-3 px-4"
              >
                {header.isPlaceholder
                  ? null
                  : flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map(row => (
          <tr key={row.id} className="border-b">
            {row.getVisibleCells().map(cell => (
              <td 
                key={cell.id} 
                className="py-3 px-4"
              >
                {flexRender(
                  cell.column.columnDef.cell,
                  cell.getContext()
                )}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Экспорт типов для удобства
export type { ColumnDef } from '@tanstack/react-table';