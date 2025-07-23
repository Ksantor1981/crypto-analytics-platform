import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import useResponsive from '@/hooks/useResponsive';

interface ResponsiveCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  mobileFullWidth?: boolean;
  mobileNoPadding?: boolean;
  clickable?: boolean;
  onClick?: () => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export function ResponsiveCard({
  title,
  children,
  className = '',
  mobileFullWidth = true,
  mobileNoPadding = false,
  clickable = false,
  onClick,
  header,
  footer,
}: ResponsiveCardProps) {
  const { isMobile, isTablet } = useResponsive();

  const cardClasses = `
    ${className}
    ${isMobile && mobileFullWidth ? 'mx-0 rounded-none border-x-0' : ''}
    ${clickable ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}
    ${isMobile ? 'shadow-sm' : 'shadow'}
  `;

  const contentClasses = `
    ${isMobile && mobileNoPadding ? 'p-0' : ''}
    ${isMobile ? 'p-4' : 'p-6'}
  `;

  return (
    <Card className={cardClasses} onClick={clickable ? onClick : undefined}>
      {(title || header) && (
        <CardHeader className={isMobile ? 'p-4 pb-2' : 'p-6 pb-4'}>
          {header || (
            <CardTitle className={isMobile ? 'text-lg' : 'text-xl'}>
              {title}
            </CardTitle>
          )}
        </CardHeader>
      )}

      <CardContent className={contentClasses}>{children}</CardContent>

      {footer && (
        <div
          className={`border-t border-gray-200 ${isMobile ? 'p-4 pt-3' : 'p-6 pt-4'}`}
        >
          {footer}
        </div>
      )}
    </Card>
  );
}

// Компонент для адаптивной сетки карточек
interface ResponsiveGridProps {
  children: React.ReactNode;
  cols?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: number;
  className?: string;
}

export function ResponsiveGrid({
  children,
  cols = { mobile: 1, tablet: 2, desktop: 3 },
  gap = 4,
  className = '',
}: ResponsiveGridProps) {
  const { isMobile, isTablet, isDesktop } = useResponsive();

  const getGridCols = () => {
    if (isMobile) return cols.mobile || 1;
    if (isTablet) return cols.tablet || 2;
    return cols.desktop || 3;
  };

  const gridClasses = `
    grid gap-${gap}
    grid-cols-${getGridCols()}
    ${className}
  `;

  return <div className={gridClasses}>{children}</div>;
}

// Компонент для адаптивного списка
interface ResponsiveListProps {
  items: Array<{
    id: string;
    title: string;
    subtitle?: string;
    icon?: React.ReactNode;
    badge?: string | number;
    action?: React.ReactNode;
    onClick?: () => void;
  }>;
  className?: string;
  emptyState?: React.ReactNode;
}

export function ResponsiveList({
  items,
  className = '',
  emptyState,
}: ResponsiveListProps) {
  const { isMobile } = useResponsive();

  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {emptyState || 'Нет элементов для отображения'}
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {items.map(item => (
        <div
          key={item.id}
          onClick={item.onClick}
          className={`
            flex items-center justify-between p-4 rounded-lg border
            ${item.onClick ? 'cursor-pointer hover:bg-gray-50 active:bg-gray-100' : ''}
            ${isMobile ? 'border-gray-200' : 'border-gray-100'}
            transition-colors
          `}
        >
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            {item.icon && <div className="flex-shrink-0">{item.icon}</div>}

            <div className="flex-1 min-w-0">
              <p
                className={`font-medium text-gray-900 ${isMobile ? 'text-sm' : 'text-base'} truncate`}
              >
                {item.title}
              </p>
              {item.subtitle && (
                <p
                  className={`text-gray-600 ${isMobile ? 'text-xs' : 'text-sm'} truncate`}
                >
                  {item.subtitle}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2 flex-shrink-0">
            {item.badge && (
              <span
                className={`
                px-2 py-1 rounded-full text-xs font-medium
                bg-blue-100 text-blue-800
                ${isMobile ? 'text-xs' : 'text-sm'}
              `}
              >
                {item.badge}
              </span>
            )}

            {item.action}
          </div>
        </div>
      ))}
    </div>
  );
}

// Компонент для адаптивных вкладок
interface ResponsiveTabsProps {
  tabs: Array<{
    id: string;
    label: string;
    count?: number;
    content: React.ReactNode;
  }>;
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

export function ResponsiveTabs({
  tabs,
  activeTab,
  onTabChange,
  className = '',
}: ResponsiveTabsProps) {
  const { isMobile } = useResponsive();

  return (
    <div className={className}>
      {/* Tab Headers */}
      <div
        className={`
        flex border-b border-gray-200 overflow-x-auto
        ${isMobile ? 'space-x-0' : 'space-x-4'}
      `}
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              flex items-center space-x-2 py-3 px-4 font-medium text-sm
              border-b-2 transition-colors whitespace-nowrap
              ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }
              ${isMobile ? 'flex-1 justify-center' : ''}
            `}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span
                className={`
                px-2 py-1 text-xs rounded-full
                ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600'
                }
              `}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className={isMobile ? 'mt-4' : 'mt-6'}>
        {tabs.find(tab => tab.id === activeTab)?.content}
      </div>
    </div>
  );
}

export default ResponsiveCard;

