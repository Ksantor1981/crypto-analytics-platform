// Строгая типизация для React Table компонентов
export interface TableCellContext<TData> {
  row: {
    original: TData;
    index: number;
  };
  column: {
    id: string;
  };
  getValue: () => any;
}

export interface TableHeaderContext {
  column: {
    id: string;
  };
}

export interface ColumnDefinition<TData> {
  header: string | React.ReactNode | ((context: TableHeaderContext) => React.ReactNode);
  accessorKey: keyof TData;
  cell?: (context: TableCellContext<TData>) => React.ReactNode;
  sortable?: boolean;
}

export interface TableProps<TData> {
  data: TData[];
  columns: ColumnDefinition<TData>[];
  onSort?: (field: keyof TData, direction: 'asc' | 'desc') => void;
}
