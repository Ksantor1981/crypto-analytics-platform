import { useEffect, useState } from 'react';

export const useResponsive = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [isLarge, setIsLarge] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 640);
      setIsTablet(width >= 640 && width < 1024);
      setIsDesktop(width >= 1024 && width < 1280);
      setIsLarge(width >= 1280);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return { isMobile, isTablet, isDesktop, isLarge };
};

interface ResponsiveProps {
  mobile?: React.ReactNode;
  tablet?: React.ReactNode;
  desktop?: React.ReactNode;
}

export const Responsive: React.FC<ResponsiveProps> = ({
  mobile,
  tablet,
  desktop,
}) => {
  const { isMobile, isTablet, isDesktop, isLarge } = useResponsive();

  if (isMobile && mobile) return <>{mobile}</>;
  if (isTablet && tablet) return <>{tablet}</>;
  if ((isDesktop || isLarge) && desktop) return <>{desktop}</>;
  return null;
};

// Хук для определения видимости элемента на экране
export function useIntersectionObserver(
  ref: React.RefObject<Element>,
  options: IntersectionObserverInit = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => setIsIntersecting(entry.isIntersecting),
      options
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [ref, options]);

  return isIntersecting;
}

// Хук для определения направления скролла
export function useScrollDirection() {
  const [scrollDirection, setScrollDirection] = useState<'up' | 'down' | null>(
    null
  );
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const updateScrollDirection = () => {
      const scrollY = window.pageYOffset;
      const direction = scrollY > lastScrollY ? 'down' : 'up';

      if (
        direction !== scrollDirection &&
        (scrollY - lastScrollY > 10 || scrollY - lastScrollY < -10)
      ) {
        setScrollDirection(direction);
      }

      setLastScrollY(scrollY > 0 ? scrollY : 0);
    };

    window.addEventListener('scroll', updateScrollDirection);
    return () => window.removeEventListener('scroll', updateScrollDirection);
  }, [scrollDirection, lastScrollY]);

  return scrollDirection;
}

// Хук для управления модальными окнами на мобильных устройствах
export function useMobileModal() {
  const { isMobile } = useResponsive();

  useEffect(() => {
    if (isMobile) {
      // Отключаем скролл body при открытии модального окна на мобильных
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';

      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isMobile]);

  return { isMobile };
}

// Хук для адаптивных шрифтов
export function useResponsiveFontSize() {
  const { width } = useResponsive();

  const getFontSize = (baseSize: number) => {
    if (width < breakpoints.sm) return baseSize * 0.8;
    if (width < breakpoints.md) return baseSize * 0.9;
    if (width < breakpoints.lg) return baseSize;
    return baseSize * 1.1;
  };

  return { getFontSize };
}

// Утилита для условного рендеринга по размеру экрана
export function MediaQuery({
  mobile,
  tablet,
  desktop,
  fallback = null,
}: {
  mobile?: React.ReactNode;
  tablet?: React.ReactNode;
  desktop?: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { isMobile, isTablet, isDesktop, isLarge } = useResponsive();

  if (isMobile && mobile) return <>{mobile}</>;
  if (isTablet && tablet) return <>{tablet}</>;
  if ((isDesktop || isLarge) && desktop) return <>{desktop}</>;

  return <>{fallback}</>;
}

export default useResponsive;
