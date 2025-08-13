import React from 'react';

// Простая таблица без внешних зависимостей
export interface SimpleColumn<TData> {
  header: string | React.ReactNode;
  accessorKey: keyof TData;
  cell?: (data: TData) => React.ReactNode;
}

export interface SimpleTableProps<TData> {
  data: TData[];
  columns: SimpleColumn<TData>[];
}

export function SimpleTable<TData>({ data, columns }: SimpleTableProps<TData>) {
  return (
    <table className="w-full border-collapse">
      <thead className="bg-gray-50">
        <tr>
          {columns.map((column, index) => (
            <th 
              key={index}
              className="text-left py-3 px-4"
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr key={rowIndex} className="border-b">
            {columns.map((column, colIndex) => (
              <td 
                key={colIndex}
                className="py-3 px-4"
              >
                {column.cell ? column.cell(row) : String(row[column.accessorKey])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
