import React from 'react';

interface Column<T> {
  key: keyof T;
  title: string;
  width?: string;
  sortable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  className?: string;
  onRowClick?: (record: T) => void;
}

function Table<T extends Record<string, any>>({ 
  data, 
  columns, 
  loading = false, 
  className = '',
  onRowClick 
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="w-full">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded mb-2"></div>
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-12 bg-gray-100 rounded mb-1"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="table">
        <thead className="table-header">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className="table-cell font-medium"
                style={{ width: column.width }}
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((record, index) => (
            <tr
              key={index}
              className={`table-row ${onRowClick ? 'cursor-pointer' : ''}`}
              onClick={() => onRowClick?.(record)}
            >
              {columns.map((column) => (
                <td key={String(column.key)} className="table-cell">
                  {column.render 
                    ? column.render(record[column.key], record)
                    : record[column.key]
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No data available
        </div>
      )}
    </div>
  );
}

export { Table };
export type { TableProps, Column }; 